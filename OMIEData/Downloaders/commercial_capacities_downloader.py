import datetime as dt
from OMIEData.Downloaders.general_omie_downloader import GeneralOMIEDownloader
from OMIEData.Enums.all_enums import BorderType, CapacityType
import requests
import os


class CommercialCapacitiesDownloader(GeneralOMIEDownloader):
    """Downloads commercial capacity data for cross-border electricity exchanges after day-ahead market clearing.
        It extends the base GeneralOMIEDownloader to provide specific functionality of accessing commercial exporting capacity occupation data, 
        from OMIE (Iberian Peninsula Electricity Market Operator) for exchanges between Spain and neighboring countries.
        The data includes import/export capacities, their occupation levels, and remaining free capacities for each hourly period after the day-ahead market auction process.
        
        The downloader handles border- and category-specific URL construction using templated patterns and supports:
        1. All available cross-border interconnections: Portugal, France and MOrocco. 
        2. Interconnection export/import capacity for both "After Market Clearance" and "After Technical Restraints/Constraints".

    """
    def __init__(self, border_type: BorderType = BorderType.PORTUGAL, capacity_type: CapacityType = CapacityType.AFTER_MARKET_CLEARANCE):
        """Initialize downloader for specific border and for which type of interconncetion capacity type (after market clearance, or after technical restrictions)
            
            Following OMIEData's conventions, sets up URL and output file patterns with border-specific and capacity data type placeholders.
            
            Args:
                border_type: The cross-border connection to download data for. Available options: BorderType.PORTUGAL (2), BorderType.FRANCE (3), BorderType.MOROCCO (5). Defaults to BorderType.PORTUGAL.
                capacity_type: Type of Interconncetion export/import capacity data to fetch. Available options: "Market Clearance" or "Technical Contrainsts/Restrictions", as defined in Enums.
        
            Example usage:
                - Access France's cross border, after technical constraints data
                OMIECommercialCapacitiesDownloader(BorderType.PORTUGAL,capacity_type=CapacityType.AFTER_TECHNICAL_RESTRICTIONS)
                - Access Portugal's cross-border, after market clearanced data 
                OMIECommercialCapacitiesDownloader(BorderType.PORTUGAL,capacity_type=CapacityType.AFTER_TECHNICAL_RESTRICTIONS)
                
        """
        self.border_type = border_type
        
        # Build URL pattern with border placeholder
        # Where: BB = border ID; DD/MM/YYYY = date components, 
        # capacity_type = Type of Interconncetion export/import capacity data "category" 
        # (either after market clearance or after technical constraints/restrictions)
        # get_url_suffix - defined in the Enums, it returns the value and url replacement suffix corresponding to the different 
        # URL configuration patterns/strings for each of the two  
        url_pattern = f'AGNO_YYYY/MES_MM/TXT/{capacity_type.get_url_suffix()}'
        output_pattern = f'omie_CC_{capacity_type.value}_BB_YYYYMMDD.txt'
        
        # Call parent constructor
        super().__init__(url_mask=url_pattern, output_mask=output_pattern)
    
    def get_expected_filename(self, date: dt.datetime) -> str:
        """Generate expected output filename for a given date, including border type.

        Overrides parent to handle border-specific filename generation.

        Args:
            date: Date to generate filename for

        Returns:
            Expected filename with border type substituted
        """
        filename = super().get_expected_filename(date)
        filename = filename.replace('BB', str(self.border_type.value))
        return filename

    def get_response_for_date(self, date: dt.datetime, verbose: bool = False):
        """Get HTTP response for a single date with border placeholder replacement.

        Overrides parent to handle border-specific URL generation.

        Args:
            date: Date to download data for
            verbose: Print progress messages

        Returns:
            HTTP Response object
        """
        url_aux = self._replace_placeholders(self.get_complete_url(), date)

        if verbose:
            print(f'Requesting {self.border_type.name} data: {url_aux}')

        return requests.get(url_aux, allow_redirects=True)

    def _replace_placeholders(self, template: str, date: dt.datetime) -> str:
        """
        Placeholder replacement that includes border support.

        This method extends the parent's placeholder logic to handle BB (border).
        Example:
        Template: "CC_BB_YYYYMMDD.txt"
        Border: Portugal (ID=2), Date: 2024-01-15
        Result: "CC_2_20240115.txt"


        """

        result = template.replace('DD', f'{date.day:02d}')
        result = result.replace('MM', f'{date.month:02d}')
        result = result.replace('YYYY', f'{date.year:04d}')
        result = result.replace('BB', str(self.border_type.value))

        return result
    
    def url_responses(self, date_ini: dt.datetime, date_end: dt.datetime, verbose=False):
        """
        Generate URL responses with border-specific handling.
        """
        dt_aux = date_ini
        while dt_aux <= date_end:
            # Use our enhanced placeholder replacement
            url_aux = self._replace_placeholders(self.get_complete_url(), dt_aux)
            
            if verbose:
                print(f'Requesting {self.border_type.name} data: {url_aux}')
            
            try:
                yield requests.get(url_aux, allow_redirects=True)
            except Exception as e:
                if verbose:
                    print(f'Error requesting {url_aux}: {e}')
                # TODO:Yield empty response or handle error
                
            dt_aux = dt_aux + dt.timedelta(days=1)
    
    def download_data(self, date_ini: dt.datetime, date_end: dt.datetime, output_folder: str, verbose=False) -> int:
        """
        Download data with border-specific handling.
        """
        
        error_count = 0
        dt_aux = date_ini
        
        while dt_aux <= date_end:
            try:
                # Use our enhanced placeholder replacement
                url_aux = self._replace_placeholders(self.get_complete_url(), dt_aux)
                file_aux = self._replace_placeholders(self.output_mask, dt_aux)
                file_path = os.path.join(output_folder, file_aux)
                
                if verbose:
                    print(f'Downloading {self.border_type.name}: {url_aux}')
                
                response = requests.get(url_aux, allow_redirects=True)
                response.raise_for_status()  # Raise exception for bad status codes
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                if verbose:
                    print(f'Saved to: {file_path}')
                    
            except Exception as e:
                if verbose:
                    print(f'Error downloading {url_aux}: {e}')
                error_count += 1
            
            dt_aux = dt_aux + dt.timedelta(days=1)
        
        return error_count