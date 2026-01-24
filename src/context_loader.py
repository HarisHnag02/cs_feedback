"""
Context loader for game feature information.

This module loads and validates game-specific context from YAML files.
The context provides essential information about game features, constraints,
and recent changes to enhance AI analysis of feedback.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .config import CONTEXT_DIR
from .logger import get_logger


# Initialize logger for this module
logger = get_logger(__name__)


class ContextLoaderError(Exception):
    """Custom exception for context loading errors."""
    pass


@dataclass
class GameFeatureContext:
    """
    Structured game feature context data.
    
    This dataclass represents all context information about a game,
    including its features, constraints, and recent changes.
    
    Attributes:
        game_name: Name of the game
        current_features: List of current game features
        known_constraints: List of known technical/design constraints
        recent_changes: List of recent updates/changes
        additional_info: Optional additional context information
    """
    game_name: str
    current_features: List[str]
    known_constraints: List[str]
    recent_changes: List[str]
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary."""
        return {
            'game_name': self.game_name,
            'current_features': self.current_features,
            'known_constraints': self.known_constraints,
            'recent_changes': self.recent_changes,
            'additional_info': self.additional_info
        }
    
    def format_for_ai(self) -> str:
        """
        Format context as a structured string for AI analysis.
        
        Returns:
            Formatted string containing all context information
        """
        sections = [
            f"GAME: {self.game_name}",
            "",
            "CURRENT FEATURES:",
        ]
        
        for feature in self.current_features:
            sections.append(f"  • {feature}")
        
        sections.extend(["", "KNOWN CONSTRAINTS:"])
        for constraint in self.known_constraints:
            sections.append(f"  • {constraint}")
        
        sections.extend(["", "RECENT CHANGES:"])
        for change in self.recent_changes:
            sections.append(f"  • {change}")
        
        if self.additional_info:
            sections.extend(["", "ADDITIONAL CONTEXT:"])
            for key, value in self.additional_info.items():
                sections.append(f"  {key}: {value}")
        
        return "\n".join(sections)
    
    def __str__(self) -> str:
        """String representation for display."""
        return (
            f"\n{'='*60}\n"
            f"  GAME FEATURE CONTEXT: {self.game_name}\n"
            f"{'='*60}\n"
            f"\n📋 Features: {len(self.current_features)}"
            f"\n⚠️  Constraints: {len(self.known_constraints)}"
            f"\n🔄 Recent Changes: {len(self.recent_changes)}\n"
            f"{'='*60}"
        )


def load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """
    Load and parse a YAML file.
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        Parsed YAML data as dictionary
        
    Raises:
        ContextLoaderError: If file doesn't exist or YAML is invalid
    """
    if not file_path.exists():
        raise ContextLoaderError(
            f"Context file not found: {file_path}\n"
            f"Please create the file with required game context."
        )
    
    try:
        logger.debug(f"Loading YAML file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if data is None:
            raise ContextLoaderError(
                f"YAML file is empty: {file_path}\n"
                f"Please add game context information."
            )
        
        logger.debug(f"Successfully loaded YAML with {len(data)} top-level keys")
        return data
        
    except yaml.YAMLError as e:
        raise ContextLoaderError(
            f"Invalid YAML syntax in {file_path}:\n{e}\n"
            f"Please check the YAML file format."
        ) from e
    except Exception as e:
        raise ContextLoaderError(
            f"Error reading {file_path}: {e}"
        ) from e


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that all required fields are present in the data.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Raises:
        ContextLoaderError: If any required field is missing
    """
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise ContextLoaderError(
            f"Missing required fields in context file: {', '.join(missing_fields)}\n"
            f"Required fields: {', '.join(required_fields)}"
        )
    
    logger.debug(f"All required fields present: {', '.join(required_fields)}")


def validate_field_types(data: Dict[str, Any]) -> None:
    """
    Validate that fields have the correct types.
    
    Args:
        data: Dictionary to validate
        
    Raises:
        ContextLoaderError: If field types are incorrect
    """
    validations = {
        'game_name': (str, "must be a string"),
        'current_features': (list, "must be a list"),
        'known_constraints': (list, "must be a list"),
        'recent_changes': (list, "must be a list")
    }
    
    for field_name, (expected_type, error_msg) in validations.items():
        if field_name in data:
            value = data[field_name]
            
            if not isinstance(value, expected_type):
                raise ContextLoaderError(
                    f"Field '{field_name}' {error_msg}, got {type(value).__name__}"
                )
            
            # Additional validation for lists (must not be empty for critical fields)
            if expected_type == list and len(value) == 0:
                logger.warning(f"Field '{field_name}' is an empty list")
    
    logger.debug("Field type validation passed")


def validate_list_contents(data: Dict[str, Any]) -> None:
    """
    Validate that list fields contain only strings.
    
    Args:
        data: Dictionary to validate
        
    Raises:
        ContextLoaderError: If list contents are invalid
    """
    list_fields = ['current_features', 'known_constraints', 'recent_changes']
    
    for field_name in list_fields:
        if field_name in data:
            items = data[field_name]
            
            for i, item in enumerate(items):
                if not isinstance(item, str):
                    raise ContextLoaderError(
                        f"Field '{field_name}' must contain only strings. "
                        f"Item at index {i} is {type(item).__name__}"
                    )
                
                if not item.strip():
                    raise ContextLoaderError(
                        f"Field '{field_name}' contains empty string at index {i}"
                    )
    
    logger.debug("List contents validation passed")


def load_game_context(game_name: Optional[str] = None) -> GameFeatureContext:
    """
    Load game feature context from YAML file.
    
    Loads context from context/game_features.yaml and validates all required
    fields. If game_name is provided, validates it matches the context.
    
    Args:
        game_name: Optional game name to validate against context
        
    Returns:
        GameFeatureContext object with validated data
        
    Raises:
        ContextLoaderError: If file is missing, invalid, or validation fails
        
    Example:
        >>> context = load_game_context("Candy Crush")
        >>> print(f"Features: {len(context.current_features)}")
        >>> print(context.format_for_ai())
    """
    logger.info("Loading game feature context...")
    
    # Define file path
    context_file = CONTEXT_DIR / "game_features.yaml"
    logger.info(f"Context file path: {context_file}")
    
    # Load YAML file
    data = load_yaml_file(context_file)
    
    # Define required fields
    required_fields = [
        'game_name',
        'current_features',
        'known_constraints',
        'recent_changes'
    ]
    
    # Validate required fields exist
    validate_required_fields(data, required_fields)
    
    # Validate field types
    validate_field_types(data)
    
    # Validate list contents
    validate_list_contents(data)
    
    # Validate game name if provided
    context_game_name = data['game_name'].strip()
    
    if game_name:
        if context_game_name.lower() != game_name.lower():
            logger.warning(
                f"Game name mismatch: Context has '{context_game_name}', "
                f"requested '{game_name}'"
            )
            # Note: We log a warning but don't raise an error
            # This allows using the same context for similar game names
    
    # Extract additional info (any fields beyond required ones)
    additional_info = {
        key: value for key, value in data.items()
        if key not in required_fields
    }
    
    # Create context object
    context = GameFeatureContext(
        game_name=context_game_name,
        current_features=data['current_features'],
        known_constraints=data['known_constraints'],
        recent_changes=data['recent_changes'],
        additional_info=additional_info
    )
    
    logger.info(f"✓ Successfully loaded context for '{context.game_name}'")
    logger.info(f"  Features: {len(context.current_features)}")
    logger.info(f"  Constraints: {len(context.known_constraints)}")
    logger.info(f"  Recent Changes: {len(context.recent_changes)}")
    
    return context


def create_sample_context_file(game_name: str = "Sample Game") -> Path:
    """
    Create a sample context file with template structure.
    
    This is a utility function to help users get started with context files.
    
    Args:
        game_name: Name of the game for the sample
        
    Returns:
        Path to created sample file
    """
    sample_data = {
        'game_name': game_name,
        'current_features': [
            'Feature 1: Description',
            'Feature 2: Description',
            'Feature 3: Description'
        ],
        'known_constraints': [
            'Constraint 1: Technical limitation',
            'Constraint 2: Design choice'
        ],
        'recent_changes': [
            'Change 1: Recent update description',
            'Change 2: New feature added'
        ],
        'target_audience': 'Casual mobile gamers',
        'platform': 'iOS and Android'
    }
    
    # Ensure context directory exists
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    
    sample_file = CONTEXT_DIR / "game_features.yaml"
    
    with open(sample_file, 'w', encoding='utf-8') as f:
        yaml.dump(sample_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Created sample context file: {sample_file}")
    return sample_file


if __name__ == "__main__":
    # Test the context loader
    print("\n" + "="*70)
    print("  TESTING GAME FEATURE CONTEXT LOADER")
    print("="*70 + "\n")
    
    try:
        # Check if context file exists
        context_file = CONTEXT_DIR / "game_features.yaml"
        
        if not context_file.exists():
            print("📝 Context file not found. Creating sample...")
            sample_file = create_sample_context_file("Test Game")
            print(f"✓ Created sample file: {sample_file}\n")
        
        # Load context
        print("1. Loading game context...")
        context = load_game_context()
        
        print(f"✓ Context loaded successfully!")
        print(context)
        
        # Display details
        print("\n2. Context Details:")
        print(f"\n📋 Current Features ({len(context.current_features)}):")
        for i, feature in enumerate(context.current_features, 1):
            print(f"   {i}. {feature}")
        
        print(f"\n⚠️  Known Constraints ({len(context.known_constraints)}):")
        for i, constraint in enumerate(context.known_constraints, 1):
            print(f"   {i}. {constraint}")
        
        print(f"\n🔄 Recent Changes ({len(context.recent_changes)}):")
        for i, change in enumerate(context.recent_changes, 1):
            print(f"   {i}. {change}")
        
        if context.additional_info:
            print(f"\n📌 Additional Info:")
            for key, value in context.additional_info.items():
                print(f"   {key}: {value}")
        
        # Test AI formatting
        print("\n3. Formatted for AI Analysis:")
        print("\n" + "-"*70)
        print(context.format_for_ai())
        print("-"*70)
        
        # Test dictionary conversion
        print("\n4. Dictionary representation:")
        context_dict = context.to_dict()
        print(f"   Keys: {', '.join(context_dict.keys())}")
        
        print("\n" + "="*70)
        print("✅ Context loader test completed successfully!")
        print("="*70 + "\n")
        
    except ContextLoaderError as e:
        print(f"\n❌ Context loading failed: {e}\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        logger.error(f"Test failed: {e}", exc_info=True)
