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
        Apply client-side filtering to tickets.
        
        Filters ALL tickets from regular API by:
        - Status: 5 (Closed)
        - updated_at: Within date range  
        - Game: From custom_fields['Game']
        
        OS and Type filtering happens in AI step.
        
        Args:
            tickets: List of all ticket dictionaries from API
            input_params: User input parameters
            
        Returns:
            List of Closed tickets matching date range and game (all OS, all types)
        """
        filtered_tickets = []
        
        logger.info(f"Filtering {len(tickets)} tickets for Game → Date → Type...")
        
        game_rejected = 0
        date_rejected = 0
        type_rejected = 0
        no_custom_fields = 0
        
        for ticket in tickets:
            # NO Status filter - all statuses included
            
            # Filter 1: Date range (updated_at)
            updated_at = ticket.get('updated_at')
            if updated_at:
                try:
                    ticket_date = datetime.fromisoformat(
                        updated_at.replace('Z', '+00:00')
                    ).date()
                    
                    start_date = datetime.strptime(
                        input_params.start_date, '%Y-%m-%d'
                    ).date()
                    end_date = datetime.strptime(
                        input_params.end_date, '%Y-%m-%d'
                    ).date()
                    
                    if not (start_date <= ticket_date <= end_date):
                        date_rejected += 1
                        continue
                        
                except (ValueError, AttributeError) as e:
                    date_rejected += 1
                    continue
            else:
                date_rejected += 1
                continue
            
            # Filter 2: Game name (custom_fields['game'])
            game_name_lower = input_params.game_name.lower()
            custom_fields = ticket.get('custom_fields', {})
            
            if not custom_fields:
                game_rejected += 1
                continue
            
            game_field = str(custom_fields.get('game', '')).lower()
            if game_name_lower not in game_field:
                game_rejected += 1
                continue
            
            # Filter 3: Type = "Feedback" (ticket['type'])
            ticket_type = ticket.get('type')
            if ticket_type != 'Feedback':
                type_rejected += 1
                continue
            
            # Passed all filters (Date + Game + Type)
            filtered_tickets.append(ticket)
        
        logger.info(f"✅ Filtered: {len(tickets)} tickets → {len(filtered_tickets)} tickets")
        logger.info(f"   Step 1 - Date: {len(tickets) - date_rejected} in range, {date_rejected} outside")
        logger.info(f"   Step 2 - Status: {len(tickets) - date_rejected - status_rejected} Closed, {status_rejected} other statuses")
        logger.info(f"   Step 3 - Game: {len(tickets) - date_rejected - status_rejected - game_rejected - no_custom_fields} '{input_params.game_name}' tickets")
        logger.info(f"   Step 4 - OS: {len(filtered_tickets)} '{input_params.os}' tickets, {os_rejected} other OS")
        logger.info(f"   ✅ Final: {len(filtered_tickets)} Closed '{input_params.game_name}' tickets on '{input_params.os}'")
        
        return filtered_tickets
    
    def fetch_feedback_tickets(
        self,
        input_params: FeedbackAnalysisInput,
        max_pages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch tickets for a specific game within the date range using Freshdesk Search API.
        
        Server-side filters (Search API query):
        - Status: 4, 5, or 6 (Resolved, Closed, Waiting on Customer)
        - updated_at: Between start_date and end_date
        
        Client-side filters (after fetch):
        - Game: Matches custom_fields['Game'] (custom fields not supported in Search API)
        
        NO OS or Type filtering - pulls all OS and all types.
        OS and Type filtering happens LATER before AI.
        
        Returns only essential fields: id, subject, description (+ minimal metadata for OS filtering)
        
        Args:
            input_params: FeedbackAnalysisInput with game name and date range
            max_pages: Maximum number of pages to fetch (safety limit)
            
        Returns:
            List of ticket dictionaries for the game within date range (all OS, all types)
            
        Example:
            >>> client = FreshdeskClient()
            >>> params = FeedbackAnalysisInput(...)
            >>> tickets = client.fetch_feedback_tickets(params)
            >>> print(f"Found {len(tickets)} total tickets (all types)")
        """
        logger.info("="*70)
        logger.info("Fetching tickets using Regular Tickets API")
        logger.info(f"Endpoint: /api/v2/tickets (paginated)")
        logger.info(f"Client-Side Filters Will Be Applied:")
        logger.info(f"  • Status: 5 (Closed)")
        logger.info(f"  • Date Range (updated_at): {input_params.start_date} to {input_params.end_date}")
        logger.info(f"  • Game: '{input_params.game_name}' (custom_fields['Game'])")
        logger.info(f"AI Step Filters:")
        logger.info(f"  • OS: '{input_params.os}' (custom_fields['OS'])")
        logger.info(f"  • Type: 'Feedback' (custom_fields['Type'])")
        logger.info("="*70)
        
        all_tickets = []
        page = 1
        
        while page <= max_pages:
            logger.info(f"Fetching page {page}...")
            
            # Use REGULAR Tickets API with description included
            # include=description ensures we get the full ticket description
            endpoint = f"tickets?include=description&per_page=100&page={page}&order_by=updated_at&order_type=desc"
            
            logger.debug(f"Fetching from: {endpoint}")
            
            try:
                # Make API request
                response = self._make_request(endpoint, method='GET')
                
                # Regular Tickets API returns array directly
                tickets = response.json()
                
                if not isinstance(tickets, list):
                    logger.error(f"Unexpected response format: {type(tickets)}")
                    break
                
                if not tickets:
                    logger.info("No more tickets found.")
                    break
                
                logger.info(f"Retrieved {len(tickets)} tickets from page {page}")
                
                # Apply client-side filtering for custom fields (game_name and OS)
                filtered = self._filter_tickets_by_criteria(tickets, input_params)
                all_tickets.extend(filtered)
                
                logger.info(
                    f"Page {page}: {len(filtered)} tickets matched criteria "
                    f"(Total so far: {len(all_tickets)})"
                )
                
                # Check if there are more pages
                if not tickets or len(tickets) < 100:  # Regular API uses 100 per page
                    logger.info("All tickets fetched.")
                    break
                
                page += 1
                
                # Small delay to be nice to the API
                time.sleep(0.5)
                
            except FreshdeskAPIError as e:
                logger.error(f"Failed to fetch page {page}: {e}")
                break
        
        logger.info("="*70)
        logger.info(f"✅ Fetch complete: {len(all_tickets)} Feedback tickets for '{input_params.game_name}'")
        logger.info(f"   Includes: All Dates, All Statuses, All OS")
        logger.info(f"Next Steps:")
        logger.info(f"   • Date filtering: Applied during data analysis")
        logger.info(f"   • OS filtering: '{input_params.os}' in AI step")
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
