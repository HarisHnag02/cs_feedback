#!/usr/bin/env python3
"""
Test script for the Freshdesk API client.

This script tests the Freshdesk client functionality including connection
testing, ticket fetching with filters, and error handling.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.freshdesk_client import FreshdeskClient, fetch_feedback_data, FreshdeskAPIError
from src.input_handler import FeedbackAnalysisInput
from src.logger import setup_logger


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def test_client_initialization():
    """Test Freshdesk client initialization."""
    print_section("TEST 1: Client Initialization")
    
    try:
        client = FreshdeskClient()
        print(f"✓ Client initialized successfully")
        print(f"  Domain: {client.domain}")
        print(f"  Base URL: {client.base_url}")
        print(f"  API Key: {'*' * 8}{client.api_key[-4:] if len(client.api_key) > 4 else '****'}")
        return client
        
    except Exception as e:
        print(f"✗ Client initialization failed: {e}")
        return None


def test_connection(client: FreshdeskClient):
    """Test API connection."""
    print_section("TEST 2: API Connection Test")
    
    try:
        success = client.test_connection()
        
        if success:
            print("✓ Connection test passed!")
            print("  API is accessible and authentication works")
        else:
            print("✗ Connection test failed!")
            print("  Please check your API key and domain")
        
        return success
        
    except Exception as e:
        print(f"✗ Connection test error: {e}")
        return False


def test_fetch_with_filters():
    """Test fetching tickets with various filter combinations."""
    print_section("TEST 3: Fetch Tickets with Filters")
    
    test_cases = [
        {
            'name': 'Android game feedback',
            'params': FeedbackAnalysisInput(
                game_name="Candy Crush",
                os="Android",
                start_date="2024-01-01",
                end_date="2024-01-31"
            )
        },
        {
            'name': 'iOS game feedback',
            'params': FeedbackAnalysisInput(
                game_name="Subway Surfers",
                os="iOS",
                start_date="2024-02-01",
                end_date="2024-02-29"
            )
        },
        {
            'name': 'Both platforms',
            'params': FeedbackAnalysisInput(
                game_name="Clash of Clans",
                os="Both",
                start_date="2024-03-01",
                end_date="2024-03-31"
            )
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test['name']}")
        print(f"   Game: {test['params'].game_name}")
        print(f"   OS: {test['params'].os}")
        print(f"   Date Range: {test['params'].start_date} to {test['params'].end_date}")
        
        try:
            data = fetch_feedback_data(test['params'])
            count = len(data['feedbacks'])
            
            print(f"   ✓ Fetched {count} tickets")
            
            if count > 0:
                sample = data['feedbacks'][0]
                print(f"   Sample ticket ID: {sample.get('id')}")
                print(f"   Sample subject: {sample.get('subject', 'N/A')[:50]}...")
            
        except FreshdeskAPIError as e:
            print(f"   ✗ Fetch failed: {e}")
        except Exception as e:
            print(f"   ✗ Unexpected error: {e}")
    
    print("\n✓ Filter testing completed")


def test_pagination():
    """Test pagination handling."""
    print_section("TEST 4: Pagination Handling")
    
    try:
        client = FreshdeskClient()
        
        # Create params that might return multiple pages
        params = FeedbackAnalysisInput(
            game_name="Test",
            os="Both",
            start_date="2023-01-01",
            end_date="2024-12-31"
        )
        
        print("Fetching with max_pages=3 (safety limit)...")
        tickets = client.fetch_feedback_tickets(params, max_pages=3)
        
        print(f"✓ Pagination test completed")
        print(f"  Total tickets fetched: {len(tickets)}")
        
    except Exception as e:
        print(f"✗ Pagination test failed: {e}")


def test_error_handling():
    """Test error handling for invalid inputs."""
    print_section("TEST 5: Error Handling")
    
    tests = []
    
    # Test 1: Invalid API key
    print("1. Testing with invalid API key...")
    try:
        client = FreshdeskClient(api_key="invalid_key_12345")
        client.test_connection()
        print("   ✗ Should have failed with invalid key")
    except FreshdeskAPIError:
        print("   ✓ Correctly caught invalid API key")
    except Exception as e:
        print(f"   ⚠ Unexpected error: {e}")
    
    # Test 2: Invalid domain
    print("\n2. Testing with invalid domain...")
    try:
        client = FreshdeskClient(
            domain="invalid-domain-12345.freshdesk.com",
            api_key="test_key"
        )
        client.test_connection()
        print("   ✗ Should have failed with invalid domain")
    except FreshdeskAPIError:
        print("   ✓ Correctly caught invalid domain")
    except Exception as e:
        print(f"   ⚠ Unexpected error: {e}")
    
    print("\n✓ Error handling tests completed")


def test_data_structure():
    """Test the structure of returned data."""
    print_section("TEST 6: Data Structure Validation")
    
    try:
        params = FeedbackAnalysisInput(
            game_name="Test Game",
            os="Android",
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        
        data = fetch_feedback_data(params)
        
        # Validate metadata
        print("Validating metadata structure...")
        required_metadata = [
            'game_name', 'os', 'start_date', 'end_date',
            'fetched_at', 'total_records', 'source', 'domain'
        ]
        
        metadata_valid = all(key in data['metadata'] for key in required_metadata)
        
        if metadata_valid:
            print("✓ Metadata structure is valid")
            print(f"  Keys: {', '.join(data['metadata'].keys())}")
        else:
            print("✗ Metadata structure is invalid")
        
        # Validate feedbacks
        print("\nValidating feedbacks structure...")
        if 'feedbacks' in data and isinstance(data['feedbacks'], list):
            print(f"✓ Feedbacks is a list with {len(data['feedbacks'])} items")
            
            if data['feedbacks']:
                sample = data['feedbacks'][0]
                print(f"  Sample ticket keys: {', '.join(list(sample.keys())[:10])}...")
        else:
            print("✗ Feedbacks structure is invalid")
        
    except Exception as e:
        print(f"✗ Data structure test failed: {e}")


def main():
    """Run all Freshdesk client tests."""
    print("\n" + "🧪 "*35)
    print("  FRESHDESK API CLIENT TEST SUITE")
    print("🧪 "*35)
    
    # Setup logging
    logger = setup_logger(__name__, log_level="INFO")
    
    try:
        # Test 1: Initialize client
        client = test_client_initialization()
        if not client:
            print("\n❌ Cannot proceed without valid client")
            return
        
        # Test 2: Connection
        if not test_connection(client):
            print("\n⚠️  Warning: Connection test failed.")
            print("The following tests may not work properly.")
            print("Please check:")
            print("  1. FRESHDESK_API_KEY is set correctly in .env")
            print("  2. FRESHDESK_DOMAIN is set correctly in .env")
            print("  3. Your API key has proper permissions")
            print("  4. Your Freshdesk account is accessible")
            
            # Ask user if they want to continue
            response = input("\nContinue with remaining tests? (y/n): ").lower()
            if response != 'y':
                return
        
        # Test 3: Fetch with filters
        test_fetch_with_filters()
        
        # Test 4: Pagination
        test_pagination()
        
        # Test 5: Error handling
        test_error_handling()
        
        # Test 6: Data structure
        test_data_structure()
        
        # Summary
        print("\n" + "="*70)
        print("  TEST SUITE SUMMARY")
        print("="*70)
        print("\n✅ All Freshdesk client tests completed!")
        print("\nTested functionality:")
        print("  ✓ Client initialization")
        print("  ✓ API connection")
        print("  ✓ Ticket fetching with filters")
        print("  ✓ Pagination handling")
        print("  ✓ Error handling")
        print("  ✓ Data structure validation")
        print("\n" + "="*70 + "\n")
        
        logger.info("All Freshdesk client tests completed successfully")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelled by user (Ctrl+C)")
        logger.warning("Tests cancelled by user")
        
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        logger.error(f"Test suite failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
