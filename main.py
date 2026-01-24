#!/usr/bin/env python3
"""
Main entry point for the Freshdesk Feedback AI Analysis System.

This script orchestrates the complete feedback analysis workflow:
1. Input collection (interactive CLI)
2. Cache check (intelligent caching)
3. Fetch from Freshdesk (ONLY on cache miss)
4. Data cleaning (noise removal)
5. Game context loading (feature context)
6. AI classification (OpenAI with context)
7. Pattern aggregation (insights extraction)
8. Report generation (Markdown + JSON)
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.aggregator import aggregate_classifications
from src.ai_classifier import classify_feedback_data, save_classification_results, AIClassifierError
from src.config import ensure_directories, get_settings
from src.context_loader import load_game_context, ContextLoaderError
from src.data_cleaner import clean_feedback_data
from src.freshdesk_client import fetch_feedback_data, FreshdeskAPIError
from src.input_handler import get_validated_inputs
from src.logger import setup_logger
from src.report_generator import save_reports
from src import storage_manager


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def main():
    """
    Main application entry point.
    
    Orchestrates the complete feedback analysis workflow following the pipeline:
    Input → Cache → Fetch → Clean → Context → AI → Aggregate → Report
    """
    # Setup logging
    logger = setup_logger(__name__, log_level="INFO")
    
    try:
        # ===================================================================
        # INITIALIZATION
        # ===================================================================
        logger.info("="*70)
        logger.info("Starting Freshdesk Feedback AI Analysis System")
        logger.info("="*70)
        
        # Ensure all required directories exist
        logger.info("Ensuring required directories exist...")
        ensure_directories()
        
        # Load and validate configuration
        logger.info("Loading configuration...")
        try:
            settings = get_settings()
            logger.info("✓ Configuration loaded successfully")
        except Exception as e:
            logger.error(f"✗ Configuration error: {e}")
            print("\n❌ Configuration Error!")
            print("\nPlease ensure:")
            print("1. .env file exists in the project root")
            print("2. Required environment variables are set:")
            print("   - FRESHDESK_API_KEY")
            print("   - FRESHDESK_DOMAIN")
            print("   - OPENAI_API_KEY")
            print("\nYou can copy .env.example to .env and fill in your keys.")
            return 1
        
        # ===================================================================
        # STEP 1: INPUT COLLECTION
        # ===================================================================
        logger.info("STEP 1: Starting interactive input collection...")
        user_inputs = get_validated_inputs()
        
        logger.info("User inputs collected:")
        logger.info(f"  Game Name: {user_inputs.game_name}")
        logger.info(f"  OS: {user_inputs.os}")
        logger.info(f"  Date Range: {user_inputs.start_date} to {user_inputs.end_date}")
        
        print_header("INPUT COLLECTION COMPLETE")
        print(f"\n📋 Analysis Parameters:")
        print(user_inputs)
        
        # ===================================================================
        # STEP 2: CACHE CHECK
        # ===================================================================
        logger.info("STEP 2: Checking for cached data...")
        feedback_data = None
        used_cache = False
        
        if storage_manager.exists(user_inputs):
            # Cache HIT
            cache_info = storage_manager.get_cache_info(user_inputs)
            print_header("CACHE STATUS: HIT")
            print(f"\n✅ Found cached data:")
            print(f"   File: {cache_info['filename']}")
            print(f"   Size: {cache_info['size_kb']} KB")
            
            # Ask user if they want to use cache or fetch fresh
            use_cache = input("\n   Use cached data? (y/n): ").strip().lower()
            
            if use_cache in ['y', 'yes']:
                print("\n📂 Loading cached data...")
                feedback_data = storage_manager.load(user_inputs)
                used_cache = True
                logger.info("✓ Loaded data from cache (Freshdesk API not called)")
            else:
                print("\n🗑️  Clearing old cache...")
                storage_manager.delete(user_inputs)
                logger.info("User chose to fetch fresh data")
        else:
            # Cache MISS
            print_header("CACHE STATUS: MISS")
            print("\n⚠️  No cached data found.")
            print("   Fresh data will be fetched from Freshdesk API.")
            logger.info("Cache miss - will fetch from Freshdesk")
        
        # ===================================================================
        # STEP 3: FETCH FROM FRESHDESK (ONLY ON CACHE MISS)
        # ===================================================================
        if feedback_data is None:
            logger.info("STEP 3: Fetching data from Freshdesk API...")
            print_header("FETCHING FROM FRESHDESK API")
            
            print(f"\n🔌 Connecting to Freshdesk...")
            print(f"   Game: {user_inputs.game_name}")
            print(f"   OS: {user_inputs.os}")
            print(f"   Date Range: {user_inputs.start_date} to {user_inputs.end_date}")
            print("\n⏳ Fetching tickets (this may take a moment)...\n")
            
            try:
                # Fetch fresh data from Freshdesk API
                feedback_data = fetch_feedback_data(user_inputs)
                
                print(f"\n✅ Successfully fetched {len(feedback_data['feedbacks'])} tickets!")
                logger.info(f"✓ Fetched {len(feedback_data['feedbacks'])} tickets from Freshdesk")
                
                # Save to cache for future use
                print("\n💾 Saving to cache for future use...")
                storage_manager.save(user_inputs, feedback_data)
                logger.info("✓ Data cached successfully")
                
            except FreshdeskAPIError as e:
                print(f"\n❌ Failed to fetch from Freshdesk: {e}")
                logger.error(f"Freshdesk API error: {e}")
                print("\nPlease check:")
                print("  1. FRESHDESK_API_KEY is correct")
                print("  2. FRESHDESK_DOMAIN is correct")
                print("  3. Your Freshdesk account is accessible")
                return 1
            except Exception as e:
                print(f"\n❌ Unexpected error during fetch: {e}")
                logger.error(f"Fetch error: {e}", exc_info=True)
                return 1
        else:
            logger.info("STEP 3: Skipped (using cached data)")
        
        # ===================================================================
        # STEP 4: DATA CLEANING
        # ===================================================================
        logger.info("STEP 4: Cleaning feedback data...")
        print_header("CLEANING FEEDBACK DATA")
        
        print("\n🧹 Removing noise from feedback...")
        print("   ⚙️  Removing auto-replies and system messages")
        print("   ⚙️  Removing email signatures")
        print("   ⚙️  Removing HTML tags and formatting")
        print("   ⚙️  Removing quoted replies and URLs")
        print("   ⚙️  Normalizing whitespace")
        
        try:
            cleaned_data = clean_feedback_data(feedback_data)
            
            print(f"\n✅ Cleaning complete!")
            print(f"   Original: {cleaned_data['metadata'].get('original_count', len(feedback_data.get('feedbacks', [])))} tickets")
            print(f"   Cleaned: {cleaned_data['metadata'].get('cleaned_count', len(cleaned_data.get('feedbacks', [])))} tickets")
            logger.info("✓ Data cleaning completed successfully")
            
        except Exception as e:
            print(f"\n❌ Data cleaning failed: {e}")
            logger.error(f"Cleaning error: {e}", exc_info=True)
            return 1
        
        # Display cleaned data summary
        print_header("DATA SUMMARY")
        print(f"\n📊 Dataset Overview:")
        print(f"   Total Tickets: {len(cleaned_data['feedbacks'])} (Status=5 Closed, all types)")
        print(f"   Game: {cleaned_data['metadata']['game_name']}")
        print(f"   Platform: {cleaned_data['metadata']['os']}")
        print(f"   Date Range: {cleaned_data['metadata']['start_date']} to {cleaned_data['metadata']['end_date']}")
        print(f"   Source: {'Cache' if used_cache else 'Freshdesk API'}")
        print(f"\n💡 Note: Filtering to Feedback type happens in AI classification step")
        
        if cleaned_data['feedbacks']:
            print(f"\n📝 Sample Clean Tickets (first 3):")
            for i, ticket in enumerate(cleaned_data['feedbacks'][:3], 1):
                print(f"\n   {i}. Ticket #{ticket.get('ticket_id')}")
                print(f"      Subject: {ticket.get('subject', 'N/A')}")
                print(f"      Created: {ticket.get('created_date', 'N/A')[:10]}")
                feedback_preview = ticket.get('clean_feedback', '')[:80]
                print(f"      Clean Feedback: \"{feedback_preview}...\"")
        
        # ===================================================================
        # STEP 5: LOAD GAME CONTEXT
        # ===================================================================
        logger.info("STEP 5: Loading game feature context...")
        game_context = None
        
        try:
            game_context = load_game_context(game_name=user_inputs.game_name)
            
            print_header("GAME CONTEXT LOADED")
            print(f"\n✅ Context loaded for '{game_context.game_name}'")
            print(f"   📋 Current Features: {len(game_context.current_features)}")
            print(f"   ⚠️  Known Constraints: {len(game_context.known_constraints)}")
            print(f"   🔄 Recent Changes: {len(game_context.recent_changes)}")
            
            logger.info(f"✓ Game context loaded successfully")
            
        except ContextLoaderError as e:
            print_header("GAME CONTEXT NOT AVAILABLE")
            print(f"\n⚠️  {e}")
            print("\n   Continuing without game context...")
            print("   Note: AI analysis will be less context-aware.")
            logger.warning(f"Failed to load game context: {e}")
        
        # ===================================================================
        # STEP 6: AI CLASSIFICATION
        # ===================================================================
        logger.info("STEP 6: AI classification with OpenAI...")
        print_header("AI CLASSIFICATION")
        
        print("\n🤖 Ready for AI-powered analysis:")
        print(f"   ✓ {len(cleaned_data['feedbacks'])} cleaned tickets")
        if game_context:
            print(f"   ✓ Game context loaded ({len(game_context.current_features)} features)")
        else:
            print(f"   ⚠️  No game context (will proceed without context)")
        
        # Cost estimate and user confirmation
        estimated_cost = len(cleaned_data['feedbacks']) * 0.01
        print(f"\n💰 Cost Estimate:")
        print(f"   Tickets to classify: {len(cleaned_data['feedbacks'])}")
        print(f"   Estimated cost: ~${estimated_cost:.2f}")
        print(f"   Model: OpenAI GPT-4 Turbo")
        print(f"   Temperature: 0 (deterministic)")
        
        proceed = input("\n   Proceed with AI classification? (yes/no): ").strip().lower()
        
        if proceed not in ['yes', 'y']:
            print("\n   ⏭️  Skipping AI classification.")
            logger.info("User chose to skip AI classification")
            print_header("ANALYSIS COMPLETE")
            print("\n✅ Data collection and cleaning completed successfully!")
            print(f"\n📂 Cleaned data available with {len(cleaned_data['feedbacks'])} tickets")
            print("   AI classification was skipped.")
            return 0
        
        # Proceed with AI classification
        print("\n🤖 Starting AI classification...")
        print("   ⚙️  Using OpenAI GPT-4 Turbo")
        print("   ⚙️  Temperature: 0 (consistent results)")
        print("   ⚙️  Retry logic: Enabled (3 attempts)")
        print("   ⏳ This may take several minutes...\n")
        
        try:
            # Classify tickets with AI
            classified_data = classify_feedback_data(
                cleaned_data,
                game_context=game_context,
                model="gpt-4-turbo-preview"
            )
            
            classifications = classified_data['classifications']
            metadata = classified_data['metadata']
            filtering_stats = classified_data.get('filtering_stats', {})
            
            # Display classification results
            print_header("CLASSIFICATION RESULTS")
            
            # Show filtering statistics
            print(f"\n🔍 Filtering Statistics:")
            print(f"   Closed Tickets (status=5): {filtering_stats.get('closed_tickets', 'N/A')}")
            print(f"   Feedback Type: {filtering_stats.get('feedback_tickets', 'N/A')}")
            print(f"   Non-Feedback Filtered Out: {filtering_stats.get('filtered_out', 'N/A')}")
            
            print(f"\n✅ Successfully classified {len(classifications)} Feedback tickets")
            print(f"   Success Rate: {metadata['classification_success_rate']}%")
            print(f"   AI Model: {metadata['classification_model']}")
            print(f"   Average Confidence: {metadata.get('average_confidence', 'N/A')}")
            
            # Show sample classifications
            if classifications:
                print(f"\n📊 Sample Classifications (first 3):")
                for i, cls in enumerate(classifications[:3], 1):
                    print(f"\n   {i}. Ticket #{cls['ticket_id']}")
                    print(f"      Category: {cls['category']} > {cls['subcategory']}")
                    print(f"      Sentiment: {cls['sentiment']}")
                    print(f"      Intent: {cls['intent']}")
                    print(f"      Confidence: {cls['confidence']:.0%}")
                    print(f"      Summary: {cls['short_summary']}")
            
            # Save classification results
            print(f"\n💾 Saving classification results to data/processed/...")
            saved_path = save_classification_results(classified_data, user_inputs)
            print(f"   ✓ Saved to: {saved_path.name}")
            
            logger.info(f"✓ AI classification completed successfully")
            
        except AIClassifierError as e:
            print(f"\n❌ AI classification failed: {e}")
            logger.error(f"AI classification error: {e}")
            print("\nPlease check:")
            print("  1. OPENAI_API_KEY is correct")
            print("  2. You have sufficient OpenAI credits")
            print("  3. Network connection is stable")
            return 1
        except Exception as e:
            print(f"\n❌ Unexpected error during classification: {e}")
            logger.error(f"Classification error: {e}", exc_info=True)
            return 1
        
        # ===================================================================
        # STEP 7: PATTERN AGGREGATION
        # ===================================================================
        logger.info("STEP 7: Aggregating insights and patterns...")
        print_header("AGGREGATING INSIGHTS")
        
        print("\n📊 Analyzing patterns and trends...")
        print("   ⚙️  Grouping by category, feature, sentiment")
        print("   ⚙️  Identifying top recurring issues")
        print("   ⚙️  Detecting recent change impacts")
        print("   ⚙️  Finding critical patterns")
        
        try:
            insights = aggregate_classifications(classified_data, game_context)
            
            # Display aggregated insights
            print_header("AGGREGATED INSIGHTS")
            
            print(f"\n📈 Overview:")
            print(f"   Total Tickets: {insights.total_tickets}")
            print(f"   Average AI Confidence: {insights.average_confidence:.1%}")
            print(f"   Expected Behaviors: {insights.expected_behavior_count} "
                  f"({insights.expected_behavior_count/insights.total_tickets*100:.1f}%)")
            
            print(f"\n📊 Category Distribution:")
            for category, count in sorted(insights.category_breakdown.items(), 
                                         key=lambda x: x[1], reverse=True):
                percentage = count / insights.total_tickets * 100
                print(f"   • {category}: {count} ({percentage:.1f}%)")
            
            print(f"\n😊 Sentiment Analysis:")
            for sentiment, count in sorted(insights.sentiment_breakdown.items(), 
                                          key=lambda x: x[1], reverse=True):
                percentage = count / insights.total_tickets * 100
                print(f"   • {sentiment}: {count} ({percentage:.1f}%)")
            
            if insights.top_issues:
                print(f"\n🔝 Top {min(5, len(insights.top_issues))} Recurring Issues:")
                for i, issue in enumerate(insights.top_issues[:5], 1):
                    print(f"\n   {i}. {issue['category']} > {issue['subcategory']}")
                    print(f"      Frequency: {issue['count']} tickets ({issue['percentage']}%)")
                    sentiment_str = ', '.join(f"{s}:{c}" for s, c in issue['sentiment_breakdown'].items())
                    print(f"      Sentiment: {sentiment_str}")
            
            if insights.feature_breakdown:
                print(f"\n🎮 Most Discussed Features:")
                top_features = sorted(insights.feature_breakdown.items(), 
                                     key=lambda x: x[1], reverse=True)[:5]
                for feature, count in top_features:
                    if feature != "Unspecified":
                        percentage = count / insights.total_tickets * 100
                        print(f"   • {feature}: {count} mentions ({percentage:.1f}%)")
            
            if insights.recent_change_impacts:
                print(f"\n🔄 Recent Change Impact:")
                print(f"   Detected {len(insights.recent_change_impacts)} recent changes with player feedback")
                for impact in insights.recent_change_impacts[:3]:
                    print(f"\n   • '{impact['change_keyword']}': {impact['affected_tickets_count']} tickets")
                    sentiment_str = ', '.join(f"{s}:{c}" for s, c in impact['sentiment_breakdown'].items())
                    print(f"     Sentiment: {sentiment_str}")
            
            if insights.key_patterns:
                print(f"\n🔍 Critical Patterns Detected:")
                for pattern in insights.key_patterns[:5]:
                    severity_emoji = {
                        'High': '🔴',
                        'Medium': '🟡',
                        'Low': '🟢'
                    }.get(pattern.get('severity', 'Low'), '⚪')
                    print(f"   {severity_emoji} {pattern['description']}")
            
            logger.info("✓ Aggregation completed successfully")
            
        except Exception as e:
            print(f"\n❌ Aggregation failed: {e}")
            logger.error(f"Aggregation error: {e}", exc_info=True)
            return 1
        
        # ===================================================================
        # STEP 8: REPORT GENERATION
        # ===================================================================
        logger.info("STEP 8: Generating reports...")
        print_header("GENERATING REPORTS")
        
        print("\n📝 Creating comprehensive reports...")
        print("   ⚙️  Markdown report for designers")
        print("   ⚙️  JSON insights for data analysis")
        
        try:
            report_paths = save_reports(
                insights,
                classifications,
                user_inputs,
                game_context,
                metadata=classified_data.get('metadata', {})
            )
            
            print("\n✅ Reports generated successfully!")
            
            print(f"\n📄 Markdown Report (for designers):")
            print(f"   File: {report_paths['markdown'].name}")
            print(f"   Location: {report_paths['markdown'].parent}/")
            
            print(f"\n📊 JSON Insights (for analysis):")
            print(f"   File: {report_paths['json'].name}")
            print(f"   Location: {report_paths['json'].parent}/")
            
            logger.info("✓ Report generation completed successfully")
            
        except Exception as e:
            print(f"\n⚠️  Report generation failed: {e}")
            logger.error(f"Report generation error: {e}", exc_info=True)
            print("\n   Analysis data is still available in data/processed/")
        
        # ===================================================================
        # COMPLETION
        # ===================================================================
        print_header("ANALYSIS PIPELINE COMPLETE")
        
        print("\n🎉 Feedback analysis completed successfully!")
        
        print("\n📂 Generated Files:")
        print(f"   • Markdown Report: reports/markdown/")
        print(f"   • JSON Insights: reports/json/")
        print(f"   • Classifications: data/processed/")
        if not used_cache:
            print(f"   • Raw Data Cache: data/raw/")
        
        print("\n✨ Next Steps:")
        print("   1. 📖 Review the Markdown report for actionable insights")
        print("   2. 🤝 Share findings with your team")
        print("   3. 🎯 Prioritize issues based on frequency and severity")
        print("   4. 📊 Use JSON data for custom analysis or dashboards")
        
        print("\n" + "="*60)
        logger.info("="*70)
        logger.info("Application completed successfully")
        logger.info("="*70)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Application interrupted by user (Ctrl+C).")
        logger.warning("Application interrupted by user")
        return 130
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n\n❌ An unexpected error occurred: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check the error message above")
        print("   2. Verify all environment variables are set")
        print("   3. Ensure you have network connectivity")
        print("   4. Check that all required files exist")
        return 1


if __name__ == "__main__":
    sys.exit(main())
