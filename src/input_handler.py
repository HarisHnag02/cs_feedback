"""
Interactive CLI input handler for collecting game feedback analysis parameters.

This module provides functions to interactively collect user inputs for game name,
platform (OS), and date range, with comprehensive validation and user-friendly prompts.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .logger import get_logger


# Initialize logger for this module
logger = get_logger(__name__)


@dataclass
class FeedbackAnalysisInput:
    """
    Data class representing validated user input for feedback analysis.
    
    Attributes:
        game_name: Name of the game to analyze
        os: Operating system platform (Android, iOS, or Both)
        days_back: Number of days to look back from today
        start_date: Analysis start date (calculated from days_back)
        end_date: Analysis end date (today)
    """
    game_name: str
    os: str
    days_back: int
    start_date: str  # Calculated from days_back
    end_date: str    # Today's date
    
    def to_dict(self) -> dict:
        """Convert dataclass to dictionary."""
        return {
            'game_name': self.game_name,
            'os': self.os,
            'start_date': self.start_date,
            'end_date': self.end_date
        }
    
    def __str__(self) -> str:
        """String representation for display."""
        return (
            f"\n{'='*50}\n"
            f"  Game Name:   {self.game_name}\n"
            f"  Platform:    {self.os}\n"
            f"  Days Back:   {self.days_back} days\n"
            f"  Start Date:  {self.start_date}\n"
            f"  End Date:    {self.end_date}\n"
            f"{'='*50}"
        )


# Valid OS options
VALID_OS_OPTIONS = ['Android', 'iOS', 'Both']


def prompt_game_name() -> str:
    """
    Prompt user for game name with validation.
    
    Returns:
        str: Validated game name (non-empty, stripped of whitespace)
    """
    print("\n" + "="*50)
    print("  FRESHDESK FEEDBACK AI ANALYSIS")
    print("="*50 + "\n")
    
    while True:
        game_name = input("📱 Enter Game Name: ").strip()
        
        if not game_name:
            print("   ❌ Error: Game name cannot be empty. Please try again.\n")
            logger.warning("User entered empty game name")
            continue
        
        logger.info(f"Game name entered: {game_name}")
        return game_name


def prompt_os() -> str:
    """
    Prompt user for operating system with validation.
    
    Returns:
        str: Validated OS choice (Android, iOS, or Both)
    """
    print(f"\n💻 Select Operating System:")
    print(f"   Options: {', '.join(VALID_OS_OPTIONS)}")
    
    while True:
        os_input = input("   Enter OS: ").strip()
        
        if not os_input:
            print("   ❌ Error: OS cannot be empty. Please try again.\n")
            logger.warning("User entered empty OS")
            continue
        
        # Case-insensitive matching
        os_matched = None
        for valid_os in VALID_OS_OPTIONS:
            if os_input.lower() == valid_os.lower():
                os_matched = valid_os
                break
        
        if os_matched:
            logger.info(f"OS selected: {os_matched}")
            return os_matched
        else:
            print(f"   ❌ Error: Invalid OS. Must be one of: {', '.join(VALID_OS_OPTIONS)}")
            print(f"   Please try again.\n")
            logger.warning(f"Invalid OS entered: {os_input}")


def validate_date_format(date_string: str) -> Optional[datetime]:
    """
    Validate date string format (YYYY-MM-DD).
    
    Args:
        date_string: Date string to validate
        
    Returns:
        datetime object if valid, None if invalid
    """
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        return date_obj
    except ValueError:
        return None


def prompt_days_back() -> int:
    """
    Prompt user for number of days to look back.
    
    Returns:
        int: Number of days to look back (7, 14, 30, etc.)
    """
    print(f"\n📅 How many days back to analyze?")
    print(f"   Examples: 7 (last week), 14 (last 2 weeks), 30 (last month)")
    
    while True:
        days_input = input("   Enter number of days: ").strip()
        
        if not days_input:
            print("   ❌ Error: Please enter a number. Please try again.\n")
            logger.warning("User entered empty days")
            continue
        
        # Validate it's a number
        try:
            days = int(days_input)
            
            if days <= 0:
                print("   ❌ Error: Days must be a positive number.")
                print("   Please try again.\n")
                continue
            
            if days > 365:
                print("   ⚠️  Warning: {days} days is more than a year. Are you sure?")
                confirm = input("   Continue? (y/n): ").strip().lower()
                if confirm not in ['y', 'yes']:
                    continue
            
            logger.info(f"days_back entered: {days}")
            return days
            
        except ValueError:
            print("   ❌ Error: Please enter a valid number.")
            print("   Please try again.\n")
            logger.warning(f"Invalid days format: {days_input}")
            continue


def validate_date_range(start_date: str, end_date: str) -> bool:
    """
    Validate that start date is not after end date.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        
    Returns:
        bool: True if valid range, False otherwise
    """
    start_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_obj = datetime.strptime(end_date, "%Y-%m-%d")
    
    return start_obj <= end_obj


def collect_user_inputs() -> FeedbackAnalysisInput:
    """
    Collect all user inputs interactively with validation.
    
    This is the main function that orchestrates the entire input collection process.
    It prompts for game name, OS, and number of days back.
    
    Returns:
        FeedbackAnalysisInput: Validated user inputs as a dataclass
        
    Example:
        >>> inputs = collect_user_inputs()
        >>> print(inputs.game_name)
        'Word Trip'
    """
    from datetime import datetime, timedelta
    
    logger.info("Starting user input collection")
    
    # Step 1: Collect game name
    game_name = prompt_game_name()
    
    # Step 2: Collect OS
    os = prompt_os()
    
    # Step 3: Collect days back (simpler than start/end dates)
    days_back = prompt_days_back()
    
    # Calculate date range automatically
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)
    
    # Convert to string format
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    logger.info(f"Calculated date range: {start_date_str} to {end_date_str} ({days_back} days)")
    
    # Create and return the validated input object
    user_input = FeedbackAnalysisInput(
        game_name=game_name,
        os=os,
        days_back=days_back,
        start_date=start_date_str,
        end_date=end_date_str
    )
    
    logger.info("User input collection completed successfully")
    return user_input


def display_confirmation(user_input: FeedbackAnalysisInput) -> bool:
    """
    Display collected inputs and ask for user confirmation.
    
    Args:
        user_input: FeedbackAnalysisInput object to display
        
    Returns:
        bool: True if user confirms, False to re-enter
    """
    print("\n" + "="*50)
    print("  REVIEW YOUR INPUTS")
    print(user_input)
    
    while True:
        confirm = input("\n✅ Is this information correct? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y']:
            logger.info("User confirmed inputs")
            return True
        elif confirm in ['no', 'n']:
            logger.info("User rejected inputs, will re-collect")
            return False
        else:
            print("   Please enter 'yes' or 'no'")


def get_validated_inputs() -> FeedbackAnalysisInput:
    """
    Main entry point for collecting and validating user inputs with confirmation.
    
    This function collects inputs and asks for confirmation. If the user rejects,
    it will collect inputs again until confirmed.
    
    Returns:
        FeedbackAnalysisInput: Validated and confirmed user inputs
    """
    while True:
        user_input = collect_user_inputs()
        
        if display_confirmation(user_input):
            print("\n✨ Great! Proceeding with the analysis...\n")
            return user_input
        else:
            print("\n🔄 Let's start over...\n")


if __name__ == "__main__":
    # Test the input handler
    print("Testing Interactive Input Handler\n")
    
    try:
        inputs = get_validated_inputs()
        print("\n" + "="*50)
        print("  FINAL VALIDATED INPUTS")
        print("="*50)
        print(f"\nAs Dictionary:\n{inputs.to_dict()}")
        print(f"\nAs String:\n{inputs}")
        
    except KeyboardInterrupt:
        print("\n\n❌ Input collection cancelled by user.")
        logger.info("User cancelled input collection")
    except Exception as e:
        print(f"\n\n❌ An error occurred: {e}")
        logger.error(f"Error during input collection: {e}")
