"""
Freshdesk API client for fetching feedback tickets.

This module provides a client for interacting with the Freshdesk API to fetch
feedback tickets based on specific filters (game name, OS, date range, etc.).
It handles authentication, pagination, and error handling.
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from requests.auth import HTTPBasicAuth

from .config import get_settings
from .input_handler import FeedbackAnalysisInput
from .logger import get_logger


# Initialize logger for this module
logger = get_logger(__name__)


class FreshdeskAPIError(Exception):
    """Custom exception for Freshdesk API errors."""
    pass


class FreshdeskClient:
    """
    Client for interacting with Freshdesk API.
    
    This client handles authentication, ticket fetching with filters,
    pagination, and error handling for the Freshdesk API.
    
    Attributes:
        domain: Freshdesk domain (e.g., 'yourcompany.freshdesk.com')
        api_key: Freshdesk API key for authentication
        base_url: Base URL for API requests
    """
    
    def __init__(self, domain: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the Freshdesk client.
        
        Args:
            domain: Freshdesk domain. If None, loads from environment
            api_key: Freshdesk API key. If None, loads from environment
        """
        settings = get_settings()
        
        self.api_key = api_key or settings.freshdesk_api_key
        self.domain = domain or settings.freshdesk_domain
        
        if not self.domain:
            raise FreshdeskAPIError(
                "Freshdesk domain not configured. "
                "Set FRESHDESK_DOMAIN in .env file."
            )
        
        # Ensure domain doesn't have protocol
        self.domain = self.domain.replace('https://', '').replace('http://', '')
        
        # Build base URL
        self.base_url = f"https://{self.domain}/api/v2/"
        
        # Setup authentication
        self.auth = HTTPBasicAuth(self.api_key, 'X')
        
        logger.info(f"Initialized Freshdesk client for domain: {self.domain}")
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = 'GET'
    ) -> requests.Response:
        """
        Make an HTTP request to the Freshdesk API.
        
        Args:
            endpoint: API endpoint (e.g., 'tickets')
            params: Query parameters
            method: HTTP method (GET, POST, etc.)
            
        Returns:
            requests.Response object
            
        Raises:
            FreshdeskAPIError: If request fails
        """
        url = urljoin(self.base_url, endpoint)
        
        try:
            logger.debug(f"Making {method} request to {endpoint}")
            logger.debug(f"Parameters: {params}")
            
            response = requests.request(
                method=method,
                url=url,
                auth=self.auth,
                params=params,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                return self._make_request(endpoint, params, method)
            
            # Raise exception for HTTP errors
            response.raise_for_status()
            
            logger.debug(f"Request successful. Status code: {response.status_code}")
            return response
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error occurred: {e}"
            if hasattr(e.response, 'text'):
                error_msg += f"\nResponse: {e.response.text}"
            logger.error(error_msg)
            raise FreshdeskAPIError(error_msg) from e
            
        except requests.exceptions.Timeout as e:
            error_msg = f"Request timeout: {e}"
            logger.error(error_msg)
            raise FreshdeskAPIError(error_msg) from e
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {e}"
            logger.error(error_msg)
            raise FreshdeskAPIError(error_msg) from e
    
    def _filter_tickets_by_criteria(
        self,
        tickets: List[Dict[str, Any]],
        input_params: FeedbackAnalysisInput
    ) -> List[Dict[str, Any]]:
        """
        Apply strict client-side filtering to tickets.
        
        This function applies additional filtering on tickets to ensure they match
        all criteria, especially for custom fields like game name and OS.
        
        Args:
            tickets: List of ticket dictionaries from API
            input_params: User input parameters with filter criteria
            
        Returns:
            List of filtered tickets matching all criteria
        """
        filtered_tickets = []
        
        logger.debug(f"Applying client-side filters to {len(tickets)} tickets")
        
        for ticket in tickets:
            # Filter by status (Only Closed = 5)
            # Status values: 2=Open, 3=Pending, 4=Resolved, 5=Closed
            status = ticket.get('status')
            if status != 5:  # Only Closed
                continue
            
            # Filter by type (Feedback - usually a custom field or tag)
            # This may vary by Freshdesk configuration
            ticket_type = ticket.get('type')
            tags = ticket.get('tags', [])
            
            # Check if it's a feedback ticket
            # (adjust based on your Freshdesk configuration)
            is_feedback = (
                ticket_type == 'Feedback' or
                'feedback' in [tag.lower() for tag in tags] or
                'Feedback' in tags
            )
            
            if not is_feedback:
                continue
            
            # Filter by date range
            created_at = ticket.get('created_at')
            if created_at:
                try:
                    # Parse Freshdesk datetime (ISO format)
                    ticket_date = datetime.fromisoformat(
                        created_at.replace('Z', '+00:00')
                    ).date()
                    
                    start_date = datetime.strptime(
                        input_params.start_date, '%Y-%m-%d'
                    ).date()
                    end_date = datetime.strptime(
                        input_params.end_date, '%Y-%m-%d'
                    ).date()
                    
                    if not (start_date <= ticket_date <= end_date):
                        continue
                        
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse date for ticket {ticket.get('id')}: {e}")
                    continue
            
            # Filter by game name (check subject, description, and custom fields)
            game_name_lower = input_params.game_name.lower()
            
            subject = (ticket.get('subject') or '').lower()
            description = (ticket.get('description_text') or '').lower()
            
            # Check if game name appears in subject or description
            game_match = (
                game_name_lower in subject or
                game_name_lower in description
            )
            
            # Also check custom fields if they exist
            custom_fields = ticket.get('custom_fields', {})
            if custom_fields:
                game_field = custom_fields.get('game_name', '').lower()
                if game_name_lower in game_field:
                    game_match = True
            
            if not game_match:
                continue
            
            # Filter by OS
            os_filter = input_params.os
            
            if os_filter != 'Both':
                # Check subject, description, and custom fields for OS
                # Handle variations: Android, iOS, IOS (case-insensitive)
                os_match = False
                
                # For iOS, check both "ios" and "iOS" variations
                if os_filter.lower() == 'ios':
                    # Check for "ios" or "iOS" or "IOS"
                    os_variations = ['ios', 'iOS', 'IOS']
                    for os_var in os_variations:
                        if os_var in subject or os_var in description:
                            os_match = True
                            break
                else:
                    # For Android, simple case-insensitive match
                    if os_filter.lower() in subject or os_filter.lower() in description:
                        os_match = True
                
                # Check custom fields
                if custom_fields and not os_match:
                    os_field = custom_fields.get('os', '')
                    platform_field = custom_fields.get('platform', '')
                    
                    # Handle iOS variations in custom fields
                    if os_filter.lower() == 'ios':
                        if os_field in ['ios', 'iOS', 'IOS'] or platform_field in ['ios', 'iOS', 'IOS']:
                            os_match = True
                    else:
                        if os_filter.lower() in os_field.lower() or os_filter.lower() in platform_field.lower():
                            os_match = True
                
                if not os_match:
                    continue
            
            # Ticket passed all filters
            filtered_tickets.append(ticket)
        
        logger.info(
            f"Filtered {len(tickets)} tickets down to {len(filtered_tickets)} "
            f"matching all criteria"
        )
        
        return filtered_tickets
    
    def fetch_feedback_tickets(
        self,
        input_params: FeedbackAnalysisInput,
        max_pages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch feedback tickets from Freshdesk with strict filtering.
        
        Fetches tickets matching the following criteria:
        - Type: Feedback
        - Status: Closed (Resolved or Closed)
        - Created date: Between start_date and end_date
        - Game name: Matches user input
        - OS: Matches selected filter (if not 'Both')
        
        Args:
            input_params: FeedbackAnalysisInput with filter criteria
            max_pages: Maximum number of pages to fetch (safety limit)
            
        Returns:
            List of ticket dictionaries matching all criteria
            
        Example:
            >>> client = FreshdeskClient()
            >>> params = FeedbackAnalysisInput(...)
            >>> tickets = client.fetch_feedback_tickets(params)
            >>> print(f"Found {len(tickets)} feedback tickets")
        """
        logger.info("="*70)
        logger.info("Starting Freshdesk ticket fetch")
        logger.info(f"Filters: Game={input_params.game_name}, OS={input_params.os}")
        logger.info(f"Date Range: {input_params.start_date} to {input_params.end_date}")
        logger.info("="*70)
        
        all_tickets = []
        page = 1
        per_page = 100  # Freshdesk max is 100 per page
        
        while page <= max_pages:
            logger.info(f"Fetching page {page}...")
            
            # Build query parameters
            # Note: Freshdesk API has limited filtering, so we'll fetch broadly
            # and filter client-side for strict matching
            params = {
                'per_page': per_page,
                'page': page,
                # Include updated tickets within a broader range
                'order_by': 'created_at',
                'order_type': 'desc'
            }
            
            try:
                # Make API request
                response = self._make_request('tickets', params=params)
                tickets = response.json()
                
                if not tickets:
                    logger.info("No more tickets found. Pagination complete.")
                    break
                
                logger.info(f"Retrieved {len(tickets)} tickets from page {page}")
                
                # Apply strict client-side filtering
                filtered = self._filter_tickets_by_criteria(tickets, input_params)
                all_tickets.extend(filtered)
                
                logger.info(
                    f"Page {page}: {len(filtered)} tickets matched criteria "
                    f"(Total so far: {len(all_tickets)})"
                )
                
                # Check if we got less than per_page (last page)
                if len(tickets) < per_page:
                    logger.info("Received fewer tickets than page size. Last page reached.")
                    break
                
                page += 1
                
                # Small delay to be nice to the API
                time.sleep(0.5)
                
            except FreshdeskAPIError as e:
                logger.error(f"Failed to fetch page {page}: {e}")
                break
        
        logger.info("="*70)
        logger.info(f"✓ Fetch complete: {len(all_tickets)} total tickets match all criteria")
        logger.info("="*70)
        
        return all_tickets
    
    def get_ticket_by_id(self, ticket_id: int) -> Dict[str, Any]:
        """
        Fetch a single ticket by ID.
        
        Args:
            ticket_id: Freshdesk ticket ID
            
        Returns:
            Ticket data as dictionary
        """
        logger.info(f"Fetching ticket {ticket_id}")
        
        response = self._make_request(f'tickets/{ticket_id}')
        ticket = response.json()
        
        logger.info(f"Successfully fetched ticket {ticket_id}")
        return ticket
    
    def test_connection(self) -> bool:
        """
        Test the connection to Freshdesk API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info("Testing Freshdesk API connection...")
            
            # Try to fetch a single ticket
            response = self._make_request('tickets', params={'per_page': 1})
            
            logger.info("✓ Connection test successful!")
            return True
            
        except FreshdeskAPIError as e:
            logger.error(f"✗ Connection test failed: {e}")
            return False


def fetch_feedback_data(input_params: FeedbackAnalysisInput) -> Dict[str, Any]:
    """
    High-level function to fetch feedback data from Freshdesk.
    
    This is the main entry point for fetching Freshdesk data. It creates
    a client, fetches tickets, and returns them in a structured format.
    
    Args:
        input_params: FeedbackAnalysisInput with filter criteria
        
    Returns:
        Dictionary with metadata and feedback tickets
        
    Example:
        >>> params = FeedbackAnalysisInput(...)
        >>> data = fetch_feedback_data(params)
        >>> print(f"Fetched {len(data['feedbacks'])} tickets")
    """
    logger.info("Starting feedback data fetch from Freshdesk")
    
    # Create Freshdesk client
    client = FreshdeskClient()
    
    # Test connection first
    if not client.test_connection():
        raise FreshdeskAPIError(
            "Failed to connect to Freshdesk API. "
            "Please check your API key and domain configuration."
        )
    
    # Fetch tickets
    tickets = client.fetch_feedback_tickets(input_params)
    
    # Structure the response
    data = {
        'metadata': {
            'game_name': input_params.game_name,
            'os': input_params.os,
            'start_date': input_params.start_date,
            'end_date': input_params.end_date,
            'fetched_at': datetime.now().isoformat(),
            'total_records': len(tickets),
            'source': 'freshdesk_api',
            'domain': client.domain
        },
        'feedbacks': tickets
    }
    
    logger.info(f"✓ Successfully fetched {len(tickets)} feedback tickets")
    
    return data


if __name__ == "__main__":
    # Test the Freshdesk client
    print("\n" + "="*70)
    print("  TESTING FRESHDESK API CLIENT")
    print("="*70 + "\n")
    
    try:
        # Create a test client
        print("1. Initializing Freshdesk client...")
        client = FreshdeskClient()
        print(f"   ✓ Client initialized for domain: {client.domain}\n")
        
        # Test connection
        print("2. Testing API connection...")
        if client.test_connection():
            print("   ✓ Connection successful!\n")
        else:
            print("   ✗ Connection failed!\n")
            exit(1)
        
        # Create test parameters
        print("3. Creating test filter parameters...")
        test_params = FeedbackAnalysisInput(
            game_name="Test Game",
            os="Android",
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        print(f"   Game: {test_params.game_name}")
        print(f"   OS: {test_params.os}")
        print(f"   Date Range: {test_params.start_date} to {test_params.end_date}\n")
        
        # Fetch tickets
        print("4. Fetching feedback tickets...")
        print("   (This may take a moment...)\n")
        
        data = fetch_feedback_data(test_params)
        
        print(f"\n   ✓ Fetch complete!")
        print(f"   Total tickets found: {len(data['feedbacks'])}")
        
        if data['feedbacks']:
            print(f"\n5. Sample ticket (first result):")
            sample = data['feedbacks'][0]
            print(f"   ID: {sample.get('id')}")
            print(f"   Subject: {sample.get('subject')}")
            print(f"   Status: {sample.get('status')}")
            print(f"   Created: {sample.get('created_at')}")
        
        print("\n" + "="*70)
        print("✅ Freshdesk API client test completed successfully!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
        exit(1)
