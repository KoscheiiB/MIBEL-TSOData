import datetime as dt
import pandas as pd
import os
from typing import List, Union, Optional

from OMIEData.DataImport.omie_data_importer_from_responses import OMIEDataImporterFromResponses
from OMIEData.Downloaders.commercial_capacities_downloader import CommercialCapacitiesDownloader
from OMIEData.FileReaders.commercial_capacities_file_reader import CommercialCapacitiesFileReader
from OMIEData.Enums.all_enums import BorderType, CapacityType


# ///////////////////////////////////////////////////////////////////////////////
# NEXT STEPS, +- by order of priority:
# 1. Incorporate parallel processing for the download process, in case of multiple borders and long waiting time
# 2. Imporove error handling 
# 3. Unit tests
# 4. Incorporate polars (better performance in data presentation and arrangement? or even flexible support for >)
# 5. Incorporate plotting methods?

class OMIECommercialCapacitiesImporter(OMIEDataImporterFromResponses):
    """High-level importer for OMIE commercial interconnection capacity data, across multiple cross-border connections 
    & with the support to both after "market clearance" or "technical constraints" capacity type data.
    
    Building from the OMIEDataImporterFromResponse, this importer orchestrates the complete data acquisition process for 
    commercial capacity occupation and export data on the day-ahead market sectorial information. 
    It coordinates specialized downloaders and file readers to provide a unified approach for accessing cross-border 
    electricity exchange capacity data from OMIE.

    The importer supports flexible border selection - users can fetch data for individual borders, specific combinations, 
    or all available borders simultaneously (default). The importer also supports the option of defining the capacity type 
    data category, from OMIE - after market clearance or after technical contraints, as defined in Enums.
    
    Example usage:
        - Import all borders for January 2024, after market clearance
        OMIECommercialCapacitiesImporter(dt.date(2024, 1, 1),dt.date(2024, 1, 31),borders='all', capacity_type=CapacityType.AFTER_MARKET_CLEARANCE)
        - Import Portugal and France data, after technical restrictions/contrainsts
        OMIECommercialCapacitiesImporter(dt.date(2024, 1, 1),dt.date(2024, 1, 31), borders=[BorderType.PORTUGAL, BorderType.FRANCE], capacity_type=CapacityType.AFTER_TECHNICAL_CLEARANCE)
    """
    
    def __init__(self, date_ini: dt.date, date_end: dt.date,
                 borders: Union[BorderType, List[BorderType], str] = None,
                 capacity_type: CapacityType = CapacityType.AFTER_MARKET_CLEARANCE):
        """
        Enhanced constructor/Importer with support to 1. flexible border choices and 2. Interconnection export/import capacity type.

        Args:
            date_ini: Start date
            date_end: End date
            borders: Border(s) to fetch data for. Can be 'all', None, BorderType, or list of BorderType
            capacity_type: Type of Interconncetion export capacity data to fetch (after "Market Clearance" or "Technical Contrainsts/Restrictions")
        """
        # Store capacity type
        self.capacity_type = capacity_type

        # Border selection logic
        if borders is None or borders == 'all':
            self.borders = BorderType.get_all_borders()
        elif isinstance(borders, BorderType):
            self.borders = [borders]
        elif isinstance(borders, list):
            self.borders = borders
        else:
            raise ValueError("borders must be 'all', BorderType, list of BorderType, or None")
        
        # Store for multi-border case
        self.date_ini = date_ini
        self.date_end = date_end
        
        # For single border, use the standard pattern
        if len(self.borders) == 1:
            super().__init__(
                date_ini=date_ini,
                date_end=date_end,
                file_downloader=CommercialCapacitiesDownloader(border_type=self.borders[0], capacity_type=capacity_type),
                file_reader=CommercialCapacitiesFileReader(border_type=self.borders[0])
            )
        else:
            # For multi-border, we'll override read_to_dataframe
            # Initialize with first border to satisfy parent constructor
            super().__init__(
                date_ini=date_ini,
                date_end=date_end,
                file_downloader=CommercialCapacitiesDownloader(border_type=self.borders[0], capacity_type=capacity_type),
                file_reader=CommercialCapacitiesFileReader(border_type=self.borders[0])
            )
    
    def read_to_dataframe(self,
                          verbose: bool = False,
                          save_raw_data_path: Optional[str] = None,
                          skip_existing: bool = True,
                          read_from_disk: bool = False) -> pd.DataFrame:
        """Override to handle multi-border support with resume and read-from-disk functionality.

        Args:
            verbose: Print progress messages
            save_raw_data_path: Optional path to save/read raw .txt files
            skip_existing: If True, skip downloading files that already exist on disk
            read_from_disk: If True, read all files from disk without downloading

        Returns:
            pd.DataFrame: Processed data
        """
        # Single border: use parent's optimized implementation
        if len(self.borders) == 1:
            return super().read_to_dataframe(verbose=verbose,
                                            save_raw_data_path=save_raw_data_path,
                                            skip_existing=skip_existing,
                                            read_from_disk=read_from_disk)

        # Multi-border: custom implementation
        return self._read_multi_border_dataframe(verbose=verbose,
                                                 save_raw_data_path=save_raw_data_path,
                                                 skip_existing=skip_existing,
                                                 read_from_disk=read_from_disk)
    
    def _read_multi_border_dataframe(self,
                                     verbose: bool = False,
                                     save_raw_data_path: Optional[str] = None,
                                     skip_existing: bool = True,
                                     read_from_disk: bool = False) -> pd.DataFrame:
        """Handle multi-border data fetching with resume and read-from-disk support.

        Args:
            verbose: Print progress messages
            save_raw_data_path: Optional path to save/read raw .txt files
            skip_existing: If True, skip downloading files that already exist on disk
            read_from_disk: If True, read all files from disk without downloading

        Returns:
            pd.DataFrame: Combined data from all borders
        """
        # Create directory if save path is provided
        if save_raw_data_path:
            os.makedirs(save_raw_data_path, exist_ok=True)
            if verbose:
                print(f'Raw data will be saved to: {save_raw_data_path}')

        all_data = []

        for border in self.borders:
            if verbose:
                print(f"\nFetching data for {border.get_country_name()}...")

            try:
                # Create border-specific downloader and reader
                downloader = CommercialCapacitiesDownloader(border_type=border, capacity_type=self.capacity_type)
                reader = CommercialCapacitiesFileReader(border_type=border)

                # Create temporary importer for this border
                border_importer = OMIEDataImporterFromResponses(
                    date_ini=self.date_ini,
                    date_end=self.date_end,
                    file_downloader=downloader,
                    file_reader=reader
                )

                # Use parent's read_to_dataframe with all parameters
                border_df = border_importer.read_to_dataframe(
                    verbose=verbose,
                    save_raw_data_path=save_raw_data_path,
                    skip_existing=skip_existing,
                    read_from_disk=read_from_disk
                )

                all_data.append(border_df)

            except Exception as exc:
                print(f'Error fetching data for {border.get_country_name()}: {exc}')

        # Combine all border data
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            return combined_df.sort_values(['DATE', 'COUNTRY', 'HOUR']).reset_index(drop=True)
        else:
            return pd.DataFrame(columns=CommercialCapacitiesFileReader().get_keys())