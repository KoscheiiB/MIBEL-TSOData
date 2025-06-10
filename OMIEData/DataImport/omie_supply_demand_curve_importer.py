import datetime as dt
import pandas as pd

from OMIEData.DataImport.omie_data_importer_from_responses import OMIEDataImporterFromResponses
from OMIEData.Downloaders.supply_demand_curve_downloader import SupplyDemandCurveDownloader
from OMIEData.FileReaders.supply_demand_curve_file_reader import SupplyDemandCurvesReader


class OMIESupplyDemandCurvesImporter(OMIEDataImporterFromResponses):

    def __init__(self,
                 date_ini: dt.date,
                 date_end: dt.date,
                 hour: int):

        super().__init__(date_ini=date_ini,
                         date_end=date_end,
                         file_downloader=SupplyDemandCurveDownloader(hour=hour),
                         file_reader=SupplyDemandCurvesReader())

    def read_to_dataframe(self, verbose=False) -> pd.DataFrame:

        df = super().read_to_dataframe(verbose=verbose)
        #TODO: we have process the data-frame to generate another in a better format.
        #NOTE: See comments below,
        return df

# /////////////////////////////////////////////////////////////////////////////////////////////////
# Ideas for output's "better format" to-do above
# next steps ideas: maybe add methods for plotting, overall statistics  (# of bid and capacity offered, clearing prices, ...)
# def transform_supply_demand_data(df):
#     """
#     Transform and clean the supply-demand curve data for better analysis
#     """
#     if df is None or df.empty:
#         print("No data to transform")
#         return None
    
#     # Create a copy to avoid modifying original data
#     df_clean = df.copy()
    
#     # Convert DATE to datetime
#     df_clean['DATE'] = pd.to_datetime(df_clean['DATE'], format='%d/%m/%Y')
    
#     # Create a proper datetime column combining date and hour
#     df_clean['DATETIME'] = df_clean['DATE'] + pd.to_timedelta(df_clean['HOUR'] - 1, unit='h')
    
#     # Clean and standardize the data
#     df_clean['OFFER_TYPE_DESC'] = df_clean['OFFER_TYPE'].map({
#         'C': 'Buy/Demand',
#         'V': 'Sell/Supply'
#     })
    
#     # Add cumulative energy for curve construction
#     df_clean = df_clean.sort_values(['DATE', 'HOUR', 'OFFER_TYPE', 'PRICE'])
    
#     # Calculate cumulative energy for each curve
#     df_clean['CUMULATIVE_ENERGY'] = df_clean.groupby(['DATE', 'HOUR', 'OFFER_TYPE'])['ENERGY'].cumsum()
    
#     # Add matched status description
#     df_clean['MATCHED_DESC'] = df_clean['MATCHED'].map({
#         'O': 'Out of Market',
#         'C': 'In Market/Matched'
#     })
    
#     return df_clean

# def create_supply_demand_curves(df_clean, target_date, target_hour):
#     """
#     Create supply and demand curves for visualization
#     """
#     # Filter for specific date and hour
#     mask = (df_clean['DATE'] == pd.to_datetime(target_date)) & (df_clean['HOUR'] == target_hour)
#     hour_data = df_clean[mask].copy()
    
#     if hour_data.empty:
#         print(f"No data found for {target_date} hour {target_hour}")
#         return None, None
    
#     # Separate supply and demand
#     supply_data = hour_data[hour_data['OFFER_TYPE'] == 'V'].copy()
#     demand_data = hour_data[hour_data['OFFER_TYPE'] == 'C'].copy()
    
#     # Sort for proper curve construction
#     supply_data = supply_data.sort_values('PRICE')
#     demand_data = demand_data.sort_values('PRICE', ascending=False)
    
#     # Reset cumulative energy calculation for cleaner curves
#     supply_data['CUMULATIVE_ENERGY'] = supply_data['ENERGY'].cumsum()
#     demand_data['CUMULATIVE_ENERGY'] = demand_data['ENERGY'].cumsum()
    
#     return supply_data, demand_data