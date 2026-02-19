#!/usr/bin/env python3
"""
Show exact filtering process step-by-step
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent))

from src.freshdesk_client import FreshdeskClient
from src.input_handler import FeedbackAnalysisInput
import json

print("\n" + "="*80)
print("  STEP-BY-STEP FILTERING DEMONSTRATION")
print("="*80 + "\n")

# Sample parameters
params = FeedbackAnalysisInput(
    game_name="Word Trip",
    os="Android",
    start_date="2026-01-20",  # Using recent dates
    end_date="2026-02-19"
)

print("📋 INPUT PARAMETERS:")
print("-" * 80)
print(f"  Game Name: {params.game_name}")
print(f"  OS: {params.os}")
print(f"  Start Date: {params.start_date}")
print(f"  End Date: {params.end_date}")
print()

# Initialize client
try:
    client = FreshdeskClient()
    
    # STEP 1: Show the exact API call
    print("\n" + "="*80)
    print("  STEP 1: FRESHDESK API CALL")
    print("="*80 + "\n")
    
    endpoint = "tickets?per_page=100&page=1&order_by=updated_at&order_type=desc"
    full_url = f"https://{client.domain}/api/v2/{endpoint}"
    
    print("📡 EXACT API CALL:")
    print("-" * 80)
    print(f"Method: GET")
    print(f"URL: {full_url}")
    print(f"Auth: Basic <API_KEY>:X")
    print(f"No query filtering - pulls ALL tickets")
    print()
    
    # Make the call
    print("⏳ Fetching first 100 tickets...")
    response = client._make_request(endpoint)
    tickets = response.json()
    
    print(f"✅ Retrieved {len(tickets)} tickets from Freshdesk\n")
    
    # STEP 2: Show what we got
    print("="*80)
    print("  STEP 2: RAW DATA RECEIVED")
    print("="*80 + "\n")
    
    print(f"Sample of first 3 tickets:")
    print("-" * 80)
    for i, ticket in enumerate(tickets[:3], 1):
        print(f"\nTicket {i}:")
        print(f"  ID: {ticket.get('id')}")
        print(f"  Subject: {ticket.get('subject', 'N/A')[:50]}...")
        print(f"  Status: {ticket.get('status')} (5=Closed)")
        print(f"  Updated: {ticket.get('updated_at', 'N/A')[:10]}")
        cf = ticket.get('custom_fields', {})
        print(f"  Game: {cf.get('game', 'N/A')}")
        print(f"  OS: {cf.get('os', 'N/A')}")
        print(f"  Type: {ticket.get('type', 'N/A')}")
    
    # STEP 3: Apply filters one by one
    print("\n" + "="*80)
    print("  STEP 3: APPLYING FILTERS ONE BY ONE")
    print("="*80 + "\n")
    
    # Start with all tickets
    remaining_tickets = list(tickets)
    
    print(f"Starting with: {len(remaining_tickets)} tickets")
    print()
    
    # Filter 1: Status
    print("FILTER 1: Status = 5 (Closed)")
    print("-" * 80)
    
    status_5_tickets = []
    for ticket in remaining_tickets:
        if ticket.get('status') == 5:
            status_5_tickets.append(ticket)
    
    rejected_status = len(remaining_tickets) - len(status_5_tickets)
    print(f"  Before: {len(remaining_tickets)} tickets")
    print(f"  After:  {len(status_5_tickets)} tickets")
    print(f"  Rejected: {rejected_status} tickets (status != 5)")
    
    # Show status breakdown
    status_counts = {}
    for t in remaining_tickets:
        s = t.get('status')
        status_counts[s] = status_counts.get(s, 0) + 1
    
    print(f"\n  Status Breakdown:")
    status_names = {2: "Open", 3: "Pending", 4: "Resolved", 5: "Closed", 6: "Waiting"}
    for status, count in sorted(status_counts.items()):
        indicator = "✅" if status == 5 else "❌"
        print(f"    {indicator} Status {status} ({status_names.get(status, 'Unknown')}): {count} tickets")
    
    remaining_tickets = status_5_tickets
    print()
    
    # Filter 2: Date Range
    print("\nFILTER 2: Date Range (updated_at)")
    print("-" * 80)
    print(f"  Looking for: {params.start_date} to {params.end_date}")
    
    date_filtered_tickets = []
    start_date = datetime.strptime(params.start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(params.end_date, '%Y-%m-%d').date()
    
    for ticket in remaining_tickets:
        updated_at = ticket.get('updated_at')
        if updated_at:
            try:
                ticket_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00')).date()
                if start_date <= ticket_date <= end_date:
                    date_filtered_tickets.append(ticket)
            except:
                pass
    
    rejected_date = len(remaining_tickets) - len(date_filtered_tickets)
    print(f"  Before: {len(remaining_tickets)} tickets")
    print(f"  After:  {len(date_filtered_tickets)} tickets")
    print(f"  Rejected: {rejected_date} tickets (date out of range)")
    
    # Show date distribution
    if remaining_tickets:
        dates = []
        for t in remaining_tickets[:10]:
            ua = t.get('updated_at', '')[:10]
            if ua:
                dates.append(ua)
        print(f"\n  Sample updated_at dates from first 10 tickets:")
        for date in dates[:5]:
            in_range = "✅" if start_date <= datetime.strptime(date, '%Y-%m-%d').date() <= end_date else "❌"
            print(f"    {in_range} {date}")
    
    remaining_tickets = date_filtered_tickets
    print()
    
    # Filter 3: Game Name
    print("\nFILTER 3: Game Name")
    print("-" * 80)
    print(f"  Looking for: 'word trip' (case-insensitive)")
    
    game_filtered_tickets = []
    game_name_lower = params.game_name.lower()
    
    for ticket in remaining_tickets:
        custom_fields = ticket.get('custom_fields', {})
        game_field = str(custom_fields.get('game', '')).lower()
        
        if game_name_lower in game_field:
            game_filtered_tickets.append(ticket)
    
    rejected_game = len(remaining_tickets) - len(game_filtered_tickets)
    print(f"  Before: {len(remaining_tickets)} tickets")
    print(f"  After:  {len(game_filtered_tickets)} tickets")
    print(f"  Rejected: {rejected_game} tickets (game mismatch)")
    
    # Show game distribution
    if remaining_tickets:
        game_counts = {}
        for t in remaining_tickets:
            cf = t.get('custom_fields', {})
            g = cf.get('game', 'No game')
            game_counts[g] = game_counts.get(g, 0) + 1
        
        print(f"\n  Game Distribution in filtered tickets:")
        for game, count in sorted(game_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            match = "✅" if 'word trip' in game.lower() else "❌"
            print(f"    {match} {game}: {count} tickets")
    
    # Final result
    print("\n" + "="*80)
    print("  FINAL RESULT AFTER ALL FILTERS")
    print("="*80 + "\n")
    
    print(f"✅ Tickets Matching ALL Criteria: {len(game_filtered_tickets)}")
    print(f"\nThese tickets will be:")
    print(f"  • Saved to data/raw/")
    print(f"  • Cleaned (remove noise)")
    print(f"  • Filtered for OS='{params.os}' and Type='Feedback'")
    print(f"  • Sent to ChatGPT for analysis")
    
    if game_filtered_tickets:
        print(f"\n📝 Sample Matching Ticket:")
        print("-" * 80)
        sample = game_filtered_tickets[0]
        print(f"  ID: {sample.get('id')}")
        print(f"  Subject: {sample.get('subject')}")
        print(f"  Status: {sample.get('status')}")
        print(f"  Updated: {sample.get('updated_at')}")
        print(f"  Game: {sample.get('custom_fields', {}).get('game')}")
        print(f"  OS: {sample.get('custom_fields', {}).get('os')}")
        print(f"  Type: {sample.get('type')}")
    
    # Summary
    print("\n" + "="*80)
    print("  FILTERING SUMMARY")
    print("="*80 + "\n")
    
    print(f"Starting with: 100 tickets (from Freshdesk API)")
    print(f"After Status=5 filter: {len(status_5_tickets)} tickets ({rejected_status} rejected)")
    print(f"After Date filter: {len(date_filtered_tickets)} tickets ({rejected_date} rejected)")
    print(f"After Game filter: {len(game_filtered_tickets)} tickets ({rejected_game} rejected)")
    print(f"\n✅ Final: {len(game_filtered_tickets)} tickets ready for analysis")
    
    print("\n" + "="*80 + "\n")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
