"""
Data cleaning module for feedback tickets.

This module processes raw Freshdesk ticket data to extract meaningful user feedback
by removing auto-replies, signatures, system messages, and other noise while
preserving essential metadata.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .logger import get_logger


# Initialize logger for this module
logger = get_logger(__name__)


@dataclass
class CleanTicket:
    """
    Cleaned ticket data ready for AI analysis.
    
    Attributes:
        ticket_id: Original Freshdesk ticket ID
        subject: Ticket subject line
        clean_feedback: Cleaned feedback text (main user message)
        created_date: Ticket creation date
        status: Ticket status
        priority: Ticket priority
        tags: List of tags
        metadata: Additional ticket metadata
    """
    ticket_id: int
    subject: str
    clean_feedback: str
    created_date: str
    status: Optional[int] = None
    priority: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'ticket_id': self.ticket_id,
            'subject': self.subject,
            'clean_feedback': self.clean_feedback,
            'created_date': self.created_date,
            'status': self.status,
            'priority': self.priority,
            'tags': self.tags,
            'metadata': self.metadata
        }
    
    def __str__(self) -> str:
        """String representation."""
        feedback_preview = self.clean_feedback[:100] + "..." if len(self.clean_feedback) > 100 else self.clean_feedback
        return (
            f"Ticket #{self.ticket_id}\n"
            f"  Subject: {self.subject}\n"
            f"  Date: {self.created_date}\n"
            f"  Feedback: {feedback_preview}"
        )


# Common auto-reply patterns (case-insensitive)
AUTO_REPLY_PATTERNS = [
    r"this is an automated (message|response|reply)",
    r"auto(-|\s)?reply",
    r"out of (the )?office",
    r"currently (away|unavailable)",
    r"on vacation",
    r"thank you for (contacting|reaching out)",
    r"we have received your (request|message|email)",
    r"your (ticket|request) has been (received|created)",
    r"ticket (id|number|#):\s*\d+",
    r"reference (id|number):\s*\d+",
    r"do not reply to this email",
    r"this (email|message) was sent automatically",
]

# Common signature patterns
SIGNATURE_PATTERNS = [
    r"(best |kind )?regards,?",
    r"sincerely,?",
    r"thanks,?",
    r"thank you,?",
    r"cheers,?",
    r"--+",  # Signature delimiter
    r"_{3,}",  # Underscore delimiter
    r"sent from my (iphone|ipad|android|mobile)",
    r"get outlook for (ios|android)",
    r"this email and any attachments",
    r"confidentiality notice",
]

# System message patterns
SYSTEM_MESSAGE_PATTERNS = [
    r"\[system\]",
    r"\[automated\]",
    r"please do not respond",
    r"generated automatically",
    r"this is a system (message|notification)",
]


def remove_html_tags(text: str) -> str:
    """
    Remove HTML tags from text.
    
    Args:
        text: Text potentially containing HTML
        
    Returns:
        Text with HTML tags removed
    """
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Decode common HTML entities
    html_entities = {
        '&nbsp;': ' ',
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&mdash;': '—',
        '&ndash;': '–',
    }
    
    for entity, char in html_entities.items():
        text = text.replace(entity, char)
    
    return text


def remove_urls(text: str) -> str:
    """
    Remove URLs from text.
    
    Args:
        text: Text potentially containing URLs
        
    Returns:
        Text with URLs removed
    """
    # Remove http/https URLs
    text = re.sub(r'https?://\S+', '', text)
    
    # Remove www URLs
    text = re.sub(r'www\.\S+', '', text)
    
    return text


def remove_email_addresses(text: str) -> str:
    """
    Remove email addresses from text.
    
    Args:
        text: Text potentially containing email addresses
        
    Returns:
        Text with email addresses removed
    """
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
    return text


def remove_auto_replies(text: str) -> str:
    """
    Remove auto-reply messages from text.
    
    Args:
        text: Text potentially containing auto-replies
        
    Returns:
        Text with auto-replies removed
    """
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Check if line matches any auto-reply pattern
        is_auto_reply = False
        for pattern in AUTO_REPLY_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                is_auto_reply = True
                logger.debug(f"Removed auto-reply line: {line[:50]}...")
                break
        
        if not is_auto_reply:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def remove_signatures(text: str) -> str:
    """
    Remove email signatures from text.
    
    Signatures are typically at the end of the message after patterns like
    "Best regards," or "--" delimiters.
    
    Args:
        text: Text potentially containing signatures
        
    Returns:
        Text with signatures removed
    """
    lines = text.split('\n')
    
    # Find the first line that looks like a signature start
    signature_start = None
    
    for i, line in enumerate(lines):
        for pattern in SIGNATURE_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                signature_start = i
                logger.debug(f"Found signature at line {i}: {line[:50]}...")
                break
        
        if signature_start is not None:
            break
    
    # If signature found, keep only lines before it
    if signature_start is not None:
        lines = lines[:signature_start]
    
    return '\n'.join(lines)


def remove_system_messages(text: str) -> str:
    """
    Remove system-generated messages from text.
    
    Args:
        text: Text potentially containing system messages
        
    Returns:
        Text with system messages removed
    """
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Check if line matches any system message pattern
        is_system_message = False
        for pattern in SYSTEM_MESSAGE_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                is_system_message = True
                logger.debug(f"Removed system message: {line[:50]}...")
                break
        
        if not is_system_message:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def remove_quoted_replies(text: str) -> str:
    """
    Remove quoted/forwarded email content.
    
    Common patterns:
    - Lines starting with ">"
    - "On ... wrote:" blocks
    - "From: ... To: ..." email headers
    
    Args:
        text: Text potentially containing quoted replies
        
    Returns:
        Text with quoted replies removed
    """
    lines = text.split('\n')
    cleaned_lines = []
    
    in_quote_block = False
    
    for line in lines:
        # Check for quote indicators
        if line.strip().startswith('>'):
            in_quote_block = True
            continue
        
        # Check for "On ... wrote:" pattern
        if re.search(r'On .+ wrote:', line):
            in_quote_block = True
            continue
        
        # Check for email header pattern
        if re.search(r'^(From|To|Cc|Sent|Subject):\s+', line):
            in_quote_block = True
            continue
        
        # Check for forward delimiter
        if re.search(r'---+\s*(Forwarded|Original)\s+Message', line, re.IGNORECASE):
            in_quote_block = True
            continue
        
        # If we're in a quote block and hit a blank line, we might be out
        if in_quote_block and not line.strip():
            in_quote_block = False
            continue
        
        if not in_quote_block:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    - Replace multiple spaces with single space
    - Replace multiple newlines with double newline (paragraph break)
    - Remove leading/trailing whitespace
    
    Args:
        text: Text to normalize
        
    Returns:
        Text with normalized whitespace
    """
    # Replace tabs with spaces
    text = text.replace('\t', ' ')
    
    # Replace multiple spaces with single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Replace multiple newlines with double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove spaces at line endings
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_meaningful_text(text: str) -> str:
    """
    Extract meaningful text by removing various noise elements.
    
    This is the main cleaning pipeline that applies all cleaning steps.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned, meaningful text
    """
    if not text:
        return ""
    
    logger.debug(f"Starting text cleaning. Original length: {len(text)}")
    
    # Step 1: Remove HTML tags
    text = remove_html_tags(text)
    logger.debug(f"After HTML removal: {len(text)} chars")
    
    # Step 2: Remove URLs
    text = remove_urls(text)
    logger.debug(f"After URL removal: {len(text)} chars")
    
    # Step 3: Remove email addresses
    text = remove_email_addresses(text)
    logger.debug(f"After email removal: {len(text)} chars")
    
    # Step 4: Remove quoted replies
    text = remove_quoted_replies(text)
    logger.debug(f"After quote removal: {len(text)} chars")
    
    # Step 5: Remove auto-replies
    text = remove_auto_replies(text)
    logger.debug(f"After auto-reply removal: {len(text)} chars")
    
    # Step 6: Remove signatures
    text = remove_signatures(text)
    logger.debug(f"After signature removal: {len(text)} chars")
    
    # Step 7: Remove system messages
    text = remove_system_messages(text)
    logger.debug(f"After system message removal: {len(text)} chars")
    
    # Step 8: Normalize whitespace
    text = normalize_whitespace(text)
    logger.debug(f"After whitespace normalization: {len(text)} chars")
    
    return text


def clean_ticket(raw_ticket: Dict[str, Any]) -> CleanTicket:
    """
    Clean a single ticket, extracting meaningful feedback.
    
    Args:
        raw_ticket: Raw ticket dictionary from Freshdesk API
        
    Returns:
        CleanTicket object with cleaned data
    """
    # Extract ticket ID
    ticket_id = raw_ticket.get('id', 0)
    
    # Extract subject
    subject = raw_ticket.get('subject', '').strip()
    
    # Extract description (prefer description_text over description)
    # description_text is plain text, description is HTML
    raw_feedback = raw_ticket.get('description_text') or raw_ticket.get('description') or ''
    
    # Clean the feedback text
    clean_feedback = extract_meaningful_text(raw_feedback)
    
    # If cleaned feedback is too short, it might be mostly noise
    if len(clean_feedback) < 10 and subject:
        # Use subject as feedback if description is empty/noise
        clean_feedback = subject
        logger.warning(
            f"Ticket #{ticket_id}: Cleaned feedback very short, "
            f"using subject as feedback"
        )
    
    # Extract created date
    created_date = raw_ticket.get('created_at', '')
    
    # Extract optional fields
    status = raw_ticket.get('status')
    priority = raw_ticket.get('priority')
    tags = raw_ticket.get('tags', [])
    
    # Get custom_fields to extract Type, Game, OS, etc.
    custom_fields = raw_ticket.get('custom_fields', {})
    
    # Store additional metadata
    # Type is in custom_fields as "Type" in Freshdesk
    metadata = {
        'type': custom_fields.get('Type') or raw_ticket.get('type'),  # Try custom_fields first
        'status': status,  # Store status for filtering
        'source': raw_ticket.get('source'),
        'custom_fields': custom_fields,
        'tags': tags,  # Store tags for filtering
        'original_length': len(raw_feedback),
        'cleaned_length': len(clean_feedback),
        'reduction_ratio': round(
            (1 - len(clean_feedback) / len(raw_feedback)) * 100, 1
        ) if raw_feedback else 0
    }
    
    # Create cleaned ticket object
    clean_ticket_obj = CleanTicket(
        ticket_id=ticket_id,
        subject=subject,
        clean_feedback=clean_feedback,
        created_date=created_date,
        status=status,
        priority=priority,
        tags=tags,
        metadata=metadata
    )
    
    logger.debug(
        f"Cleaned ticket #{ticket_id}: "
        f"{metadata['original_length']} → {metadata['cleaned_length']} chars "
        f"({metadata['reduction_ratio']}% reduction)"
    )
    
    return clean_ticket_obj


def clean_tickets(raw_tickets: List[Dict[str, Any]]) -> List[CleanTicket]:
    """
    Clean multiple tickets.
    
    Args:
        raw_tickets: List of raw ticket dictionaries
        
    Returns:
        List of CleanTicket objects
    """
    logger.info(f"Starting to clean {len(raw_tickets)} tickets...")
    
    cleaned_tickets = []
    
    for i, raw_ticket in enumerate(raw_tickets, 1):
        try:
            cleaned = clean_ticket(raw_ticket)
            cleaned_tickets.append(cleaned)
            
            if i % 10 == 0:
                logger.info(f"Cleaned {i}/{len(raw_tickets)} tickets...")
                
        except Exception as e:
            ticket_id = raw_ticket.get('id', 'unknown')
            logger.error(f"Failed to clean ticket #{ticket_id}: {e}")
            # Continue with other tickets
            continue
    
    logger.info(
        f"✓ Cleaning complete: {len(cleaned_tickets)}/{len(raw_tickets)} "
        f"tickets successfully cleaned"
    )
    
    # Log cleaning statistics
    if cleaned_tickets:
        total_original = sum(t.metadata['original_length'] for t in cleaned_tickets)
        total_cleaned = sum(t.metadata['cleaned_length'] for t in cleaned_tickets)
        avg_reduction = round((1 - total_cleaned / total_original) * 100, 1) if total_original else 0
        
        logger.info(f"Overall reduction: {avg_reduction}% (noise removed)")
    
    return cleaned_tickets


def clean_feedback_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean feedback data structure (from Freshdesk or cache).
    
    This is the main entry point that processes the entire feedback data
    structure including metadata.
    
    Args:
        data: Feedback data with 'metadata' and 'feedbacks' keys
        
    Returns:
        Cleaned feedback data with same structure
    """
    logger.info("Cleaning feedback data...")
    
    # Extract raw tickets
    raw_tickets = data.get('feedbacks', [])
    
    if not raw_tickets:
        logger.warning("No feedback tickets to clean")
        return data
    
    # Clean all tickets
    cleaned_tickets = clean_tickets(raw_tickets)
    
    # Convert to dictionaries
    cleaned_dicts = [ticket.to_dict() for ticket in cleaned_tickets]
    
    # Update data structure
    cleaned_data = {
        'metadata': {
            **data.get('metadata', {}),
            'cleaned': True,
            'original_count': len(raw_tickets),
            'cleaned_count': len(cleaned_tickets),
            'cleaning_timestamp': data.get('metadata', {}).get('fetched_at', '')
        },
        'feedbacks': cleaned_dicts
    }
    
    logger.info(f"✓ Feedback data cleaned successfully")
    
    return cleaned_data


if __name__ == "__main__":
    # Test the data cleaner
    print("\n" + "="*70)
    print("  TESTING DATA CLEANER")
    print("="*70 + "\n")
    
    # Sample raw ticket with various noise
    sample_ticket = {
        'id': 12345,
        'subject': 'Game crashes on level 5',
        'description': '''
<p>Hi,</p>

<p>The game keeps crashing when I reach level 5. This is very frustrating!</p>

<p>I've tried reinstalling but it still happens.</p>

<p>Best regards,<br>
John Doe<br>
john.doe@example.com<br>
Sent from my iPhone</p>

<p>--<br>
This email and any attachments are confidential.</p>
        ''',
        'description_text': '''
Hi,

The game keeps crashing when I reach level 5. This is very frustrating!

I've tried reinstalling but it still happens.

Best regards,
John Doe
john.doe@example.com
Sent from my iPhone

--
This email and any attachments are confidential.
        ''',
        'created_at': '2024-01-15T10:30:00Z',
        'status': 4,
        'priority': 3,
        'tags': ['bug', 'crash'],
        'type': 'Feedback',
        'custom_fields': {'game_name': 'Test Game', 'os': 'iOS'}
    }
    
    print("1. Sample Raw Ticket:")
    print(f"   ID: {sample_ticket['id']}")
    print(f"   Subject: {sample_ticket['subject']}")
    print(f"   Original text length: {len(sample_ticket['description_text'])} chars\n")
    
    print("2. Cleaning ticket...")
    cleaned = clean_ticket(sample_ticket)
    
    print(f"\n3. Cleaned Result:")
    print(f"   {cleaned}\n")
    
    print(f"4. Cleaning Statistics:")
    print(f"   Original: {cleaned.metadata['original_length']} chars")
    print(f"   Cleaned: {cleaned.metadata['cleaned_length']} chars")
    print(f"   Reduction: {cleaned.metadata['reduction_ratio']}%\n")
    
    print(f"5. Clean Feedback Text:")
    print(f"   \"{cleaned.clean_feedback}\"\n")
    
    # Test batch cleaning
    print("6. Testing batch cleaning...")
    sample_data = {
        'metadata': {'game_name': 'Test Game', 'total_records': 2},
        'feedbacks': [sample_ticket, sample_ticket]
    }
    
    cleaned_data = clean_feedback_data(sample_data)
    print(f"   Cleaned {len(cleaned_data['feedbacks'])} tickets")
    print(f"   Metadata: {cleaned_data['metadata']}\n")
    
    print("="*70)
    print("✅ Data cleaner test completed successfully!")
    print("="*70 + "\n")
