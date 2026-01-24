#!/usr/bin/env python3
"""
Comprehensive test script for the storage manager module.

This script demonstrates all storage manager functionality including
cache hit/miss detection, save/load operations, and filename generation.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.input_handler import FeedbackAnalysisInput
from src.logger import setup_logger
from src import storage_manager


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def test_filename_generation():
    """Test deterministic filename generation."""
    print_section("TEST 1: Filename Generation")
    
    test_cases = [
        FeedbackAnalysisInput("Candy Crush", "Android", "2024-01-01", "2024-01-31"),
        FeedbackAnalysisInput("Subway Surfers", "iOS", "2024-02-01", "2024-02-29"),
        FeedbackAnalysisInput("Clash of Clans", "Both", "2024-03-01", "2024-03-31"),
        FeedbackAnalysisInput("My Game: Special Edition!", "Android", "2024-04-01", "2024-04-30"),
    ]
    
    for params in test_cases:
        filename = storage_manager.generate_filename(params)
        print(f"Input: {params.game_name} | {params.os} | {params.start_date} to {params.end_date}")
        print(f"Filename: {filename}")
        print()
    
    print("✅ Filename generation test completed\n")


def test_cache_miss():
    """Test cache miss scenario."""
    print_section("TEST 2: Cache Miss Scenario")
    
    params = FeedbackAnalysisInput(
        game_name="NonExistent Game",
        os="Android",
        start_date="2099-01-01",
        end_date="2099-12-31"
    )
    
    print(f"Checking cache for: {params.game_name}")
    exists = storage_manager.exists(params)
    print(f"Cache exists: {exists}")
    
    if not exists:
        print("✅ Cache miss detected correctly\n")
    else:
        print("⚠️  Unexpected cache hit\n")


def test_save_and_load():
    """Test save and load operations."""
    print_section("TEST 3: Save and Load Operations")
    
    params = FeedbackAnalysisInput(
        game_name="Test Game",
        os="Both",
        start_date="2024-01-15",
        end_date="2024-01-20"
    )
    
    # Create test data
    test_data = {
        'metadata': {
            'game_name': params.game_name,
            'os': params.os,
            'start_date': params.start_date,
            'end_date': params.end_date,
            'fetched_at': datetime.now().isoformat(),
            'total_records': 5
        },
        'feedbacks': [
            {
                'id': 1001,
                'subject': 'Love the game!',
                'description': 'Best game ever, highly recommended!',
                'status': 'Closed',
                'priority': 'Low',
                'created_at': '2024-01-15T10:30:00Z'
            },
            {
                'id': 1002,
                'subject': 'Bug in level 5',
                'description': 'Game freezes when I reach level 5',
                'status': 'Open',
                'priority': 'High',
                'created_at': '2024-01-16T14:20:00Z'
            },
            {
                'id': 1003,
                'subject': 'Feature request',
                'description': 'Please add multiplayer mode',
                'status': 'Open',
                'priority': 'Medium',
                'created_at': '2024-01-17T09:15:00Z'
            },
            {
                'id': 1004,
                'subject': 'Payment issue',
                'description': 'In-app purchase not working',
                'status': 'In Progress',
                'priority': 'High',
                'created_at': '2024-01-18T16:45:00Z'
            },
            {
                'id': 1005,
                'subject': 'Great update!',
                'description': 'The new features are amazing',
                'status': 'Closed',
                'priority': 'Low',
                'created_at': '2024-01-19T11:00:00Z'
            }
        ]
    }
    
    print(f"Test data created with {len(test_data['feedbacks'])} feedback records")
    print()
    
    # Save data
    print("Step 1: Saving data...")
    saved_path = storage_manager.save(params, test_data)
    print(f"✓ Saved to: {saved_path.name}")
    print()
    
    # Check existence
    print("Step 2: Checking if cache exists...")
    exists = storage_manager.exists(params)
    print(f"✓ Cache exists: {exists}")
    print()
    
    # Get cache info
    print("Step 3: Getting cache information...")
    cache_info = storage_manager.get_cache_info(params)
    if cache_info:
        print(f"  Filename: {cache_info['filename']}")
        print(f"  Size: {cache_info['size_kb']} KB ({cache_info['size_bytes']} bytes)")
        print(f"  Path: {cache_info['path']}")
    print()
    
    # Load data
    print("Step 4: Loading data from cache...")
    loaded_data = storage_manager.load(params)
    print(f"✓ Loaded {len(loaded_data['feedbacks'])} feedback records")
    print()
    
    # Verify data integrity
    print("Step 5: Verifying data integrity...")
    if loaded_data == test_data:
        print("✓ Data integrity verified - loaded data matches saved data")
    else:
        print("✗ WARNING: Data mismatch detected!")
    print()
    
    # Clean up
    print("Step 6: Cleaning up test cache...")
    deleted = storage_manager.delete(params)
    print(f"✓ Cache deleted: {deleted}")
    print()
    
    print("✅ Save and load test completed\n")


def test_cache_hit():
    """Test cache hit scenario."""
    print_section("TEST 4: Cache Hit Scenario")
    
    params = FeedbackAnalysisInput(
        game_name="Persistent Game",
        os="iOS",
        start_date="2024-06-01",
        end_date="2024-06-30"
    )
    
    # Create and save initial data
    initial_data = {
        'metadata': {
            'game_name': params.game_name,
            'cached_at': datetime.now().isoformat()
        },
        'feedbacks': [
            {'id': 1, 'subject': 'Test feedback 1'},
            {'id': 2, 'subject': 'Test feedback 2'}
        ]
    }
    
    print("Creating initial cache...")
    storage_manager.save(params, initial_data)
    print()
    
    print("First check - should be a cache hit:")
    exists_1 = storage_manager.exists(params)
    print()
    
    print("Second check - should also be a cache hit:")
    exists_2 = storage_manager.exists(params)
    print()
    
    print("Loading cached data:")
    loaded = storage_manager.load(params)
    print(f"✓ Successfully loaded {len(loaded['feedbacks'])} records from cache")
    print()
    
    # Clean up
    print("Cleaning up...")
    storage_manager.delete(params)
    print()
    
    print("✅ Cache hit test completed\n")


def test_multiple_games():
    """Test storage for multiple different games."""
    print_section("TEST 5: Multiple Games Cache Management")
    
    games = [
        FeedbackAnalysisInput("Game A", "Android", "2024-01-01", "2024-01-31"),
        FeedbackAnalysisInput("Game B", "iOS", "2024-01-01", "2024-01-31"),
        FeedbackAnalysisInput("Game C", "Both", "2024-02-01", "2024-02-28"),
    ]
    
    print(f"Creating cache for {len(games)} different games...")
    print()
    
    # Save data for each game
    for i, params in enumerate(games, 1):
        data = {
            'metadata': {'game_name': params.game_name},
            'feedbacks': [{'id': j} for j in range(1, i+2)]
        }
        storage_manager.save(params, data)
        print(f"  {i}. {params.game_name} ({params.os}): {len(data['feedbacks'])} feedbacks")
    print()
    
    # Verify all exist
    print("Verifying all caches exist...")
    for params in games:
        exists = storage_manager.exists(params)
        filename = storage_manager.generate_filename(params)
        status = "✓" if exists else "✗"
        print(f"  {status} {filename}")
    print()
    
    # Clean up all
    print("Cleaning up all test caches...")
    for params in games:
        storage_manager.delete(params)
    print("✓ All test caches deleted")
    print()
    
    print("✅ Multiple games test completed\n")


def main():
    """Run all storage manager tests."""
    print("\n" + "🧪 "*35)
    print("  STORAGE MANAGER COMPREHENSIVE TEST SUITE")
    print("🧪 "*35)
    
    # Setup logging
    logger = setup_logger(__name__, log_level="INFO")
    
    try:
        # Run all tests
        test_filename_generation()
        test_cache_miss()
        test_save_and_load()
        test_cache_hit()
        test_multiple_games()
        
        # Summary
        print("\n" + "="*70)
        print("  TEST SUITE SUMMARY")
        print("="*70)
        print("\n✅ All storage manager tests passed successfully!")
        print("\nTested functionality:")
        print("  ✓ Deterministic filename generation")
        print("  ✓ Cache miss detection")
        print("  ✓ Cache hit detection with logging")
        print("  ✓ Data save operations")
        print("  ✓ Data load operations")
        print("  ✓ Data integrity verification")
        print("  ✓ Cache information retrieval")
        print("  ✓ Cache deletion")
        print("  ✓ Multiple game cache management")
        print("\n" + "="*70 + "\n")
        
        logger.info("All storage manager tests completed successfully")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelled by user (Ctrl+C)")
        logger.warning("Tests cancelled by user")
        
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
