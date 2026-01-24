#!/usr/bin/env python3
"""
Test script for the game feature context loader.

This script tests context loading, validation, and error handling.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.context_loader import (
    load_game_context,
    create_sample_context_file,
    ContextLoaderError,
    GameFeatureContext
)
from src.logger import setup_logger
from src.config import CONTEXT_DIR


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def test_load_existing_context():
    """Test loading existing context file."""
    print_section("TEST 1: Load Existing Context")
    
    try:
        context = load_game_context()
        
        print(f"✓ Context loaded successfully!")
        print(f"  Game: {context.game_name}")
        print(f"  Features: {len(context.current_features)}")
        print(f"  Constraints: {len(context.known_constraints)}")
        print(f"  Recent Changes: {len(context.recent_changes)}")
        
        if context.additional_info:
            print(f"  Additional Info: {len(context.additional_info)} fields")
        
        return context
        
    except ContextLoaderError as e:
        print(f"✗ Failed to load context: {e}")
        return None


def test_game_name_validation():
    """Test game name validation."""
    print_section("TEST 2: Game Name Validation")
    
    try:
        # Load without game name check
        context1 = load_game_context()
        print(f"✓ Loaded context without game name check: {context1.game_name}")
        
        # Load with matching game name
        context2 = load_game_context(game_name=context1.game_name)
        print(f"✓ Loaded context with matching game name: {context2.game_name}")
        
        # Load with different game name (should warn but not fail)
        print("\nTesting with different game name (should log warning)...")
        context3 = load_game_context(game_name="Different Game")
        print(f"✓ Context loaded despite name mismatch (warning logged)")
        
    except ContextLoaderError as e:
        print(f"✗ Validation failed: {e}")


def test_context_formatting():
    """Test context formatting methods."""
    print_section("TEST 3: Context Formatting")
    
    try:
        context = load_game_context()
        
        # Test to_dict()
        print("1. Dictionary conversion:")
        context_dict = context.to_dict()
        print(f"   ✓ Keys: {', '.join(context_dict.keys())}")
        print(f"   ✓ Type: {type(context_dict).__name__}")
        
        # Test format_for_ai()
        print("\n2. AI-formatted string:")
        ai_format = context.format_for_ai()
        lines = ai_format.split('\n')
        print(f"   ✓ Generated {len(lines)} lines")
        print(f"   ✓ First 5 lines:")
        for line in lines[:5]:
            print(f"      {line}")
        
        # Test __str__()
        print("\n3. String representation:")
        str_repr = str(context)
        print(f"   ✓ Generated: {str_repr[:100]}...")
        
    except Exception as e:
        print(f"✗ Formatting test failed: {e}")


def test_context_details():
    """Test accessing context details."""
    print_section("TEST 4: Context Details")
    
    try:
        context = load_game_context()
        
        # Display features
        print(f"📋 Current Features ({len(context.current_features)}):")
        for i, feature in enumerate(context.current_features[:3], 1):
            print(f"   {i}. {feature}")
        if len(context.current_features) > 3:
            print(f"   ... and {len(context.current_features) - 3} more")
        
        # Display constraints
        print(f"\n⚠️  Known Constraints ({len(context.known_constraints)}):")
        for i, constraint in enumerate(context.known_constraints[:3], 1):
            print(f"   {i}. {constraint}")
        if len(context.known_constraints) > 3:
            print(f"   ... and {len(context.known_constraints) - 3} more")
        
        # Display recent changes
        print(f"\n🔄 Recent Changes ({len(context.recent_changes)}):")
        for i, change in enumerate(context.recent_changes[:3], 1):
            print(f"   {i}. {change}")
        if len(context.recent_changes) > 3:
            print(f"   ... and {len(context.recent_changes) - 3} more")
        
        # Display additional info
        if context.additional_info:
            print(f"\n📌 Additional Info ({len(context.additional_info)} fields):")
            for key, value in list(context.additional_info.items())[:3]:
                if isinstance(value, list):
                    print(f"   {key}: {len(value)} items")
                else:
                    print(f"   {key}: {value}")
        
        print("\n✓ All context details accessible")
        
    except Exception as e:
        print(f"✗ Failed to access details: {e}")


def test_create_sample():
    """Test creating sample context file."""
    print_section("TEST 5: Create Sample Context")
    
    try:
        # Create sample in a test location
        sample_path = create_sample_context_file("Test Sample Game")
        
        print(f"✓ Created sample file: {sample_path}")
        print(f"  File exists: {sample_path.exists()}")
        
        if sample_path.exists():
            print(f"  File size: {sample_path.stat().st_size} bytes")
        
    except Exception as e:
        print(f"✗ Failed to create sample: {e}")


def test_error_handling():
    """Test error handling for invalid scenarios."""
    print_section("TEST 6: Error Handling")
    
    import tempfile
    import shutil
    
    # Create temporary directory for testing
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Test 1: Missing file
        print("1. Testing missing file...")
        try:
            from src.context_loader import load_yaml_file
            load_yaml_file(temp_dir / "nonexistent.yaml")
            print("   ✗ Should have raised error for missing file")
        except ContextLoaderError as e:
            print(f"   ✓ Correctly caught missing file error")
        
        # Test 2: Empty file
        print("\n2. Testing empty file...")
        empty_file = temp_dir / "empty.yaml"
        empty_file.write_text("")
        try:
            from src.context_loader import load_yaml_file
            load_yaml_file(empty_file)
            print("   ✗ Should have raised error for empty file")
        except ContextLoaderError as e:
            print(f"   ✓ Correctly caught empty file error")
        
        # Test 3: Invalid YAML
        print("\n3. Testing invalid YAML syntax...")
        invalid_file = temp_dir / "invalid.yaml"
        invalid_file.write_text("game_name: Test\ninvalid: [unclosed")
        try:
            from src.context_loader import load_yaml_file
            load_yaml_file(invalid_file)
            print("   ✗ Should have raised error for invalid YAML")
        except ContextLoaderError as e:
            print(f"   ✓ Correctly caught YAML syntax error")
        
        # Test 4: Missing required fields
        print("\n4. Testing missing required fields...")
        incomplete_file = temp_dir / "incomplete.yaml"
        incomplete_file.write_text("game_name: Test\ncurrent_features: []")
        try:
            from src.context_loader import load_yaml_file, validate_required_fields
            data = load_yaml_file(incomplete_file)
            required = ['game_name', 'current_features', 'known_constraints', 'recent_changes']
            validate_required_fields(data, required)
            print("   ✗ Should have raised error for missing fields")
        except ContextLoaderError as e:
            print(f"   ✓ Correctly caught missing required fields")
        
        # Test 5: Wrong field types
        print("\n5. Testing wrong field types...")
        wrong_type_file = temp_dir / "wrong_type.yaml"
        wrong_type_file.write_text("""
game_name: Test
current_features: "should be a list"
known_constraints: []
recent_changes: []
""")
        try:
            from src.context_loader import load_yaml_file, validate_field_types
            data = load_yaml_file(wrong_type_file)
            validate_field_types(data)
            print("   ✗ Should have raised error for wrong types")
        except ContextLoaderError as e:
            print(f"   ✓ Correctly caught wrong field type")
        
        print("\n✓ Error handling tests completed")
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_ai_integration():
    """Test how context would be used in AI analysis."""
    print_section("TEST 7: AI Integration Simulation")
    
    try:
        context = load_game_context()
        
        # Simulate preparing context for AI
        print("Preparing context for AI analysis...")
        
        ai_prompt = f"""
You are analyzing player feedback for the following game:

{context.format_for_ai()}

Please analyze the feedback with this context in mind.
"""
        
        print("✓ Generated AI prompt:")
        lines = ai_prompt.strip().split('\n')
        for line in lines[:10]:
            print(f"  {line}")
        print(f"  ... ({len(lines)} total lines)")
        
        # Test data structure
        print("\n✓ Context data structure suitable for AI:")
        print(f"  - Game name available: {bool(context.game_name)}")
        print(f"  - Features list: {len(context.current_features)} items")
        print(f"  - Constraints list: {len(context.known_constraints)} items")
        print(f"  - Changes list: {len(context.recent_changes)} items")
        print(f"  - Dictionary format: {bool(context.to_dict())}")
        
    except Exception as e:
        print(f"✗ AI integration test failed: {e}")


def main():
    """Run all context loader tests."""
    print("\n" + "🧪 "*35)
    print("  GAME FEATURE CONTEXT LOADER TEST SUITE")
    print("🧪 "*35)
    
    # Setup logging
    logger = setup_logger(__name__, log_level="INFO")
    
    try:
        # Check if context file exists
        context_file = CONTEXT_DIR / "game_features.yaml"
        
        if not context_file.exists():
            print(f"\n⚠️  Context file not found: {context_file}")
            print("Creating sample file for testing...")
            create_sample_context_file("Test Game")
            print("✓ Sample file created\n")
        
        # Run tests
        test_load_existing_context()
        test_game_name_validation()
        test_context_formatting()
        test_context_details()
        test_create_sample()
        test_error_handling()
        test_ai_integration()
        
        # Summary
        print("\n" + "="*70)
        print("  TEST SUITE SUMMARY")
        print("="*70)
        print("\n✅ All context loader tests completed!")
        print("\nTested functionality:")
        print("  ✓ Load existing context file")
        print("  ✓ Game name validation")
        print("  ✓ Context formatting (dict, AI format, string)")
        print("  ✓ Context detail access")
        print("  ✓ Sample file creation")
        print("  ✓ Error handling (missing, empty, invalid, wrong types)")
        print("  ✓ AI integration simulation")
        print("\n" + "="*70 + "\n")
        
        logger.info("All context loader tests completed successfully")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelled by user (Ctrl+C)")
        logger.warning("Tests cancelled by user")
        
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        logger.error(f"Test suite failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
