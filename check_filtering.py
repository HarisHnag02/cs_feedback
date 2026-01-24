#!/usr/bin/env python3
"""Quick script to check what's being filtered and why."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.logger import setup_logger

# Enable DEBUG logging to see all rejection reasons
logger = setup_logger("test", log_level="DEBUG")

print("Run 'python main.py' again and check the logs.")
print("The system will now show you:")
print("  1. How many tickets were fetched from Freshdesk")
print("  2. How many were rejected by each filter")
print("  3. Why specific tickets were rejected")
print("\nLook for lines like:")
print("  'Rejection breakdown:'")
print("  '  Status (not Closed): X'")
print("  '  Type (not Feedback): X'")
print("  '  Game Name: X'")
print("etc.")
