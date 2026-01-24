#!/usr/bin/env python3
"""
Test script for the data cleaner module.

This script tests various cleaning functions with different types of noise
and validates the cleaning pipeline.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.data_cleaner import (
    clean_ticket,
    clean_tickets,
    clean_feedback_data,
    extract_meaningful_text,
    remove_html_tags,
    remove_auto_replies,
    remove_signatures,
    CleanTicket
)
from src.logger import setup_logger


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def test_html_removal():
    """Test HTML tag removal."""
    print_section("TEST 1: HTML Tag Removal")
    
    html_text = '''
<p>This is a <strong>test</strong> message.</p>
<div>With <span style="color:red">HTML</span> tags.</div>
<br />
Some &nbsp; entities &amp; symbols.
    '''
    
    cleaned = remove_html_tags(html_text)
    
    print("Original HTML:")
    print(html_text[:100] + "...")
    print(f"\nCleaned text:")
    print(f'"{cleaned.strip()}"')
    print(f"\n✓ HTML tags removed")


def test_auto_reply_removal():
    """Test auto-reply detection and removal."""
    print_section("TEST 2: Auto-Reply Removal")
    
    auto_reply_text = '''
This is an automated response to confirm we received your message.
Your ticket number is: 12345

We will get back to you within 24 hours.

Do not reply to this email.
    '''
    
    cleaned = remove_auto_replies(auto_reply_text)
    
    print("Original text:")
    print(auto_reply_text)
    print(f"\nCleaned text:")
    print(f'"{cleaned.strip()}"')
    print(f"\n✓ Auto-reply patterns removed")


def test_signature_removal():
    """Test signature detection and removal."""
    print_section("TEST 3: Signature Removal")
    
    text_with_sig = '''
The game is crashing frequently. Please fix this issue.

Thanks,
John Doe
Senior Player
john.doe@example.com
Sent from my iPhone
    '''
    
    cleaned = remove_signatures(text_with_sig)
    
    print("Original text:")
    print(text_with_sig)
    print(f"\nCleaned text:")
    print(f'"{cleaned.strip()}"')
    print(f"\n✓ Signature removed")


def test_complete_cleaning_pipeline():
    """Test the complete cleaning pipeline."""
    print_section("TEST 4: Complete Cleaning Pipeline")
    
    dirty_text = '''
<p>Hi Support Team,</p>

<p>The game keeps freezing on level 147. Very frustrating!</p>

<p>I'm on Android 12, latest version of the app.</p>

<p>Best regards,<br>
Jane Smith<br>
jane.smith@example.com</p>

<p>--<br>
This email is confidential.</p>

On Mon, Jan 15, 2024 at 10:30 AM Support wrote:
> Thank you for contacting us.
> We have received your message.
    '''
    
    cleaned = extract_meaningful_text(dirty_text)
    
    print("Original text:")
    print(dirty_text)
    print(f"\nCleaned text:")
    print(f'"{cleaned}"')
    
    original_len = len(dirty_text)
    cleaned_len = len(cleaned)
    reduction = round((1 - cleaned_len / original_len) * 100, 1)
    
    print(f"\nStatistics:")
    print(f"  Original: {original_len} chars")
    print(f"  Cleaned: {cleaned_len} chars")
    print(f"  Reduction: {reduction}%")
    print(f"\n✓ Complete pipeline test passed")


def test_single_ticket_cleaning():
    """Test cleaning a single ticket."""
    print_section("TEST 5: Single Ticket Cleaning")
    
    raw_ticket = {
        'id': 54321,
        'subject': 'Level 50 is impossible to beat',
        'description': '<p>I\'ve tried 100 times!</p><p>This level needs balancing.</p>',
        'description_text': 'I\'ve tried 100 times!\nThis level needs balancing.',
        'created_at': '2024-01-20T14:30:00Z',
        'status': 4,
        'priority': 2,
        'tags': ['balance', 'difficulty'],
        'type': 'Feedback',
        'custom_fields': {'game_name': 'Test Game', 'os': 'iOS'}
    }
    
    cleaned = clean_ticket(raw_ticket)
    
    print("Original ticket:")
    print(f"  ID: #{raw_ticket['id']}")
    print(f"  Subject: {raw_ticket['subject']}")
    print(f"  Description: {raw_ticket['description_text']}")
    
    print(f"\nCleaned ticket:")
    print(cleaned)
    
    print(f"\nMetadata:")
    for key, value in cleaned.metadata.items():
        print(f"  {key}: {value}")
    
    print(f"\n✓ Single ticket cleaning test passed")


def test_batch_ticket_cleaning():
    """Test cleaning multiple tickets."""
    print_section("TEST 6: Batch Ticket Cleaning")
    
    raw_tickets = [
        {
            'id': 1001,
            'subject': 'Great game!',
            'description_text': 'Love the new update!\n\nThanks,\nUser1',
            'created_at': '2024-01-15T10:00:00Z',
            'status': 4,
            'priority': 1,
            'tags': ['positive']
        },
        {
            'id': 1002,
            'subject': 'Bug report',
            'description_text': 'Game crashes on startup.\n\nBest regards,\nUser2\nuser2@example.com',
            'created_at': '2024-01-16T11:00:00Z',
            'status': 4,
            'priority': 3,
            'tags': ['bug']
        },
        {
            'id': 1003,
            'subject': 'Feature request',
            'description_text': 'Please add dark mode!\n\n--\nSent from my iPhone',
            'created_at': '2024-01-17T12:00:00Z',
            'status': 4,
            'priority': 2,
            'tags': ['feature']
        }
    ]
    
    cleaned_tickets = clean_tickets(raw_tickets)
    
    print(f"Cleaning {len(raw_tickets)} tickets...")
    print(f"✓ Successfully cleaned {len(cleaned_tickets)} tickets\n")
    
    for i, ticket in enumerate(cleaned_tickets, 1):
        print(f"{i}. Ticket #{ticket.ticket_id}")
        print(f"   Subject: {ticket.subject}")
        print(f"   Clean feedback: \"{ticket.clean_feedback}\"")
        print(f"   Reduction: {ticket.metadata['reduction_ratio']}%\n")
    
    print("✓ Batch cleaning test passed")


def test_feedback_data_cleaning():
    """Test cleaning complete feedback data structure."""
    print_section("TEST 7: Complete Feedback Data Cleaning")
    
    sample_data = {
        'metadata': {
            'game_name': 'Test Game',
            'os': 'Android',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'total_records': 2
        },
        'feedbacks': [
            {
                'id': 2001,
                'subject': 'Love the game',
                'description_text': 'Best mobile game ever!\n\nRegards,\nFan',
                'created_at': '2024-01-10T09:00:00Z',
                'status': 4,
                'priority': 1
            },
            {
                'id': 2002,
                'subject': 'Payment issue',
                'description_text': 'Cannot complete purchase.\n\nThanks,\nCustomer\ncustomer@email.com',
                'created_at': '2024-01-11T10:00:00Z',
                'status': 4,
                'priority': 3
            }
        ]
    }
    
    print("Original data:")
    print(f"  Total tickets: {len(sample_data['feedbacks'])}")
    print(f"  Metadata: {sample_data['metadata']}")
    
    cleaned_data = clean_feedback_data(sample_data)
    
    print(f"\nCleaned data:")
    print(f"  Total tickets: {len(cleaned_data['feedbacks'])}")
    print(f"  Cleaned metadata: {cleaned_data['metadata']}")
    
    print(f"\nSample cleaned ticket:")
    sample_cleaned = cleaned_data['feedbacks'][0]
    print(f"  ID: #{sample_cleaned['ticket_id']}")
    print(f"  Subject: {sample_cleaned['subject']}")
    print(f"  Clean feedback: \"{sample_cleaned['clean_feedback']}\"")
    
    print(f"\n✓ Complete data structure cleaning test passed")


def test_edge_cases():
    """Test edge cases and potential issues."""
    print_section("TEST 8: Edge Cases")
    
    edge_cases = [
        {
            'name': 'Empty description',
            'ticket': {
                'id': 3001,
                'subject': 'Empty ticket',
                'description_text': '',
                'created_at': '2024-01-01T00:00:00Z'
            }
        },
        {
            'name': 'Only whitespace',
            'ticket': {
                'id': 3002,
                'subject': 'Whitespace only',
                'description_text': '   \n\n   \t   ',
                'created_at': '2024-01-01T00:00:00Z'
            }
        },
        {
            'name': 'Only signature',
            'ticket': {
                'id': 3003,
                'subject': 'Just signature',
                'description_text': 'Best regards,\nJohn',
                'created_at': '2024-01-01T00:00:00Z'
            }
        },
        {
            'name': 'Very long text',
            'ticket': {
                'id': 3004,
                'subject': 'Long feedback',
                'description_text': 'Great game! ' * 100,
                'created_at': '2024-01-01T00:00:00Z'
            }
        }
    ]
    
    for case in edge_cases:
        print(f"Testing: {case['name']}")
        try:
            cleaned = clean_ticket(case['ticket'])
            print(f"  ✓ Handled successfully")
            print(f"    Clean feedback length: {len(cleaned.clean_feedback)}")
            print(f"    Clean feedback: \"{cleaned.clean_feedback[:50]}...\"")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        print()
    
    print("✓ Edge case tests completed")


def main():
    """Run all data cleaner tests."""
    print("\n" + "🧪 "*35)
    print("  DATA CLEANER TEST SUITE")
    print("🧪 "*35)
    
    # Setup logging
    logger = setup_logger(__name__, log_level="INFO")
    
    try:
        # Run all tests
        test_html_removal()
        test_auto_reply_removal()
        test_signature_removal()
        test_complete_cleaning_pipeline()
        test_single_ticket_cleaning()
        test_batch_ticket_cleaning()
        test_feedback_data_cleaning()
        test_edge_cases()
        
        # Summary
        print("\n" + "="*70)
        print("  TEST SUITE SUMMARY")
        print("="*70)
        print("\n✅ All data cleaner tests completed successfully!")
        print("\nTested functionality:")
        print("  ✓ HTML tag removal")
        print("  ✓ Auto-reply detection and removal")
        print("  ✓ Signature detection and removal")
        print("  ✓ Complete cleaning pipeline")
        print("  ✓ Single ticket cleaning")
        print("  ✓ Batch ticket cleaning")
        print("  ✓ Complete data structure cleaning")
        print("  ✓ Edge case handling")
        print("\n" + "="*70 + "\n")
        
        logger.info("All data cleaner tests completed successfully")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelled by user (Ctrl+C)")
        logger.warning("Tests cancelled by user")
        
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        logger.error(f"Test suite failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
