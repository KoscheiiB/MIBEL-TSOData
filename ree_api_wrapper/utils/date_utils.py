from datetime import datetime, date
from typing import Union
import pandas as pd
from client.exceptions import REEValidationError

class DateHandler:
    """Handle date parsing and validation"""
    
    @staticmethod
    def parse_date(date_input: Union[str, datetime, date]) -> datetime:
        """Parse various date formats to datetime"""
        
        if isinstance(date_input, datetime):
            return date_input
        
        if isinstance(date_input, date):
            return datetime.combine(date_input, datetime.min.time())
        
        if isinstance(date_input, str):
            try:
                # Try ISO format first
                return datetime.fromisoformat(date_input.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Try pandas date parser
                    return pd.to_datetime(date_input).to_pydatetime()
                except Exception:
                    raise REEValidationError(f"Invalid date format: {date_input}")
        
        raise REEValidationError(f"Unsupported date type: {type(date_input)}")
    
    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime) -> None:
        """Validate date range"""
        if start_date >= end_date:
            raise REEValidationError("start_date must be before end_date")