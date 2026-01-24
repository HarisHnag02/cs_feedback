#!/usr/bin/env python3
"""
Quick test script to demonstrate the input handler functionality.

This script can be run to test the interactive CLI input collection
without needing the full application setup.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.input_handler import get_validated_inputs
from src.logger import setup_logger


def main():
    """Test the input handler."""
    print("\n" + "🧪 "*25)
    print("  TESTING INTERACTIVE INPUT HANDLER")
    print("🧪 "*25 + "\n")
    
    # Setup basic logging
    logger = setup_logger(__name__, log_level="INFO")
    
    try:
        # Collect inputs
        inputs = get_validated_inputs()
        
        # Display results
        print("\n" + "="*60)
        print("  TEST RESULTS")
        print("="*60)
        
        print("\n📦 Dataclass Object:")
        print(inputs)
        
        print("\n📦 As Dictionary:")
        import json
        print(json.dumps(inputs.to_dict(), indent=2))
        
        print("\n" + "="*60)
        print("✅ Input handler test completed successfully!")
        print("="*60 + "\n")
        
        logger.info("Test completed successfully")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user (Ctrl+C)")
        logger.warning("Test cancelled by user")
        
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
