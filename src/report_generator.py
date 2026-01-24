"""
Report generation module for feedback analysis.

This module generates comprehensive reports in Markdown and JSON formats
from aggregated insights, designed for designers and stakeholders.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .aggregator import AggregatedInsights
from .config import REPORTS_JSON_DIR, REPORTS_MARKDOWN_DIR
from .context_loader import GameFeatureContext
from .input_handler import FeedbackAnalysisInput
from .logger import get_logger
from .utils import get_timestamp, sanitize_filename, save_json, save_markdown


# Initialize logger for this module
logger = get_logger(__name__)


def generate_executive_summary(
    insights: AggregatedInsights,
    input_params: FeedbackAnalysisInput,
    game_context: Optional[GameFeatureContext] = None
) -> str:
    """
    Generate executive summary section for Markdown report.
    
    Args:
        insights: Aggregated insights
        input_params: Input parameters
        game_context: Optional game context
        
    Returns:
        Markdown formatted executive summary
    """
    lines = [
        "## 📊 Executive Summary",
        "",
        f"**Game:** {input_params.game_name}",
        f"**Platform:** {input_params.os}",
        f"**Analysis Period:** {input_params.start_date} to {input_params.end_date}",
        f"**Total Feedback Analyzed:** {insights.total_tickets} tickets",
        f"**AI Confidence:** {insights.average_confidence:.1%} average",
        ""
    ]
    
    # Sentiment overview
    if insights.sentiment_breakdown:
        total = insights.total_tickets
        negative_pct = insights.sentiment_breakdown.get('Negative', 0) / total * 100
        positive_pct = insights.sentiment_breakdown.get('Positive', 0) / total * 100
        
        lines.extend([
            "### Key Findings",
            "",
            f"- **Overall Sentiment:** {negative_pct:.1f}% Negative, {positive_pct:.1f}% Positive",
            f"- **Top Issue Category:** {list(insights.category_breakdown.keys())[0] if insights.category_breakdown else 'N/A'}",
            f"- **Expected Behaviors:** {insights.expected_behavior_count} tickets ({insights.expected_behavior_count/total*100:.1f}%) are due to known constraints",
            ""
        ])
    
    # Top issues summary
    if insights.top_issues:
        top_issue = insights.top_issues[0]
        lines.extend([
            f"**Most Reported Issue:** {top_issue['subcategory']} ({top_issue['count']} tickets, {top_issue['percentage']}%)",
            ""
        ])
    
    # Recent change impacts
    if insights.recent_change_impacts:
        lines.extend([
            f"**Recent Updates Impact:** {len(insights.recent_change_impacts)} recent changes received player feedback",
            ""
        ])
    
    # Critical patterns
    high_severity_patterns = [p for p in insights.key_patterns if p.get('severity') == 'High']
    if high_severity_patterns:
        lines.extend([
            "### 🔴 Critical Attention Required",
            ""
        ])
        for pattern in high_severity_patterns[:3]:
            lines.append(f"- {pattern['description']}")
        lines.append("")
    
    return "\n".join(lines)


def generate_top_issues_section(insights: AggregatedInsights) -> str:
    """
    Generate top issues section for Markdown report.
    
    Args:
        insights: Aggregated insights
        
    Returns:
        Markdown formatted top issues section
    """
    lines = [
        "## 🔝 Top Recurring Issues",
        "",
        "The following issues were reported most frequently by players:",
        ""
    ]
    
    for i, issue in enumerate(insights.top_issues[:10], 1):
        lines.extend([
            f"### {i}. {issue['category']} > {issue['subcategory']}",
            "",
            f"**Frequency:** {issue['count']} tickets ({issue['percentage']}% of all feedback)",
            f"**Confidence:** {issue['avg_confidence']:.1%}",
            ""
        ])
        
        # Sentiment breakdown
        sentiment_str = ", ".join(
            f"{sentiment}: {count}" 
            for sentiment, count in issue['sentiment_breakdown'].items()
        )
        lines.extend([
            f"**Player Sentiment:** {sentiment_str}",
            ""
        ])
        
        # Sample summaries
        if issue.get('sample_summaries'):
            lines.extend([
                "**Example Player Reports:**",
                ""
            ])
            for summary in issue['sample_summaries']:
                lines.append(f"- \"{summary}\"")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def generate_feature_feedback_section(
    insights: AggregatedInsights,
    classifications: List[Dict[str, Any]]
) -> str:
    """
    Generate feature-wise feedback section for Markdown report.
    
    Args:
        insights: Aggregated insights
        classifications: List of all classifications
        
    Returns:
        Markdown formatted feature feedback section
    """
    lines = [
        "## 🎮 Feature-Wise Feedback Analysis",
        "",
        "Breakdown of feedback by game feature:",
        ""
    ]
    
    # Sort features by count
    sorted_features = sorted(
        insights.feature_breakdown.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    for feature, count in sorted_features[:15]:  # Top 15 features
        if feature == "Unspecified":
            continue
        
        percentage = count / insights.total_tickets * 100
        
        lines.extend([
            f"### {feature}",
            "",
            f"**Mentions:** {count} tickets ({percentage:.1f}%)",
            ""
        ])
        
        # Get sentiment breakdown for this feature
        feature_tickets = [
            c for c in classifications 
            if c.get('related_feature') == feature
        ]
        
        if feature_tickets:
            sentiments = {}
            for ticket in feature_tickets:
                sentiment = ticket['sentiment']
                sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
            
            sentiment_str = ", ".join(
                f"{s}: {c}" for s, c in sorted(sentiments.items(), key=lambda x: x[1], reverse=True)
            )
            lines.extend([
                f"**Sentiment Distribution:** {sentiment_str}",
                ""
            ])
            
            # Get categories for this feature
            categories = {}
            for ticket in feature_tickets:
                cat = ticket['category']
                categories[cat] = categories.get(cat, 0) + 1
            
            category_str = ", ".join(
                f"{c}: {count}" for c, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)
            )
            lines.extend([
                f"**Feedback Types:** {category_str}",
                ""
            ])
            
            # Sample quotes for this feature
            sample_summaries = [t['short_summary'] for t in feature_tickets[:3]]
            if sample_summaries:
                lines.extend([
                    "**Player Comments:**",
                    ""
                ])
                for summary in sample_summaries:
                    lines.append(f"- \"{summary}\"")
                lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def generate_player_quotes_section(
    classifications: List[Dict[str, Any]],
    insights: AggregatedInsights
) -> str:
    """
    Generate example player quotes section for Markdown report.
    
    Args:
        classifications: List of all classifications
        insights: Aggregated insights
        
    Returns:
        Markdown formatted player quotes section
    """
    lines = [
        "## 💬 Example Player Quotes",
        "",
        "Representative feedback from players across different categories:",
        ""
    ]
    
    # Group by category
    for category in insights.category_breakdown.keys():
        category_tickets = [
            c for c in classifications
            if c['category'] == category
        ]
        
        if not category_tickets:
            continue
        
        lines.extend([
            f"### {category}",
            ""
        ])
        
        # Get diverse quotes (different sentiments)
        quotes_by_sentiment = {}
        for ticket in category_tickets:
            sentiment = ticket['sentiment']
            if sentiment not in quotes_by_sentiment:
                quotes_by_sentiment[sentiment] = []
            if len(quotes_by_sentiment[sentiment]) < 2:  # Max 2 per sentiment
                quotes_by_sentiment[sentiment].append(ticket['short_summary'])
        
        for sentiment, quotes in sorted(quotes_by_sentiment.items()):
            for quote in quotes:
                lines.append(f"- **[{sentiment}]** \"{quote}\"")
        
        lines.extend(["", ""])
    
    return "\n".join(lines)


def generate_actionable_insights_section(
    insights: AggregatedInsights,
    game_context: Optional[GameFeatureContext] = None
) -> str:
    """
    Generate actionable insights and recommendations section.
    
    Args:
        insights: Aggregated insights
        game_context: Optional game context
        
    Returns:
        Markdown formatted actionable insights section
    """
    lines = [
        "## 💡 Actionable Insights & Recommendations",
        "",
        "Based on the analysis, here are the key recommendations:",
        ""
    ]
    
    recommendations = []
    
    # Recommendation 1: Address top issues
    if insights.top_issues:
        top_3 = insights.top_issues[:3]
        lines.extend([
            "### 🎯 Priority 1: Address Top Recurring Issues",
            ""
        ])
        for i, issue in enumerate(top_3, 1):
            lines.append(
                f"{i}. **{issue['subcategory']}** - Affecting {issue['count']} players ({issue['percentage']}%)"
            )
        lines.append("")
    
    # Recommendation 2: High severity patterns
    high_severity = [p for p in insights.key_patterns if p.get('severity') == 'High']
    if high_severity:
        lines.extend([
            "### 🔴 Priority 2: Critical Pattern Alerts",
            ""
        ])
        for pattern in high_severity:
            lines.append(f"- **{pattern['description']}**")
            if pattern.get('pattern_type') == 'Negative Sentiment Cluster':
                lines.append(f"  - Recommendation: Review and improve the {pattern.get('feature')} experience")
            elif pattern.get('pattern_type') == 'Bug Concentration':
                lines.append(f"  - Recommendation: Focus QA efforts on {pattern.get('subcategory')} issues")
        lines.append("")
    
    # Recommendation 3: Recent change impacts
    if insights.recent_change_impacts:
        negative_impacts = [
            impact for impact in insights.recent_change_impacts
            if impact['sentiment_breakdown'].get('Negative', 0) > 
               impact['sentiment_breakdown'].get('Positive', 0)
        ]
        
        if negative_impacts:
            lines.extend([
                "### 🔄 Priority 3: Review Recent Updates",
                "",
                "The following recent changes received predominantly negative feedback:",
                ""
            ])
            for impact in negative_impacts[:3]:
                neg = impact['sentiment_breakdown'].get('Negative', 0)
                pos = impact['sentiment_breakdown'].get('Positive', 0)
                lines.append(
                    f"- **{impact['change_keyword']}**: {neg} negative vs {pos} positive reports"
                )
            lines.append("")
    
    # Recommendation 4: Feature improvements
    if insights.feature_breakdown:
        lines.extend([
            "### ⭐ Priority 4: Feature Enhancement Opportunities",
            ""
        ])
        
        # Look for features with high mention count
        top_features = sorted(
            insights.feature_breakdown.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        for feature, count in top_features:
            if feature != "Unspecified":
                lines.append(
                    f"- **{feature}**: {count} mentions - High player engagement, "
                    f"consider as focus area for improvements"
                )
        lines.append("")
    
    # Recommendation 5: Expected behaviors
    if insights.expected_behavior_count > 0:
        expected_pct = insights.expected_behavior_count / insights.total_tickets * 100
        if expected_pct > 20:  # More than 20% are expected behaviors
            lines.extend([
                "### 📢 Priority 5: Player Communication",
                "",
                f"- **{insights.expected_behavior_count} tickets ({expected_pct:.1f}%)** "
                f"are reporting known constraints as issues",
                f"- Recommendation: Improve in-game communication about these limitations",
                f"- Consider adding tooltips, tutorials, or FAQ entries",
                ""
            ])
    
    return "\n".join(lines)


def generate_recent_changes_section(insights: AggregatedInsights) -> str:
    """
    Generate recent changes impact section.
    
    Args:
        insights: Aggregated insights
        
    Returns:
        Markdown formatted recent changes section
    """
    if not insights.recent_change_impacts:
        return ""
    
    lines = [
        "## 🔄 Recent Changes Impact Analysis",
        "",
        "Player feedback related to recent game updates:",
        ""
    ]
    
    for impact in insights.recent_change_impacts:
        lines.extend([
            f"### {impact['change_keyword']}",
            "",
            f"**Affected Players:** {impact['affected_tickets_count']} tickets",
            ""
        ])
        
        # Sentiment breakdown
        sentiment_str = ", ".join(
            f"{s}: {c}" for s, c in impact['sentiment_breakdown'].items()
        )
        lines.extend([
            f"**Sentiment:** {sentiment_str}",
            ""
        ])
        
        # Category breakdown
        category_str = ", ".join(
            f"{c}: {count}" for c, count in impact['category_breakdown'].items()
        )
        lines.extend([
            f"**Feedback Types:** {category_str}",
            ""
        ])
        
        # Sample tickets
        if impact.get('sample_tickets'):
            lines.extend([
                "**Sample Player Feedback:**",
                ""
            ])
            for ticket in impact['sample_tickets'][:3]:
                lines.append(f"- [{ticket['sentiment']}] \"{ticket['summary']}\"")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def generate_markdown_report(
    insights: AggregatedInsights,
    classifications: List[Dict[str, Any]],
    input_params: FeedbackAnalysisInput,
    game_context: Optional[GameFeatureContext] = None
) -> str:
    """
    Generate complete Markdown report for designers.
    
    Args:
        insights: Aggregated insights
        classifications: List of all classifications
        input_params: Input parameters
        game_context: Optional game context
        
    Returns:
        Complete Markdown formatted report
    """
    logger.info("Generating Markdown report...")
    
    report_parts = [
        f"# 📋 Feedback Analysis Report: {input_params.game_name}",
        "",
        f"*Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*",
        "",
        "---",
        "",
        generate_executive_summary(insights, input_params, game_context),
        "",
        generate_top_issues_section(insights),
        "",
        generate_feature_feedback_section(insights, classifications),
        "",
        generate_recent_changes_section(insights),
        "",
        generate_player_quotes_section(classifications, insights),
        "",
        generate_actionable_insights_section(insights, game_context),
        "",
        "---",
        "",
        "## 📈 Statistical Breakdown",
        "",
        "### Category Distribution",
        ""
    ]
    
    # Add category stats
    for category, count in sorted(insights.category_breakdown.items(), key=lambda x: x[1], reverse=True):
        percentage = count / insights.total_tickets * 100
        report_parts.append(f"- **{category}**: {count} ({percentage:.1f}%)")
    
    report_parts.extend(["", "### Sentiment Distribution", ""])
    
    # Add sentiment stats
    for sentiment, count in sorted(insights.sentiment_breakdown.items(), key=lambda x: x[1], reverse=True):
        percentage = count / insights.total_tickets * 100
        report_parts.append(f"- **{sentiment}**: {count} ({percentage:.1f}%)")
    
    report_parts.extend([
        "",
        "---",
        "",
        "*This report was automatically generated by the Freshdesk Feedback AI Analysis System*"
    ])
    
    logger.info("✓ Markdown report generated successfully")
    
    return "\n".join(report_parts)


def generate_json_insights(
    insights: AggregatedInsights,
    classifications: List[Dict[str, Any]],
    input_params: FeedbackAnalysisInput,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate structured JSON insights report.
    
    Args:
        insights: Aggregated insights
        classifications: List of all classifications
        input_params: Input parameters
        metadata: Additional metadata
        
    Returns:
        Dictionary ready for JSON export
    """
    logger.info("Generating JSON insights report...")
    
    json_report = {
        'report_metadata': {
            'game_name': input_params.game_name,
            'platform': input_params.os,
            'analysis_period': {
                'start_date': input_params.start_date,
                'end_date': input_params.end_date
            },
            'generated_at': datetime.now().isoformat(),
            'total_tickets_analyzed': insights.total_tickets,
            'ai_average_confidence': insights.average_confidence
        },
        'summary': {
            'total_tickets': insights.total_tickets,
            'expected_behaviors': insights.expected_behavior_count,
            'average_confidence': insights.average_confidence,
            'category_breakdown': insights.category_breakdown,
            'sentiment_breakdown': insights.sentiment_breakdown,
            'intent_breakdown': insights.intent_breakdown,
            'feature_breakdown': insights.feature_breakdown
        },
        'top_issues': insights.top_issues,
        'recent_change_impacts': insights.recent_change_impacts,
        'patterns': insights.key_patterns,
        'detailed_classifications': classifications,
        'metadata': metadata
    }
    
    logger.info("✓ JSON insights report generated successfully")
    
    return json_report


def save_reports(
    insights: AggregatedInsights,
    classifications: List[Dict[str, Any]],
    input_params: FeedbackAnalysisInput,
    game_context: Optional[GameFeatureContext] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Path]:
    """
    Generate and save both Markdown and JSON reports.
    
    Args:
        insights: Aggregated insights
        classifications: List of all classifications
        input_params: Input parameters
        game_context: Optional game context
        metadata: Optional additional metadata
        
    Returns:
        Dictionary with paths to saved reports
    """
    logger.info("="*70)
    logger.info("Generating and saving reports")
    logger.info("="*70)
    
    # Ensure directories exist
    REPORTS_MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_JSON_DIR.mkdir(parents=True, exist_ok=True)
    
    # Build deterministic filenames
    safe_game_name = sanitize_filename(input_params.game_name)
    timestamp = get_timestamp()
    
    base_filename = (
        f"{safe_game_name}_{input_params.os}_"
        f"{input_params.start_date}_to_{input_params.end_date}_{timestamp}"
    )
    
    # Generate and save Markdown report
    markdown_content = generate_markdown_report(
        insights,
        classifications,
        input_params,
        game_context
    )
    
    markdown_filename = f"report_{base_filename}.md"
    markdown_path = REPORTS_MARKDOWN_DIR / markdown_filename
    save_markdown(markdown_content, markdown_path)
    
    logger.info(f"✓ Markdown report saved: {markdown_filename}")
    
    # Generate and save JSON insights
    json_insights = generate_json_insights(
        insights,
        classifications,
        input_params,
        metadata or {}
    )
    
    json_filename = f"insights_{base_filename}.json"
    json_path = REPORTS_JSON_DIR / json_filename
    save_json(json_insights, json_path)
    
    logger.info(f"✓ JSON insights saved: {json_filename}")
    
    logger.info("="*70)
    logger.info("✓ Report generation complete")
    logger.info("="*70)
    
    return {
        'markdown': markdown_path,
        'json': json_path
    }


if __name__ == "__main__":
    # Test report generation
    print("\n" + "="*70)
    print("  TESTING REPORT GENERATOR")
    print("="*70 + "\n")
    
    # Create sample data for testing
    from src.aggregator import AggregatedInsights
    from src.input_handler import FeedbackAnalysisInput
    
    sample_insights = AggregatedInsights(
        total_tickets=100,
        category_breakdown={'Bug': 45, 'Feature Request': 30, 'Positive Feedback': 25},
        sentiment_breakdown={'Negative': 50, 'Positive': 35, 'Neutral': 15},
        intent_breakdown={'Report Bug': 45, 'Request Feature': 30, 'Praise Game': 25},
        feature_breakdown={'Level progression': 40, 'IAP': 30, 'UI': 20, 'Social': 10},
        top_issues=[
            {
                'category': 'Bug',
                'subcategory': 'Crash/Freeze',
                'count': 25,
                'percentage': 25.0,
                'avg_confidence': 0.95,
                'sentiment_breakdown': {'Negative': 24, 'Neutral': 1},
                'sample_summaries': [
                    'Game crashes on level 50',
                    'Freeze when opening shop',
                    'App crashes during event'
                ],
                'ticket_ids': [1, 2, 3]
            }
        ],
        recent_change_impacts=[],
        expected_behavior_count=10,
        average_confidence=0.92,
        key_patterns=[
            {
                'pattern_type': 'Negative Sentiment Cluster',
                'description': 'Lives system has 80% negative feedback',
                'severity': 'High',
                'feature': 'Lives system'
            }
        ]
    )
    
    sample_classifications = [
        {
            'ticket_id': 1,
            'category': 'Bug',
            'subcategory': 'Crash/Freeze',
            'sentiment': 'Negative',
            'intent': 'Report Bug',
            'confidence': 0.95,
            'short_summary': 'Game crashes on level 50',
            'related_feature': 'Level progression'
        }
    ]
    
    sample_params = FeedbackAnalysisInput(
        game_name="Test Game",
        os="Android",
        start_date="2024-01-01",
        end_date="2024-01-31"
    )
    
    print("1. Generating Markdown report...")
    markdown = generate_markdown_report(
        sample_insights,
        sample_classifications,
        sample_params
    )
    print(f"   ✓ Generated {len(markdown)} characters\n")
    
    print("2. Preview (first 500 chars):")
    print(markdown[:500])
    print("   ...\n")
    
    print("3. Generating JSON insights...")
    json_insights = generate_json_insights(
        sample_insights,
        sample_classifications,
        sample_params,
        {}
    )
    print(f"   ✓ Generated with {len(json_insights)} top-level keys\n")
    
    print("="*70)
    print("✅ Report generator test completed successfully!")
    print("="*70 + "\n")
