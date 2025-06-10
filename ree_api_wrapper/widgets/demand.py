from typing import Optional
from ..enums.widget_enums import DemandWidget
from ..enums.all_enums import TimeAggregation, Region
from .base_widget import BaseWidget


class DemandWidgetClient(BaseWidget):
    """Client for demand category widgets"""
    
    @property
    def category(self) -> str:
        return "demanda"
    
    @property  
    def widget_enum(self):
        return DemandWidget
    
    def get_evolution(self, start_date, end_date, time_trunc: TimeAggregation, 
                     region: Optional[Region] = None, **kwargs):
        """Get demand evolution data"""
        return self.get_data(
            widget=DemandWidget.EVOLUTION,
            start_date=start_date,
            end_date=end_date,
            time_trunc=time_trunc,
            region=region,
            **kwargs
        )

