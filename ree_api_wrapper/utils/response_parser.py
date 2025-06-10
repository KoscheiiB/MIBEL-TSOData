
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from client.exceptions import REEDataError
import pytz

# Nest steps:
# Incorporate upstream/downstream language parameter, controling language in columns.
# Optimize and make it more abstract as possible

class ResponseParser:
    """ Enhanced parser for REE API responses. 
        Already prepared to parse more than one timeseries per request 
        (i.e., len(indicators)) 
    """
    
    def __init__(self):
        self.madrid_tz = pytz.timezone('Europe/Madrid')
    
    def to_dataframe(self, response_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert REE API JSON response to pandas DataFrame
        Handles both single and multiple indicators properly
        """
        
        try:
            indicators = response_data['included']
            
            # Process all indicators - the logic should be the same regardless of count
            return self._process_indicators(indicators)
                
        except Exception as e:
            if isinstance(e, REEDataError):
                raise
            else:
                raise REEDataError(f"Failed to parse API response: {str(e)}")
    
    def _process_indicators(self, indicators: List[Dict[str, Any]]) -> pd.DataFrame:
        """Process indicators and combine into single DataFrame"""
        if len(indicators) == 1:
            # Single indicator case (like demand evolution)
            return self._process_single_indicator(indicators[0])
        else:
            # Multiple indicators case (like generation by technology)
            return self._process_multiple_indicators(indicators)
    
    def _process_single_indicator(self, indicator: Dict[str, Any]) -> pd.DataFrame:
        """Process single indicator response (e.g., demand evolution over time)"""
        values = indicator['attributes']['values']
        
        if not values:
            raise REEDataError("No values found in indicator data")
        
        # Create DataFrame from values
        df = pd.DataFrame(values)
        
        # Process datetime and set as index
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime')
        
        # Clean up percentage column if it's constant (like in demand data)
        if 'percentage' in df.columns:
            if df['percentage'].nunique() <= 1 and df['percentage'].iloc[0] == 1.0:
                df = df.drop(columns=['percentage'])
        
        # Rename value column to indicator name for clarity
        indicator_name = indicator['attributes'].get('title', 'value')
        if 'value' in df.columns:
            df = df.rename(columns={'value': indicator_name})
        
        # Add metadata as attributes
        df.attrs['indicator_name'] = indicator_name
        df.attrs['magnitude'] = indicator['attributes'].get('magnitude', '')
        df.attrs['last_update'] = indicator['attributes'].get('last-update', '')
        df.attrs['data_type'] = 'single_indicator'
        
        return df.sort_index()
    
    def _process_multiple_indicators(self, indicators: List[Dict[str, Any]]) -> pd.DataFrame:
        """Process multiple indicators and combine into single DataFrame"""
        all_dataframes = []
        
        for indicator in indicators:
            values = indicator['attributes']['values']
            if not values:
                continue
                
            indicator_name = indicator['attributes'].get('title', f"indicator_{indicator.get('id', 'unknown')}")
            
            # Create DataFrame for this indicator
            df_indicator = pd.DataFrame(values)
            df_indicator['datetime'] = pd.to_datetime(df_indicator['datetime'])
            df_indicator = df_indicator.set_index('datetime')
            
            # Convert timezone
            df_indicator.index = self._convert_timezone(df_indicator.index)
            
            # Rename columns to include indicator name
            column_mapping = {}
            if 'value' in df_indicator.columns:
                column_mapping['value'] = f"{indicator_name}_value"
            if 'percentage' in df_indicator.columns:
                column_mapping['percentage'] = f"{indicator_name}_percentage"
            
            df_indicator = df_indicator.rename(columns=column_mapping)
            all_dataframes.append(df_indicator)
        
        if not all_dataframes:
            raise REEDataError("No valid indicators found in response")
        
        # Combine all indicators into single DataFrame
        df_combined = pd.concat(all_dataframes, axis=1, sort=True)
        
        # Add metadata
        df_combined.attrs['data_type'] = 'multiple_indicators'
        df_combined.attrs['indicator_count'] = len(indicators)
        df_combined.attrs['indicators'] = [ind['attributes'].get('title', '') for ind in indicators]
        
        return df_combined.sort_index()
    
    def _convert_timezone(self, datetime_index: pd.DatetimeIndex) -> pd.DatetimeIndex:
        """Convert timezone to Madrid timezone"""
        if datetime_index.tz is not None:
            return datetime_index.tz_convert(self.madrid_tz)
        else:
            # If no timezone info, assume UTC and convert
            return datetime_index.tz_localize('UTC').tz_convert(self.madrid_tz)