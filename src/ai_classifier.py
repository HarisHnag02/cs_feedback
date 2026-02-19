"""
OpenAI-based AI classifier for feedback tickets.

This module uses OpenAI's API to classify feedback tickets with game context,
extracting categories, sentiment, intent, and other insights with strict JSON output.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import DATA_PROCESSED_DIR, get_settings
from .context_loader import GameFeatureContext
from .logger import get_logger
from .utils import save_json


# Initialize logger for this module
logger = get_logger(__name__)


class AIClassifierError(Exception):
    """Custom exception for AI classification errors."""
    pass


@dataclass
class TicketClassification:
    """
    AI classification result for a single ticket.
    
    Attributes:
        ticket_id: Original ticket ID
        category: Main category (Bug, Feature Request, Feedback, etc.)
        subcategory: Specific subcategory within main category
        sentiment: Sentiment analysis (Positive, Negative, Neutral, Mixed)
        intent: User intent (Report Issue, Request Feature, Praise, Complaint, etc.)
        confidence: AI confidence score (0.0 to 1.0)
        key_points: List of key points extracted from feedback
        short_summary: Brief summary of the feedback
        is_expected_behavior: Whether issue is due to known constraint/expected behavior
        related_feature: Which game feature this relates to (if any)
    """
    ticket_id: int
    category: str
    subcategory: str
    sentiment: str
    intent: str
    confidence: float
    key_points: List[str]
    short_summary: str
    is_expected_behavior: bool
    related_feature: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'ticket_id': self.ticket_id,
            'category': self.category,
            'subcategory': self.subcategory,
            'sentiment': self.sentiment,
            'intent': self.intent,
            'confidence': self.confidence,
            'key_points': self.key_points,
            'short_summary': self.short_summary,
            'is_expected_behavior': self.is_expected_behavior,
            'related_feature': self.related_feature
        }
    
    def __str__(self) -> str:
        """String representation."""
        return (
            f"Ticket #{self.ticket_id} Classification:\n"
            f"  Category: {self.category} > {self.subcategory}\n"
            f"  Sentiment: {self.sentiment}\n"
            f"  Intent: {self.intent}\n"
            f"  Confidence: {self.confidence:.2f}\n"
            f"  Summary: {self.short_summary}"
        )


def build_batch_classification_prompt(
    tickets: List[Dict[str, Any]],
    game_context: Optional[GameFeatureContext] = None
) -> str:
    """
    Build prompt for batch classification of multiple tickets.
    
    Args:
        tickets: List of ticket dictionaries (up to 10)
        game_context: Optional game feature context
        
    Returns:
        Complete batch prompt string for OpenAI
    """
    prompt_parts = [
        "You are an expert game feedback analyst. Analyze the following player feedback tickets and provide structured classifications.",
        ""
    ]
    
    # Add game context if available
    if game_context:
        prompt_parts.extend([
            "GAME CONTEXT:",
            game_context.format_for_ai(),
            "",
            "IMPORTANT: Use this context to:",
            "- Determine if reported issues are actually expected behaviors",
            "- Identify which specific game features the feedback relates to",
            "- Understand if suggestions are for existing or new features",
            ""
        ])
    
    # Add all tickets
    prompt_parts.append(f"ANALYZE THESE {len(tickets)} FEEDBACK TICKETS:")
    prompt_parts.append("")
    
    for i, ticket in enumerate(tickets, 1):
        prompt_parts.extend([
            f"TICKET {i}:",
            f"  ID: {ticket.get('ticket_id')}",
            f"  Subject: {ticket.get('subject', 'N/A')}",
            f"  Feedback: {ticket.get('clean_feedback', 'N/A')}",
            ""
        ])
    
    # Add response format instructions
    prompt_parts.extend([
        f"Return a JSON ARRAY with exactly {len(tickets)} classification objects (one per ticket):",
        "[",
        "  {",
        '    "ticket_id": <ticket ID>,',
        '    "category": "<Main category>",',
        '    "subcategory": "<Specific subcategory>",',
        '    "sentiment": "<Positive, Negative, Neutral, or Mixed>",',
        '    "intent": "<Report Bug, Request Feature, Praise Game, Complain, Ask Question, or Other>",',
        '    "confidence": <0.0 to 1.0>,',
        '    "key_points": ["<point 1>", "<point 2>", ...],',
        '    "short_summary": "<one sentence>",',
        '    "is_expected_behavior": <true/false>,',
        '    "related_feature": "<feature name or null>"',
        "  },",
        "  ... (repeat for all tickets)",
        "]",
        "",
        "CRITICAL:",
        "- Return ONLY the JSON array, no other text",
        f"- Array must have exactly {len(tickets)} objects",
        "- Each object must have a ticket_id matching the input",
        "- Maintain the same order as input tickets",
        "- All fields are required for each ticket"
    ])
    
    return "\n".join(prompt_parts)


def build_classification_prompt(
    clean_feedback: str,
    subject: str,
    game_context: Optional[GameFeatureContext] = None
) -> str:
    """
    Build comprehensive prompt for ticket classification.
    
    Args:
        clean_feedback: Cleaned feedback text
        subject: Ticket subject line
        game_context: Optional game feature context
        
    Returns:
        Complete prompt string for OpenAI
    """
    prompt_parts = [
        "You are an expert game feedback analyst. Analyze the following player feedback and provide a structured classification.",
        ""
    ]
    
    # Add game context if available
    if game_context:
        prompt_parts.extend([
            "GAME CONTEXT:",
            game_context.format_for_ai(),
            "",
            "IMPORTANT: Use this context to:",
            "- Determine if reported issues are actually expected behaviors based on known constraints",
            "- Identify which specific game features the feedback relates to",
            "- Understand if suggestions are for existing or new features",
            ""
        ])
    
    # Add feedback to analyze
    prompt_parts.extend([
        "FEEDBACK TO ANALYZE:",
        f"Subject: {subject}",
        f"Message: {clean_feedback}",
        "",
        "Provide your analysis in the following STRICT JSON format:",
        "{",
        '  "category": "<Main category: Bug, Feature Request, Positive Feedback, Negative Feedback, Question, Technical Issue, Balance Issue, or Other>",',
        '  "subcategory": "<Specific subcategory within the main category>",',
        '  "sentiment": "<Overall sentiment: Positive, Negative, Neutral, or Mixed>",',
        '  "intent": "<User intent: Report Bug, Request Feature, Praise Game, Complain, Ask Question, or Other>",',
        '  "confidence": <Confidence score between 0.0 and 1.0>,',
        '  "key_points": ["<Key point 1>", "<Key point 2>", ...],',
        '  "short_summary": "<One sentence summary of the feedback>",',
        '  "is_expected_behavior": <true/false - is this a known constraint or expected behavior based on game context>,',
        '  "related_feature": "<Which game feature this relates to, or null if not feature-specific>"',
        "}",
        "",
        "IMPORTANT:",
        "- Return ONLY the JSON object, no additional text",
        "- Ensure valid JSON syntax",
        "- Use double quotes for strings",
        "- confidence must be a number between 0.0 and 1.0",
        "- key_points must be an array of strings (2-5 points)",
        "- is_expected_behavior must be boolean (true/false)",
        "- related_feature can be null or a string"
    ])
    
    return "\n".join(prompt_parts)


class OpenAIClassifier:
    """
    OpenAI-based ticket classifier.
    
    This class handles communication with OpenAI API for ticket classification,
    including retry logic, error handling, and result parsing.
    """
    
    def __init__(self, model: str = "gpt-4-turbo-preview"):
        """
        Initialize OpenAI classifier.
        
        Args:
            model: OpenAI model to use (default: gpt-4-turbo-preview)
        """
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        
        logger.info(f"Initialized OpenAI classifier with model: {model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def _call_openai_api(self, prompt: str) -> str:
        """
        Call OpenAI API with retry logic.
        
        Args:
            prompt: Complete prompt for classification
            
        Returns:
            Raw API response text
            
        Raises:
            Exception: If API call fails after retries
        """
        try:
            logger.debug(f"Calling OpenAI API with model {self.model}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert game feedback analyst. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,  # Deterministic output
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            
            result = response.choices[0].message.content
            logger.debug(f"API call successful. Response length: {len(result)}")
            
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def classify_ticket(
        self,
        ticket: Dict[str, Any],
        game_context: Optional[GameFeatureContext] = None
    ) -> TicketClassification:
        """
        Classify a single ticket using OpenAI.
        
        Args:
            ticket: Clean ticket dictionary
            game_context: Optional game feature context
            
        Returns:
            TicketClassification object
            
        Raises:
            AIClassifierError: If classification fails
        """
        ticket_id = ticket.get('ticket_id', 0)
        subject = ticket.get('subject', '')
        clean_feedback = ticket.get('clean_feedback', '')
        
        if not clean_feedback:
            raise AIClassifierError(
                f"Ticket #{ticket_id} has no clean feedback text"
            )
        
        logger.info(f"Classifying ticket #{ticket_id}...")
        
        # Build prompt
        prompt = build_classification_prompt(clean_feedback, subject, game_context)
        
        try:
            # Call OpenAI API (with retry logic)
            response_text = self._call_openai_api(prompt)
            
            # Parse JSON response
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response was: {response_text}")
                raise AIClassifierError(f"Invalid JSON response from API: {e}")
            
            # Validate required fields
            required_fields = [
                'category', 'subcategory', 'sentiment', 'intent',
                'confidence', 'key_points', 'short_summary',
                'is_expected_behavior'
            ]
            
            missing_fields = [f for f in required_fields if f not in result]
            if missing_fields:
                raise AIClassifierError(
                    f"Missing required fields in API response: {missing_fields}"
                )
            
            # Create classification object
            classification = TicketClassification(
                ticket_id=ticket_id,
                category=result['category'],
                subcategory=result['subcategory'],
                sentiment=result['sentiment'],
                intent=result['intent'],
                confidence=float(result['confidence']),
                key_points=result['key_points'],
                short_summary=result['short_summary'],
                is_expected_behavior=bool(result['is_expected_behavior']),
                related_feature=result.get('related_feature')
            )
            
            logger.info(
                f"✓ Ticket #{ticket_id} classified: "
                f"{classification.category} ({classification.sentiment})"
            )
            
            return classification
            
        except Exception as e:
            logger.error(f"Failed to classify ticket #{ticket_id}: {e}")
            raise AIClassifierError(f"Classification failed: {e}") from e
    
    def classify_batch(
        self,
        tickets: List[Dict[str, Any]],
        game_context: Optional[GameFeatureContext] = None
    ) -> List[TicketClassification]:
        """
        Classify a batch of tickets in a single API call.
        
        Args:
            tickets: List of clean ticket dictionaries (up to 10)
            game_context: Optional game feature context
            
        Returns:
            List of TicketClassification objects
        """
        if not tickets:
            return []
        
        logger.info(f"Classifying batch of {len(tickets)} tickets...")
        
        # Build batch prompt
        prompt = build_batch_classification_prompt(tickets, game_context)
        
        try:
            # Call OpenAI API (with retry logic)
            response_text = self._call_openai_api(prompt)
            
            # Parse JSON array response
            try:
                results = json.loads(response_text)
                
                if not isinstance(results, list):
                    raise AIClassifierError(f"Expected JSON array, got {type(results)}")
                
                if len(results) != len(tickets):
                    logger.warning(f"Expected {len(tickets)} results, got {len(results)}")
            
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise AIClassifierError(f"Invalid JSON response from API: {e}")
            
            # Create classification objects
            classifications = []
            for result in results:
                try:
                    classification = TicketClassification(
                        ticket_id=result.get('ticket_id'),
                        category=result['category'],
                        subcategory=result['subcategory'],
                        sentiment=result['sentiment'],
                        intent=result['intent'],
                        confidence=float(result['confidence']),
                        key_points=result['key_points'],
                        short_summary=result['short_summary'],
                        is_expected_behavior=bool(result['is_expected_behavior']),
                        related_feature=result.get('related_feature')
                    )
                    classifications.append(classification)
                except (KeyError, ValueError) as e:
                    logger.error(f"Failed to parse classification for ticket {result.get('ticket_id', '?')}: {e}")
                    continue
            
            logger.info(f"✓ Batch classified: {len(classifications)}/{len(tickets)} tickets")
            return classifications
            
        except Exception as e:
            logger.error(f"Failed to classify batch: {e}")
            raise AIClassifierError(f"Batch classification failed: {e}") from e
    
    def classify_tickets(
        self,
        tickets: List[Dict[str, Any]],
        game_context: Optional[GameFeatureContext] = None,
        max_tickets: Optional[int] = None,
        batch_size: int = 10
    ) -> List[TicketClassification]:
        """
        Classify multiple tickets using batch processing.
        
        Args:
            tickets: List of clean ticket dictionaries
            game_context: Optional game feature context
            max_tickets: Optional limit on number of tickets to classify
            batch_size: Number of tickets per batch (default: 10)
            
        Returns:
            List of TicketClassification objects
        """
        if max_tickets:
            tickets = tickets[:max_tickets]
        
        logger.info(f"Starting BATCH classification of {len(tickets)} tickets (batch size: {batch_size})...")
        
        classifications = []
        failed_batches = 0
        
        # Split tickets into batches
        total_batches = (len(tickets) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(tickets))
            batch = tickets[start_idx:end_idx]
            
            try:
                batch_classifications = self.classify_batch(batch, game_context)
                classifications.extend(batch_classifications)
                
                logger.info(f"Progress: Batch {batch_num + 1}/{total_batches} complete ({len(classifications)}/{len(tickets)} tickets)")
                
            except AIClassifierError as e:
                logger.error(f"Failed to classify batch {batch_num + 1}: {e}")
                failed_batches += 1
                continue
        
        logger.info(
            f"✓ Classification complete: {len(classifications)} successful, "
            f"{failed_batches} batches failed"
        )
        
        return classifications


def filter_feedback_tickets(
    tickets: List[Dict[str, Any]], 
    os_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter to only tickets for the specified OS.
    
    Type='Feedback' and Game already filtered at Freshdesk fetch level.
    This function only filters by OS.
    
    This happens BEFORE sending to ChatGPT to reduce API costs.
    
    Args:
        tickets: List of cleaned ticket dictionaries (already Feedback type, game filtered)
        os_filter: OS to filter for ("Android", "iOS", or "Both")
        
    Returns:
        List of only Feedback tickets for the specified OS
    """
    filtered_tickets = []
    
    logger.info(f"Filtering {len(tickets)} Feedback tickets for OS='{os_filter}'...")
    
    os_rejected = 0
    
    for ticket in tickets:
        # Type='Feedback' already filtered at fetch level
        # Only filter by OS here
        
        # Get metadata (stored during cleaning)
        metadata = ticket.get('metadata', {})
        custom_fields = metadata.get('custom_fields', {})
        
        # Filter by OS (if not "Both")
        if os_filter and os_filter != 'Both':
            # Actual Freshdesk field is 'os' (lowercase)
            os_field = str(custom_fields.get('os', ''))
            
            # Check OS match (case-insensitive)
            if not os_field or os_filter.lower() not in os_field.lower():
                os_rejected += 1
                continue
        
        # Passed OS filter
        filtered_tickets.append(ticket)
    
    logger.info(f"✓ Filtered: {len(tickets)} Feedback tickets → {len(filtered_tickets)} Feedback+OS tickets")
    logger.info(f"   Rejected by OS filter: {os_rejected}")
    
    return filtered_tickets


def classify_feedback_data(
    cleaned_data: Dict[str, Any],
    os_filter: str = "Both",
    game_context: Optional[GameFeatureContext] = None,
    max_tickets: Optional[int] = None,
    model: str = "gpt-4-turbo-preview"
) -> Dict[str, Any]:
    """
    Classify entire feedback data structure.
    
    This is the main entry point for AI classification.
    Filters to Feedback tickets for specified OS before sending to ChatGPT.
    
    Args:
        cleaned_data: Cleaned feedback data with 'metadata' and 'feedbacks' keys
        game_context: Optional game feature context
        max_tickets: Optional limit on tickets to classify (useful for testing)
        model: OpenAI model to use
        
    Returns:
        Classification results with metadata
        
    Example:
        >>> classified = classify_feedback_data(clean_data, game_context)
        >>> save_classification_results(classified, input_params)
    """
    logger.info("="*70)
    logger.info("Starting AI classification of feedback data")
    logger.info("="*70)
    
    # Extract all tickets
    all_tickets = cleaned_data.get('feedbacks', [])
    
    if not all_tickets:
        logger.warning("No tickets to classify")
        return {
            'metadata': cleaned_data.get('metadata', {}),
            'classifications': [],
            'filtering_stats': {
                'closed_tickets': 0,
                'feedback_tickets': 0,
                'filtered_out': 0
            }
        }
    
    # Filter to only Feedback tickets for the specified OS
    feedback_tickets = filter_feedback_tickets(all_tickets, os_filter=os_filter)
    
    if not feedback_tickets:
        logger.warning("No Feedback tickets found after type filtering")
        return {
            'metadata': cleaned_data.get('metadata', {}),
            'classifications': [],
            'filtering_stats': {
                'closed_tickets': len(all_tickets),
                'feedback_tickets': 0,
                'filtered_out': len(all_tickets)
            }
        }
    
    # Initialize classifier
    classifier = OpenAIClassifier(model=model)
    
    # Classify only the feedback tickets
    classifications = classifier.classify_tickets(
        feedback_tickets,
        game_context=game_context,
        max_tickets=max_tickets
    )
    
    # Convert to dictionaries
    classification_dicts = [c.to_dict() for c in classifications]
    
    # Build result structure
    result = {
        'metadata': {
            **cleaned_data.get('metadata', {}),
            'classified': True,
            'classification_model': model,
            'classification_timestamp': datetime.now().isoformat(),
            'total_classified': len(classifications),
            'closed_tickets_fetched': len(all_tickets),
            'feedback_tickets_filtered': len(feedback_tickets),
            'non_feedback_filtered_out': len(all_tickets) - len(feedback_tickets),
            'classification_success_rate': round(
                len(classifications) / len(feedback_tickets) * 100, 1
            ) if feedback_tickets else 0
        },
        'classifications': classification_dicts,
        'filtering_stats': {
            'closed_tickets': len(all_tickets),
            'feedback_tickets': len(feedback_tickets),
            'filtered_out': len(all_tickets) - len(feedback_tickets)
        }
    }
    
    logger.info("="*70)
    logger.info(f"✓ AI classification complete: {len(classifications)}/{len(feedback_tickets)} Feedback tickets classified")
    logger.info(f"   Closed tickets: {len(all_tickets)} | Feedback type: {len(feedback_tickets)} | Non-Feedback filtered: {len(all_tickets) - len(feedback_tickets)}")
    logger.info("="*70)
    
    return result


def save_classification_results(
    classification_data: Dict[str, Any],
    input_params,
    filename_prefix: str = "classifications"
) -> Path:
    """
    Save classification results to data/processed/.
    
    Args:
        classification_data: Classification results from classify_feedback_data
        input_params: FeedbackAnalysisInput parameters for filename
        filename_prefix: Prefix for filename
        
    Returns:
        Path where data was saved
    """
    from .utils import sanitize_filename, get_timestamp
    
    # Build filename
    safe_game_name = sanitize_filename(input_params.game_name)
    timestamp = get_timestamp()
    
    filename = (
        f"{filename_prefix}_{safe_game_name}_{input_params.os}_"
        f"{input_params.start_date}_to_{input_params.end_date}_{timestamp}.json"
    )
    
    # Ensure directory exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = DATA_PROCESSED_DIR / filename
    save_json(classification_data, file_path)
    
    logger.info(f"✓ Classification results saved to: {file_path.name}")
    
    return file_path


if __name__ == "__main__":
    # Test the AI classifier
    print("\n" + "="*70)
    print("  TESTING AI CLASSIFIER")
    print("="*70 + "\n")
    
    # Sample clean ticket for testing
    sample_ticket = {
        'ticket_id': 99999,
        'subject': 'Game crashes on level 50',
        'clean_feedback': 'The game crashes every time I try to start level 50. Very frustrating!',
        'created_date': '2024-01-15T10:30:00Z',
        'status': 4,
        'priority': 3
    }
    
    try:
        print("1. Initializing OpenAI classifier...")
        classifier = OpenAIClassifier(model="gpt-4-turbo-preview")
        print("   ✓ Classifier initialized\n")
        
        print("2. Classifying sample ticket...")
        print(f"   Subject: {sample_ticket['subject']}")
        print(f"   Feedback: {sample_ticket['clean_feedback']}\n")
        
        # Note: This will make an actual API call
        print("   ⏳ Calling OpenAI API (this may take a moment)...\n")
        
        classification = classifier.classify_ticket(sample_ticket)
        
        print("3. Classification Result:")
        print(classification)
        
        print(f"\n4. Detailed Breakdown:")
        print(f"   Category: {classification.category}")
        print(f"   Subcategory: {classification.subcategory}")
        print(f"   Sentiment: {classification.sentiment}")
        print(f"   Intent: {classification.intent}")
        print(f"   Confidence: {classification.confidence:.2%}")
        print(f"   Expected Behavior: {classification.is_expected_behavior}")
        print(f"   Related Feature: {classification.related_feature}")
        
        print(f"\n   Key Points:")
        for i, point in enumerate(classification.key_points, 1):
            print(f"     {i}. {point}")
        
        print(f"\n   Summary: {classification.short_summary}")
        
        print("\n" + "="*70)
        print("✅ AI classifier test completed successfully!")
        print("="*70 + "\n")
        
        print("⚠️  Note: This test made an actual OpenAI API call and incurred costs.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nPossible issues:")
        print("  1. OPENAI_API_KEY not set in .env")
        print("  2. Invalid API key")
        print("  3. No API credits available")
        print("  4. Network connection issue")
