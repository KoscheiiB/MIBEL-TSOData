import datetime as dt
import pandas as pd
from typing import Optional, List, Union

from OMIEData.DataImport.omie_data_importer_from_responses import OMIEDataImporterFromResponses
from OMIEData.Downloaders.supply_demand_curve_downloader import SupplyDemandCurveDownloader
from OMIEData.FileReaders.supply_demand_curve_file_reader import SupplyDemandCurvesReader

# //////////////////////////////////////// First approach ////////////////////////////////////////
# Approach 1:
# Extend OMIESupplyDemandCurves importer to accept additionall valid parameters, besides one integer 
# (e.g., list of spacific hours or 'all').

# NEXT STEPS, +- by order of priority:
# 1. Incorporate parallel processing (draft in comments, below) for the download process, in case of multiple hours and long waiting time
# 2. Validate performance of approaches
# 3. Error handling (e.g., handle cases where certain hours might not be available, send alert if raised, ...)
# 4. Unit tests
# 5. Validate Enums
# 6. ...


class OMIESupplyDemandCurvesExtendedImporter(OMIEDataImporterFromResponses):
    """
    Extended version that can fetch supply-demand curves for multiple hours
    while reusing the existing downloader and file reader architecture.
    """

    def __init__(self,
                 date_ini: dt.date,
                 date_end: dt.date,
                 hours: Optional[Union[int, List[int], str]] = "all"):
        """
        Initialize extended importer for multiple hours.
        
        Args:
            date_ini: Start date
            date_end: End date
            hours: int, List[int], or "all" for hours 1-24
        """
        self.date_ini = date_ini
        self.date_end = date_end
        self.hours = self._parse_hours(hours)
        
        # Reuse existing reader
        self.file_reader = SupplyDemandCurvesReader()
        
        # Don't call super().__init__ here since we'll handle multiple downloaders
        
    def _parse_hours(self, hours: Union[int, List[int], str]) -> List[int]:
        """Parse hours parameter into list of integers."""
        if hours == "all":
            return list(range(1, 25))
        elif isinstance(hours, int):
            if not 1 <= hours <= 24:
                raise ValueError("Hour must be between 1 and 24")
            return [hours]
        elif isinstance(hours, list):
            for h in hours:
                if not isinstance(h, int) or not 1 <= h <= 24:
                    raise ValueError("All hours must be integers between 1 and 24")
            return sorted(list(set(hours)))
        else:
            raise ValueError("Hours must be int, List[int], or 'all'")

    def read_to_dataframe(self,
                          verbose: bool = False,
                          save_raw_data_path: Optional[str] = None,
                          skip_existing: bool = True,
                          read_from_disk: bool = False) -> pd.DataFrame:
        """
        Download and read supply-demand curves for all specified hours with resume support.
        Reuses existing downloader and file reader components.

        Args:
            verbose: Print progress messages
            save_raw_data_path: Optional path to save raw .txt files
            skip_existing: If True, skip downloading files that already exist on disk
            read_from_disk: If True, read all files from disk without downloading

        Returns:
            pd.DataFrame: Combined data from all hours
        """
        all_dataframes = []

        if verbose:
            total_hours = len(self.hours)
            print(f"Fetching curves for {total_hours} hour(s) from {self.date_ini} to {self.date_end}")

        for i, hour in enumerate(self.hours, 1):
            if verbose:
                print(f"Processing hour {hour} ({i}/{len(self.hours)})")

            try:
                # Create downloader for this specific hour (reusing existing component)
                downloader = SupplyDemandCurveDownloader(hour=hour)

                # Create a temporary importer for this hour using existing architecture
                hour_importer = OMIEDataImporterFromResponses(
                    date_ini=self.date_ini,
                    date_end=self.date_end,
                    file_downloader=downloader,
                    file_reader=self.file_reader  # Reuse the same reader instance
                )

                # Get data for this hour using existing read_to_dataframe method with all parameters
                df_hour = hour_importer.read_to_dataframe(
                    verbose=False,
                    save_raw_data_path=save_raw_data_path,
                    skip_existing=skip_existing,
                    read_from_disk=read_from_disk
                )

                if not df_hour.empty:
                    # Add hour identifier to distinguish between different hours
                    df_hour = df_hour.copy()
                    df_hour['HOUR'] = hour
                    all_dataframes.append(df_hour)

            except Exception as e:
                if verbose:
                    print(f"Warning: Could not fetch data for hour {hour}: {str(e)}")
                continue

        if not all_dataframes:
            if verbose:
                print("No data was successfully retrieved")
            return pd.DataFrame()

        # Combine all dataframes
        combined_df = pd.concat(all_dataframes, ignore_index=True)

        # Sort by date and hour for consistency
        if 'DATE' in combined_df.columns and 'HOUR' in combined_df.columns:
            combined_df = combined_df.sort_values(['DATE', 'HOUR']).reset_index(drop=True)

        if verbose:
            print(f"Successfully retrieved {len(combined_df)} records for {len(self.hours)} hour(s)")

        return combined_df

    def read_to_dataframe_optimized(self, verbose: bool = False) -> pd.DataFrame:
        """
        "Optimized" version that minimizes object creation by reusing components more efficiently.
        """
        all_dataframes = []
        
        if verbose:
            print(f"Fetching curves for {len(self.hours)} hour(s) from {self.date_ini} to {self.date_end}")
        
        # Pre-create all downloaders to reuse
        downloaders = {hour: SupplyDemandCurveDownloader(hour=hour) for hour in self.hours}
        
        for i, hour in enumerate(self.hours, 1):
            if verbose:
                print(f"Processing hour {hour} ({i}/{len(self.hours)})")
                
            try:
                # Use pre-created downloader
                downloader = downloaders[hour]
                
                # Create temporary importer using existing architecture
                hour_importer = OMIEDataImporterFromResponses(
                    date_ini=self.date_ini,
                    date_end=self.date_end,
                    file_downloader=downloader,
                    file_reader=self.file_reader
                )
                
                df_hour = hour_importer.read_to_dataframe(verbose=False)
                
                if not df_hour.empty:
                    df_hour = df_hour.copy()
                    df_hour['HOUR'] = hour
                    all_dataframes.append(df_hour)
                    
            except Exception as e:
                if verbose:
                    print(f"Warning: Could not fetch data for hour {hour}: {str(e)}")
                continue
        
        if not all_dataframes:
            return pd.DataFrame()
        
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        
        if 'DATE' in combined_df.columns and 'HOUR' in combined_df.columns:
            combined_df = combined_df.sort_values(['DATE', 'HOUR']).reset_index(drop=True)
        
        if verbose:
            print(f"Successfully retrieved {len(combined_df)} records")
            
        return combined_df
    
# //////////////////////////////////////// Alternative approach ////////////////////////////////////////
# Extend the original importer directly
class OMIESupplyDemandCurvesMultiHourImporter:
    """
    Alternative approach: Composition over inheritance.
    Uses multiple instances of the original importer.
    """
    
    def __init__(self,
                 date_ini: dt.date,
                 date_end: dt.date,
                 hours: Optional[Union[int, List[int], str]] = "all"):
        
        self.date_ini = date_ini
        self.date_end = date_end  
        self.hours = self._parse_hours(hours)
    
    def _parse_hours(self, hours):
        """Same parsing logic as above"""
        if hours == "all":
            return list(range(1, 25))
        elif isinstance(hours, int):
            return [hours] if 1 <= hours <= 24 else []
        elif isinstance(hours, list):
            return [h for h in hours if isinstance(h, int) and 1 <= h <= 24]
        return []
    
    def read_to_dataframe(self, verbose: bool = False) -> pd.DataFrame:
        """
        Use composition: create multiple instances of original importer.
        This approach maintains compatibility with existing code.
        """
        from OMIEData.DataImport.omie_supply_demand_curve_importer import OMIESupplyDemandCurvesImporter
        
        all_dataframes = []
        
        for hour in self.hours:
            if verbose:
                print(f"Fetching data for hour {hour}")
                
            try:
                # Create original importer for each hour
                importer = OMIESupplyDemandCurvesImporter(
                    date_ini=self.date_ini,
                    date_end=self.date_end,
                    hour=hour
                )
                
                df_hour = importer.read_to_dataframe(verbose=False)
                
                if not df_hour.empty:
                    df_hour = df_hour.copy()
                    df_hour['HOUR'] = hour
                    all_dataframes.append(df_hour)
                    
            except Exception as e:
                if verbose:
                    print(f"Warning: Failed to fetch hour {hour}: {e}")
                continue
        
        if not all_dataframes:
            return pd.DataFrame()
            
        return pd.concat(all_dataframes, ignore_index=True)
    
    
# /////////////////////////////////////////////////////////////////////////////////////////////////
# Parallel Processing, draftv
 
# import concurrent.futures
# from concurrent.futures import ThreadPoolExecutor

# class OMIESupplyDemandCurvesAllHoursImporter:
#     def __init__(self, date_ini, date_end, hours=None, max_workers=4):
#         self.date_ini = date_ini
#         self.date_end = date_end
#         self.hours = hours or list(range(1, 25))
#         self.max_workers = max_workers
    
#     def _download_hour_data(self, hour):
#         """Download data for a single hour"""
#         importer = OMIESupplyDemandCurvesImporter(
#             date_ini=self.date_ini,
#             date_end=self.date_end,
#             hour=hour
#         )
#         df = importer.read_to_dataframe(verbose=False)
#         df['HOUR'] = hour
#         return df
    
#     def read_to_dataframe(self, verbose=True, parallel=True):
#         if parallel:
#             # Parallel download
#             with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
#                 future_to_hour = {
#                     executor.submit(self._download_hour_data, hour): hour 
#                     for hour in self.hours
#                 }
                
#                 all_dataframes = []
#                 for future in concurrent.futures.as_completed(future_to_hour):
#                     hour = future_to_hour[future]
#                     if verbose:
#                         print(f"Completed download for hour {hour}")
#                     all_dataframes.append(future.result())
#         else:
#             # Sequential download (existing approach)
#             all_dataframes = [self._download_hour_data(hour) for hour in self.hours]
        
#         return pd.concat(all_dataframes, ignore_index=True)