from enum import Enum
from typing import Optional, Set, Dict, List
from ..enums.all_enums import TimeAggregation, GeoLimit

# Specific enums, designed to validate data availability contraints 
# (there can be identified by directly using/filtering through OMIE's data portal.

class DemandWidget(Enum):
    """Demand category widgets with their parameter constraints"""
    
    EVOLUTION = ("evolucion", {
        "allowed_time_trunc": {TimeAggregation.HOUR, TimeAggregation.DAY, TimeAggregation.MONTH, TimeAggregation.YEAR},
        "system_level_time_trunc": {TimeAggregation.HOUR, TimeAggregation.DAY, TimeAggregation.MONTH, TimeAggregation.YEAR},
        "ccaa_time_trunc": {TimeAggregation.MONTH, TimeAggregation.YEAR},
        "supports_real_time": True,
        "requires_geo_trunc": False
    })
    
    def __init__(self, api_name: str, constraints: Dict):
        self.api_name = api_name
        self.constraints = constraints
    
    def validate_parameters(self, time_trunc: TimeAggregation, geo_limit: Optional[GeoLimit] = None) -> bool:
        """Validate parameter combination for this widget"""
        
        # Check if time_trunc is allowed for this widget
        if time_trunc not in self.constraints["allowed_time_trunc"]:
            return False
        
        # Check geo-specific constraints
        if geo_limit == GeoLimit.CCAA:
            return time_trunc in self.constraints["ccaa_time_trunc"]
        else:
            return time_trunc in self.constraints["system_level_time_trunc"]