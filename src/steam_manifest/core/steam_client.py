"""Steam API client for Steam Manifest Tool."""

import logging
from typing import Dict, Any, List, Optional
from threading import Lock

import httpx
from retrying import retry

from .config import Config, URLBuilder


class SteamClient:
    """Steam API client for accessing Steam store data."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize Steam client.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.lock = Lock()
    
    @retry(wait_fixed=Config.RETRY_INTERVAL, stop_max_attempt_number=Config.RETRY_TIMES)
    def api_request(self, url: str) -> Optional[Dict[str, Any]]:
        """Send HTTP GET request to Steam API.
        
        Args:
            url: Request URL
            
        Returns:
            JSON response data or None if request failed
        """
        try:
            with httpx.Client(
                timeout=Config.TIMEOUT,
                headers=Config.HTTP_HEADERS,
                follow_redirects=True
            ) as client:
                with self.lock:
                    self.logger.debug(f"📡 Sending Steam API request: {url}")
                
                response = client.get(url)
                response.raise_for_status()
                
                json_data = response.json()
                
                with self.lock:
                    self.logger.debug(f"📥 Received Steam API response: {len(str(json_data))} bytes")
                
                return json_data
                
        except httpx.TimeoutException:
            self.logger.error(f"⌛ Steam API request timeout: {url}")
            return None
        except httpx.HTTPStatusError as e:
            self.logger.error(f"🔧 Steam API request failed: {e.response.status_code} - {url}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Steam API request exception: {str(e)} - {url}")
            return None
    
    def search_apps(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for Steam applications.
        
        Args:
            search_term: Search term for app name
            
        Returns:
            List of found applications
        """
        url = URLBuilder.steam_search(search_term)
        response = self.api_request(url)
        
        if not response or "items" not in response:
            self.logger.warning(f"No search results found for: {search_term}")
            return []
        
        return response.get("items", [])
    
    def get_app_details(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a Steam application.
        
        Args:
            app_id: Steam application ID
            
        Returns:
            Application details or None if not found
        """
        url = URLBuilder.steam_app_details(app_id)
        response = self.api_request(url)
        
        if not response or not isinstance(response, dict):
            return None
        
        app_data = response.get(app_id, {})
        if not app_data.get("success"):
            self.logger.warning(f"⚠️ Unable to get app info: {app_id}")
            return None
        
        return app_data.get("data", {})
    
    def get_app_dlc(self, app_id: str) -> List[int]:
        """Get DLC information for a Steam application.
        
        Args:
            app_id: Steam application ID
            
        Returns:
            List of DLC IDs
        """
        app_details = self.get_app_details(app_id)
        if not app_details:
            return []
        
        dlc_data = app_details.get("dlc", [])
        if dlc_data:
            self.logger.info(f"🎮 Found DLC info from Steam store: {dlc_data}")
            try:
                return [int(dlc_id) for dlc_id in dlc_data]
            except ValueError as e:
                self.logger.error(f"❌ Invalid DLC ID format: {e}")
                return []
        
        return []