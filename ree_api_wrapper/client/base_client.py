import requests
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
import pandas as pd

from enums.all_enums import GeoLimit, Language, Region
from ree_api_wrapper.widgets.demand import DemandWidgetClient
from .exceptions import REEAPIError, REEValidationError, REEConnectionError
from ..utils.response_parser import ResponseParser

class REEBaseClient:
    """Low-level HTTP base client for REE API communication"""
    BASE_URL = "https://apidatos.ree.es"
    
    def __init__(self, language: str = "es"):
        self.language = language
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Host':'apidatos.ree.es'
        })
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to REE API"""
        
        url = f"{self.BASE_URL}/{self.language}{endpoint}"
        
        # Handle list parameters
        processed_params = {}
        for key, value in params.items():
            if isinstance(value, list):
                # Convert list to comma-separated string or individual params
                if len(value) == 1:
                    processed_params[key] = value[0]
                else:
                    processed_params[key] = ','.join(map(str, value))
            else:
                processed_params[key] = value
                
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError:
            self._handle_http_error(response)
        except requests.exceptions.ConnectionError as e:
            raise REEConnectionError(f"Connection failed: {str(e)}")
        except requests.exceptions.Timeout as e:
            raise REEConnectionError(f"Request timeout: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise REEAPIError(f"Request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise REEAPIError(f"Invalid JSON response: {str(e)}")
    
    def _handle_http_error(self, response: requests.Response) -> None:
        """Handle HTTP errors and convert to custom exceptions."""
        try:
            error_data = response.json()
            if "errors" in error_data and error_data["errors"]:
                error = error_data["errors"][0]
                raise REEAPIError(
                    message=error.get("detail", "Unknown API error"),
                    status_code=response.status_code,
                    error_code=error.get("code")
                )
        except json.JSONDecodeError:
            pass
        
        # Fallback error message
        raise REEAPIError(
            message=f"HTTP {response.status_code}: {response.reason}",
            status_code=response.status_code
        )
    
    def close(self):
        """Close the session"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class REEClient:
    """
    High-level REE API client providing convenient access to all widgets
    """
    
    def __init__(self, language: Language = Language.SPANISH):
        self.base_client = REEBaseClient(language.value)
        
        # Initialize widget clients
        self.demand = DemandWidgetClient(self.base_client)
        # ...
    
    def close(self):
        """Close the underlying HTTP session"""
        self.base_client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
     