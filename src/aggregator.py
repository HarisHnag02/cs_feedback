"""
Aggregation module for classified feedback tickets.

This module processes classified tickets to identify patterns, trends, and insights
by grouping data across different dimensions (category, feature, sentiment, etc.)
and detecting recurring issues and trends.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .context_loader import GameFeatureContext
from .logger import get_logger


# Initialize logger for this module
logger = get_logger(__name__)


@dataclass
class AggregatedInsights:
    """
    Structured aggregated insights from classified tickets.
    
    Attributes:
        total_tickets: Total number of tickets analyzed
        category_breakdown: Count by category
        sentiment_breakdown: Count by sentiment
        intent_breakdown: Count by intent
        feature_breakdown: Count by related feature
        top_issues: Most frequently reported issues
        recent_change_impacts: Issues related to recent changes
        expected_behavior_count: Count of tickets that are expected behaviors
        average_confidence: Average AI confidence score
        key_patterns: Identified patterns and trends
    """
    total_tickets: int
    category_breakdown: Dict[str, int]
    sentiment_breakdown: Dict[str, int]
    intent_breakdown: Dict[str, int]
    feature_breakdown: Dict[str, int]
    top_issues: List[Dict[str, Any]]
    recent_change_impacts: List[Dict[str, Any]]
    expected_behavior_count: int
    average_confidence: float
    key_patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_tickets': self.total_tickets,
            'category_breakdown': self.category_breakdown,
            'sentiment_breakdown': self.sentiment_breakdown,
            'intent_breakdown': self.intent_breakdown,
            'feature_breakdown': self.feature_breakdown,
            'top_issues': self.top_issues,
            'recent_change_impacts': self.recent_change_impacts,
            'expected_behavior_count': self.expected_behavior_count,
            'average_confidence': self.average_confidence,
            'key_patterns': self.key_patterns
        }


def aggregate_by_category(classifications: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Aggregate tickets by category.
    
    Args:
        classifications: List of classification dictionaries
        
    Returns:
        Dictionary mapping category to count
    """
    categories = [c['category'] for c in classifications]
    category_counts = Counter(categories)
    
    logger.debug(f"Categories found: {dict(category_counts)}")
    return dict(category_counts)


def aggregate_by_sentiment(classifications: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Aggregate tickets by sentiment.
    
    Args:
        classifications: List of classification dictionaries
        
    Returns:
        Dictionary mapping sentiment to count
    """
    sentiments = [c['sentiment'] for c in classifications]
    sentiment_counts = Counter(sentiments)
    
    logger.debug(f"Sentiments found: {dict(sentiment_counts)}")
    return dict(sentiment_counts)


def aggregate_by_intent(classifications: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Aggregate tickets by intent.
    
    Args:
        classifications: List of classification dictionaries
        
    Returns:
        Dictionary mapping intent to count
    """
    intents = [c['intent'] for c in classifications]
    intent_counts = Counter(intents)
    
    logger.debug(f"Intents found: {dict(intent_counts)}")
    return dict(intent_counts)


def aggregate_by_feature(classifications: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Aggregate tickets by related feature.
    
    Args:
        classifications: List of classification dictionaries
        
    Returns:
        Dictionary mapping feature to count
    """
    features = [
        c.get('related_feature', 'Unspecified')
        for c in classifications
        if c.get('related_feature')
    ]
    
    # Add "Unspecified" for tickets without a related feature
    unspecified_count = sum(
        1 for c in classifications
        if not c.get('related_feature')
    )
    
    feature_counts = Counter(features)
    if unspecified_count > 0:
        feature_counts['Unspecified'] = unspecified_count
    
    logger.debug(f"Features found: {dict(feature_counts)}")
    return dict(feature_counts)


def identify_top_issues(
    classifications: List[Dict[str, Any]],
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Identify top recurring issues based on category and subcategory.
    
    Args:
        classifications: List of classification dictionaries
        top_n: Number of top issues to return
        
    Returns:
        List of top issues with counts and details
    """
    # Group by (category, subcategory) combination
    issue_groups = defaultdict(list)
    
    for cls in classifications:
        key = (cls['category'], cls['subcategory'])
        issue_groups[key].append(cls)
    
    # Build issue summaries with counts
    issues = []
    for (category, subcategory), tickets in issue_groups.items():
        # Calculate average confidence for this issue type
        avg_confidence = sum(t['confidence'] for t in tickets) / len(tickets)
        
        # Get sentiment breakdown for this issue
        sentiments = Counter(t['sentiment'] for t in tickets)
        
        # Get sample summaries
        sample_summaries = [t['short_summary'] for t in tickets[:3]]
        
        issues.append({
            'category': category,
            'subcategory': subcategory,
            'count': len(tickets),
            'percentage': 0,  # Will be calculated later
            'avg_confidence': round(avg_confidence, 3),
            'sentiment_breakdown': dict(sentiments),
            'sample_summaries': sample_summaries,
            'ticket_ids': [t['ticket_id'] for t in tickets]
        })
    
    # Sort by count (descending)
    issues.sort(key=lambda x: x['count'], reverse=True)
    
    # Calculate percentages
    total = len(classifications)
    for issue in issues:
        issue['percentage'] = round(issue['count'] / total * 100, 1)
    
    # Return top N
    top_issues = issues[:top_n]
    
    logger.info(f"Identified {len(issues)} unique issues, returning top {len(top_issues)}")
    
    return top_issues


def detect_recent_change_impacts(
    classifications: List[Dict[str, Any]],
    game_context: Optional[GameFeatureContext] = None
) -> List[Dict[str, Any]]:
    """
    Detect issues that may be related to recent changes.
    
    Looks for patterns where feedback mentions or relates to recent game changes.
    
    Args:
        classifications: List of classification dictionaries
        game_context: Optional game context with recent_changes
        
    Returns:
        List of issues potentially caused by recent changes
    """
    if not game_context or not game_context.recent_changes:
        logger.warning("No game context or recent changes available")
        return []
    
    # Extract recent change keywords (version numbers, feature names)
    change_keywords = []
    for change in game_context.recent_changes:
        # Extract version numbers like "v2.5.0" or "2.5.0"
        import re
        versions = re.findall(r'v?\d+\.\d+(?:\.\d+)?', change.lower())
        change_keywords.extend(versions)
        
        # Extract potential feature names (words in quotes or after "added"/"new")
        quoted = re.findall(r"'([^']+)'|\"([^\"]+)\"", change)
        change_keywords.extend([q[0] or q[1] for q in quoted])
        
        new_features = re.findall(r'(?:added|new|introduced)\s+([^,\.]+)', change.lower())
        change_keywords.extend(new_features)
    
    # Remove duplicates and clean up
    change_keywords = list(set(k.strip() for k in change_keywords if k.strip()))
    
    logger.debug(f"Recent change keywords: {change_keywords}")
    
    # Find tickets that mention these keywords
    impacted_tickets = []
    
    for cls in classifications:
        summary_lower = cls['short_summary'].lower()
        
        # Check if any keyword appears in summary or key points
        mentioned_keywords = []
        for keyword in change_keywords:
            if keyword.lower() in summary_lower:
                mentioned_keywords.append(keyword)
            
            # Also check key points
            for point in cls.get('key_points', []):
                if keyword.lower() in point.lower():
                    if keyword not in mentioned_keywords:
                        mentioned_keywords.append(keyword)
        
        if mentioned_keywords:
            impacted_tickets.append({
                'ticket_id': cls['ticket_id'],
                'category': cls['category'],
                'subcategory': cls['subcategory'],
                'sentiment': cls['sentiment'],
                'summary': cls['short_summary'],
                'mentioned_changes': mentioned_keywords,
                'confidence': cls['confidence']
            })
    
    # Group by mentioned changes
    change_impact_groups = defaultdict(list)
    for ticket in impacted_tickets:
        for change in ticket['mentioned_changes']:
            change_impact_groups[change].append(ticket)
    
    # Build impact summaries
    impacts = []
    for change, tickets in change_impact_groups.items():
        # Get sentiment breakdown
        sentiments = Counter(t['sentiment'] for t in tickets)
        
        # Get category breakdown
        categories = Counter(t['category'] for t in tickets)
        
        impacts.append({
            'change_keyword': change,
            'affected_tickets_count': len(tickets),
            'sentiment_breakdown': dict(sentiments),
            'category_breakdown': dict(categories),
            'sample_tickets': tickets[:5],  # First 5 as samples
            'ticket_ids': [t['ticket_id'] for t in tickets]
        })
    
    # Sort by number of affected tickets
    impacts.sort(key=lambda x: x['affected_tickets_count'], reverse=True)
    
    logger.info(
        f"Detected {len(impacts)} recent changes with potential impact "
        f"affecting {len(impacted_tickets)} tickets"
    )
    
    return impacts


def identify_patterns(
    classifications: List[Dict[str, Any]],
    min_pattern_size: int = 3
) -> List[Dict[str, Any]]:
    """
    Identify patterns across classifications.
    
    Looks for:
    - Features with consistently negative sentiment
    - Categories with low confidence (indicating unclear feedback)
    - High concentration of specific issue types
    
    Args:
        classifications: List of classification dictionaries
        min_pattern_size: Minimum number of tickets to consider a pattern
        
    Returns:
        List of identified patterns
    """
    patterns = []
    
    # Pattern 1: Features with negative sentiment
    feature_sentiments = defaultdict(list)
    for cls in classifications:
        feature = cls.get('related_feature')
        if feature:
            feature_sentiments[feature].append(cls['sentiment'])
    
    for feature, sentiments in feature_sentiments.items():
        if len(sentiments) >= min_pattern_size:
            negative_count = sum(1 for s in sentiments if s == 'Negative')
            negative_ratio = negative_count / len(sentiments)
            
            if negative_ratio >= 0.7:  # 70% or more negative
                patterns.append({
                    'pattern_type': 'Negative Sentiment Cluster',
                    'description': f"Feature '{feature}' has {negative_ratio:.0%} negative feedback",
                    'feature': feature,
                    'ticket_count': len(sentiments),
                    'negative_ratio': round(negative_ratio, 2),
                    'severity': 'High' if negative_ratio >= 0.8 else 'Medium'
                })
    
    # Pattern 2: Categories with low confidence
    category_confidences = defaultdict(list)
    for cls in classifications:
        category_confidences[cls['category']].append(cls['confidence'])
    
    for category, confidences in category_confidences.items():
        if len(confidences) >= min_pattern_size:
            avg_confidence = sum(confidences) / len(confidences)
            
            if avg_confidence < 0.7:  # Low confidence
                patterns.append({
                    'pattern_type': 'Low Confidence Category',
                    'description': f"Category '{category}' has low average confidence ({avg_confidence:.0%})",
                    'category': category,
                    'ticket_count': len(confidences),
                    'avg_confidence': round(avg_confidence, 2),
                    'severity': 'Low',
                    'note': 'May indicate unclear or ambiguous feedback'
                })
    
    # Pattern 3: High concentration of specific bugs
    bug_subcategories = defaultdict(list)
    for cls in classifications:
        if cls['category'] == 'Bug':
            bug_subcategories[cls['subcategory']].append(cls)
    
    total_bugs = sum(len(bugs) for bugs in bug_subcategories.values())
    
    for subcategory, bugs in bug_subcategories.items():
        if len(bugs) >= min_pattern_size:
            concentration = len(bugs) / total_bugs if total_bugs > 0 else 0
            
            if concentration >= 0.3:  # 30% or more of all bugs
                patterns.append({
                    'pattern_type': 'Bug Concentration',
                    'description': f"'{subcategory}' represents {concentration:.0%} of all bugs",
                    'subcategory': subcategory,
                    'ticket_count': len(bugs),
                    'concentration': round(concentration, 2),
                    'severity': 'High' if concentration >= 0.5 else 'Medium'
                })
    
    logger.info(f"Identified {len(patterns)} patterns")
    
    return patterns


def calculate_statistics(classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate various statistics from classifications.
    
    Args:
        classifications: List of classification dictionaries
        
    Returns:
        Dictionary of statistics
    """
    if not classifications:
        return {
            'total_tickets': 0,
            'average_confidence': 0.0,
            'expected_behavior_count': 0,
            'expected_behavior_percentage': 0.0
        }
    
    # Calculate average confidence
    confidences = [c['confidence'] for c in classifications]
    avg_confidence = sum(confidences) / len(confidences)
    
    # Count expected behaviors
    expected_behavior_count = sum(
        1 for c in classifications
        if c.get('is_expected_behavior', False)
    )
    expected_behavior_percentage = expected_behavior_count / len(classifications) * 100
    
    # Sentiment stats
    sentiments = [c['sentiment'] for c in classifications]
    positive_count = sum(1 for s in sentiments if s == 'Positive')
    negative_count = sum(1 for s in sentiments if s == 'Negative')
    neutral_count = sum(1 for s in sentiments if s == 'Neutral')
    mixed_count = sum(1 for s in sentiments if s == 'Mixed')
    
    stats = {
        'total_tickets': len(classifications),
        'average_confidence': round(avg_confidence, 3),
        'expected_behavior_count': expected_behavior_count,
        'expected_behavior_percentage': round(expected_behavior_percentage, 1),
        'sentiment_stats': {
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'mixed_count': mixed_count,
            'positive_percentage': round(positive_count / len(classifications) * 100, 1),
            'negative_percentage': round(negative_count / len(classifications) * 100, 1)
        }
    }
    
    logger.debug(f"Calculated statistics: {stats}")
    
    return stats


def aggregate_classifications(
    classification_data: Dict[str, Any],
    game_context: Optional[GameFeatureContext] = None
) -> AggregatedInsights:
    """
    Main aggregation function that processes classified tickets.
    
    This is the primary entry point for aggregation. It performs all aggregations
    and analysis to produce structured insights ready for report generation.
    
    Args:
        classification_data: Classification results from AI classifier
        game_context: Optional game context for trend detection
        
    Returns:
        AggregatedInsights object with all aggregated data
        
    Example:
        >>> insights = aggregate_classifications(classified_data, game_context)
        >>> print(f"Top issue: {insights.top_issues[0]['subcategory']}")
    """
    logger.info("="*70)
    logger.info("Starting aggregation of classified tickets")
    logger.info("="*70)
    
    classifications = classification_data.get('classifications', [])
    
    if not classifications:
        logger.warning("No classifications to aggregate")
        return AggregatedInsights(
            total_tickets=0,
            category_breakdown={},
            sentiment_breakdown={},
            intent_breakdown={},
            feature_breakdown={},
            top_issues=[],
            recent_change_impacts=[],
            expected_behavior_count=0,
            average_confidence=0.0,
            key_patterns=[]
        )
    
    logger.info(f"Aggregating {len(classifications)} classified tickets...")
    
    # Perform all aggregations
    logger.info("Aggregating by category...")
    category_breakdown = aggregate_by_category(classifications)
    
    logger.info("Aggregating by sentiment...")
    sentiment_breakdown = aggregate_by_sentiment(classifications)
    
    logger.info("Aggregating by intent...")
    intent_breakdown = aggregate_by_intent(classifications)
    
    logger.info("Aggregating by feature...")
    feature_breakdown = aggregate_by_feature(classifications)
    
    logger.info("Identifying top issues...")
    top_issues = identify_top_issues(classifications, top_n=10)
    
    logger.info("Detecting recent change impacts...")
    recent_change_impacts = detect_recent_change_impacts(classifications, game_context)
    
    logger.info("Identifying patterns...")
    key_patterns = identify_patterns(classifications, min_pattern_size=3)
    
    logger.info("Calculating statistics...")
    stats = calculate_statistics(classifications)
    
    # Build insights object
    insights = AggregatedInsights(
        total_tickets=stats['total_tickets'],
        category_breakdown=category_breakdown,
        sentiment_breakdown=sentiment_breakdown,
        intent_breakdown=intent_breakdown,
        feature_breakdown=feature_breakdown,
        top_issues=top_issues,
        recent_change_impacts=recent_change_impacts,
        expected_behavior_count=stats['expected_behavior_count'],
        average_confidence=stats['average_confidence'],
        key_patterns=key_patterns
    )
    
    logger.info("="*70)
    logger.info(f"✓ Aggregation complete:")
    logger.info(f"  Total tickets: {insights.total_tickets}")
    logger.info(f"  Categories: {len(insights.category_breakdown)}")
    logger.info(f"  Top issues: {len(insights.top_issues)}")
    logger.info(f"  Recent change impacts: {len(insights.recent_change_impacts)}")
    logger.info(f"  Patterns identified: {len(insights.key_patterns)}")
    logger.info("="*70)
    
    return insights


if __name__ == "__main__":
    # Test the aggregator
    print("\n" + "="*70)
    print("  TESTING AGGREGATOR")
    print("="*70 + "\n")
    
    # Sample classified tickets for testing
    sample_classifications = [
        {
            'ticket_id': 1001,
            'category': 'Bug',
            'subcategory': 'Crash/Freeze',
            'sentiment': 'Negative',
            'intent': 'Report Bug',
            'confidence': 0.95,
            'key_points': ['Game crashes on level 50'],
            'short_summary': 'Player reports crash on level 50',
            'is_expected_behavior': False,
            'related_feature': 'Level progression'
        },
        {
            'ticket_id': 1002,
            'category': 'Bug',
            'subcategory': 'Crash/Freeze',
            'sentiment': 'Negative',
            'intent': 'Report Bug',
            'confidence': 0.92,
            'key_points': ['Crashes when opening shop'],
            'short_summary': 'Game crashes in shop',
            'is_expected_behavior': False,
            'related_feature': 'In-app purchases'
        },
        {
            'ticket_id': 1003,
            'category': 'Feature Request',
            'subcategory': 'New Feature',
            'sentiment': 'Positive',
            'intent': 'Request Feature',
            'confidence': 0.88,
            'key_points': ['Would like dark mode'],
            'short_summary': 'Player requests dark mode',
            'is_expected_behavior': False,
            'related_feature': 'UI/UX'
        },
        {
            'ticket_id': 1004,
            'category': 'Positive Feedback',
            'subcategory': 'General Praise',
            'sentiment': 'Positive',
            'intent': 'Praise Game',
            'confidence': 0.97,
            'key_points': ['Loves the new v2.5.0 event'],
            'short_summary': 'Player loves new event in v2.5.0',
            'is_expected_behavior': False,
            'related_feature': 'Events'
        },
        {
            'ticket_id': 1005,
            'category': 'Technical Issue',
            'subcategory': 'Performance',
            'sentiment': 'Negative',
            'intent': 'Complain',
            'confidence': 0.85,
            'key_points': ['Slow loading on old device'],
            'short_summary': 'Performance issues on older device',
            'is_expected_behavior': True,
            'related_feature': 'Performance'
        }
    ]
    
    sample_data = {
        'metadata': {'total_classified': 5},
        'classifications': sample_classifications
    }
    
    print("1. Sample data:")
    print(f"   Total tickets: {len(sample_classifications)}")
    print(f"   Categories: {set(c['category'] for c in sample_classifications)}")
    print()
    
    print("2. Running aggregation...")
    insights = aggregate_classifications(sample_data)
    
    print("\n3. Aggregation Results:")
    print(f"\n   Total Tickets: {insights.total_tickets}")
    print(f"   Average Confidence: {insights.average_confidence:.1%}")
    print(f"   Expected Behaviors: {insights.expected_behavior_count}")
    
    print(f"\n   Category Breakdown:")
    for category, count in insights.category_breakdown.items():
        print(f"     • {category}: {count}")
    
    print(f"\n   Sentiment Breakdown:")
    for sentiment, count in insights.sentiment_breakdown.items():
        print(f"     • {sentiment}: {count}")
    
    print(f"\n   Top Issues:")
    for i, issue in enumerate(insights.top_issues, 1):
        print(f"     {i}. {issue['subcategory']}: {issue['count']} tickets ({issue['percentage']}%)")
    
    if insights.key_patterns:
        print(f"\n   Patterns Identified:")
        for pattern in insights.key_patterns:
            print(f"     • {pattern['pattern_type']}: {pattern['description']}")
    
    print("\n" + "="*70)
    print("✅ Aggregator test completed successfully!")
    print("="*70 + "\n")
