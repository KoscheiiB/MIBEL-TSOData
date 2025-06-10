# This is a sample Python script.
import datetime as dt
from OMIEData.DataImport.omie_supply_demand_curve_importer_extended import OMIESupplyDemandCurvesExtendedImporter

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    dateIni = dt.datetime(2020, 6, 1)
    dateEnd = dt.datetime(2020, 6, 1)
    hour = 1

    
    
    # Query with multi-hour flexible support ('all' by default9)
    df = OMIESupplyDemandCurvesExtendedImporter(date_ini=dateIni, date_end=dateEnd, hours='all').read_to_dataframe(verbose=True)
    df.sort_values(by=['DATE', 'HOUR'], axis=0, inplace=True)
    print(df)
    
    # Query specific hours, via list
    df = OMIESupplyDemandCurvesExtendedImporter(date_ini=dateIni, date_end=dateEnd, hours=[1, 12, 24]).read_to_dataframe(verbose=True)
    df.sort_values(by=['DATE', 'HOUR'], axis=0, inplace=True)
    print(df)
    
    # Original example (example_supply_demand_curves_on_the_fly.py), after update
    # This can take time, it is downloading the files from the website..
    df = OMIESupplyDemandCurvesExtendedImporter(date_ini=dateIni, date_end=dateEnd, hours=[1]).read_to_dataframe(verbose=True)    
    df.sort_values(by=['DATE', 'HOUR'], axis=0, inplace=True)
    print(df)
