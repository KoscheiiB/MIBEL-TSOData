# This is a sample Python script.
import datetime as dt
from OMIEData.DataImport.omie_commercial_capacities_importer import OMIECommercialCapacitiesImporter
from OMIEData.Enums.all_enums import BorderType, CapacityType

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    dateIni = dt.datetime(2020, 6, 1)
    dateEnd = dt.datetime(2020, 6, 1)
    hour = 1

    
    
    # Import Spain's Interconnection Import/Export capacities and occupation for all borders, after market clearance
    df = OMIECommercialCapacitiesImporter(dateIni,dateEnd,borders='all', capacity_type=CapacityType.AFTER_MARKET_CLEARANCE)
    df.sort_values(by=['DATE', 'HOUR'], axis=0, inplace=True)
    print(df)
    
    # Import Spain's Interconnection Import/Export capacities and occupation for Portugal and France, after technical constraints/restrictions
    df = OMIECommercialCapacitiesImporter(dateIni,dateEnd, borders=[BorderType.PORTUGAL, BorderType.FRANCE], capacity_type=CapacityType.AFTER_TECHNICAL_RESTRICTIONS)
    df.sort_values(by=['DATE', 'HOUR'], axis=0, inplace=True)
    print(df)
    
    