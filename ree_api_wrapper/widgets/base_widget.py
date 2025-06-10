from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import pandas as pd

from client.base_client import REEBaseClient
from ..enums.all_enums import TimeAggregation, Region, GeoLimit
from utils.date_utils import DateHandler
from utils.response_parser import ResponseParser
from client.exceptions import REEValidationError


class BaseWidget(ABC):
    """Abstract base class for all REE widgets"""
    
    def __init__(self, client: REEBaseClient):
        self.client = client
        self.date_handler = DateHandler()
        self.parser = ResponseParser()
    
    @property
    @abstractmethod
    def category(self) -> str:
        """Widget category (e.g., 'demanda')"""
        pass
    
    @property
    @abstractmethod
    def widget_enum(self):
        """Widget enum class"""
        pass
    
    def get_data(self,
                 widget: Union[str, Enum],
                 start_date: Union[str, datetime],
                 end_date: Union[str, datetime],
                 time_trunc: TimeAggregation,
                 region: Optional[Region] = None,
                 geo_limit: Optional[GeoLimit] = None,
                 geo_ids: Optional[Union[int, List[int]]] = None,
                 return_raw: bool = False) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Get widget data with validation and processing
        
        Args:
            widget: Widget identifier (enum or string)
            start_date: Start date
            end_date: End date  
            time_trunc: Time aggregation
            region: Region (takes precedence over manual geo params)
            geo_limit: Manual geo limit
            geo_ids: Manual geo IDs
            return_raw: Return raw response instead of DataFrame
            
        Returns:
            DataFrame or raw response dict
        """
        # Parse and validate dates
        start_dt = self.date_handler.parse_date(start_date)
        end_dt = self.date_handler.parse_date(end_date)
        self.date_handler.validate_date_range(start_dt, end_dt)
        
        # Convert widget to enum if string
        if isinstance(widget, str):
            widget_enum = self._get_widget_by_name(widget)
        else:
            widget_enum = widget
        
        # Validate parameters
        self._validate_parameters(widget_enum, time_trunc, region, geo_limit)
        
        # Build parameters
        params = self._build_parameters(start_dt, end_dt, time_trunc, region, geo_limit, geo_ids)
        
        # Make API request
        endpoint = f"/datos/{self.category}/{widget_enum.api_name}"
        raw_response = self.client.make_request(endpoint, params)
        
        if return_raw:
            return raw_response
        
        # Convert to DataFrame
        return self.parser.to_dataframe(raw_response)
    
    def _get_widget_by_name(self, widget_name: str):
        """Get widget enum by API name"""
        for widget in self.widget_enum:
            if widget.api_name == widget_name:
                return widget
        raise REEValidationError(f"Unknown widget: {widget_name}")
    
    def _validate_parameters(self, widget_enum, time_trunc: TimeAggregation, 
                           region: Optional[Region], geo_limit: Optional[GeoLimit]):
        """Validate parameter combinations"""
        # Determine effective geo_limit
        effective_geo_limit = None
        if region:
            effective_geo_limit = GeoLimit.CCAA if region.geo_limit == "ccaa" else None
        elif geo_limit:
            effective_geo_limit = geo_limit
        
        # Validate widget constraints
        if not widget_enum.validate_parameters(time_trunc, effective_geo_limit):
            raise REEValidationError(
                f"Invalid parameter combination for {widget_enum.api_name}: "
                f"time_trunc={time_trunc.value}, geo_limit={effective_geo_limit}"
            )
    
    def _build_parameters(self, start_dt: datetime, end_dt: datetime, 
                         time_trunc: TimeAggregation, region: Optional[Region],
                         geo_limit: Optional[GeoLimit], geo_ids: Optional[Union[int, List[int]]]) -> Dict[str, Any]:
        """Build API request parameters"""
        params = {
            'start_date': start_dt.strftime('%Y-%m-%dT%H:%M'),
            'end_date': end_dt.strftime('%Y-%m-%dT%H:%M'),
            'time_trunc': time_trunc.value
        }
        
        # Handle geographical parameters
        if region and region.requires_geo_params:
            params.update({
                'geo_trunc': 'electric_system',
                'geo_limit': region.geo_limit,
                'geo_ids': region.geo_id
            })
        elif geo_limit and geo_ids is not None:
            params.update({
                'geo_trunc': 'electric_system',
                'geo_limit': geo_limit.value,
                'geo_ids': geo_ids if isinstance(geo_ids, list) else [geo_ids]
            })
        
        return params