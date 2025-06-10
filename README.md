# MIBEL-TSOData: 
  
Based (and forked) on ![OMIEData](https://github.com/acruzgarcia/OMIEData/) python package to import data from OMIE (Iberian Peninsula's Electricity Market Operator): https://www.omie.es/.
Code repository serves the purpose of hosting different features and functionalities ideas, built on top of OMIEData's architecturally-sound and good practices and its structure (i.e., attempting to fully integrated within the package's eisting architecture). Besides the previously-developed functionalities, this repository includes:
- An upgrade to the Class responsible for downloading supply/demand curves, enabling flexible multi-hour queries (OMIESupplyDemandCurvesExtendedImporter).
- New classes for extracting data on Spain’s interconnection capacity by border, with flexible multi-border support. This includes the entire process of data extraction (OMIECommercialCapacitiesImporter, CommercialCapacitiesDownloader, CommercialCapacitiesFileReader & necessary Enums)
Additionally,
- A draft integration with Spain’s TSO REE open API (via API wrapper), supporting only demand evolution queries for now.

A more detailed description of the contributions can be found [below](#descriptive-changes). 



## Examples:

Besides all OMIE's data extraction/download functionalities, this section includes examples of the extended functionalities:

Example on how to download supply/demand curves with the extended functionality (multi-hour flexible support):

```python
import datetime as dt
from OMIEData.DataImport.omie_supply_demand_curve_importer import OMIESupplyDemandCurvesImporter

dateIni = dt.datetime(2020, 6, 1)
dateEnd = dt.datetime(2020, 6, 1)
hour = 1

# Original example, using extended class:
# This can take time, it is downloading the files from the website..
df = OMIESupplyDemandCurvesExtendedImporter(date_ini=dateIni, date_end=dateEnd, hours=[1]).read_to_dataframe(verbose=True)
df.sort_values(by=['DATE', 'HOUR'], axis=0, inplace=True)
print(df)

# Query multi-hour flexible support, by default
df = OMIESupplyDemandCurvesExtendedImporter(date_ini=dateIni, date_end=dateEnd, hours='all').read_to_dataframe(verbose=True)
df.sort_values(by=['DATE', 'HOUR'], axis=0, inplace=True)
print(df)

# Query specific hours, via list
df = OMIESupplyDemandCurvesExtendedImporter(date_ini=dateIni, date_end=dateEnd, hours=[1, 12, 24]).read_to_dataframe(verbose=True)
df.sort_values(by=['DATE', 'HOUR'], axis=0, inplace=True)
print(df)
```
Accessing Spain's interconnection Import/Export capacities and occupation:
```python

# Import Spain's Interconnection Import/Export capacities and occupation for all borders, after market clearance
df = OMIECommercialCapacitiesImporter(date_ini=dateIni, date_end=dateEnd, borders='all', capacity_type=CapacityType.AFTER_MARKET_CLEARANCE)
df.sort_values(by=['DATE', 'HOUR'], axis=0, inplace=True)
print(df)
    
# Import Spain's Interconnection Import/Export capacities and occupation for Portugal and France, after technical constraints/restrictions
df = OMIECommercialCapacitiesImporter(date_ini=dateIni, date_end=dateEnd, borders=[BorderType.PORTUGAL, BorderType.FRANCE], capacity_type=CapacityType.AFTER_TECHNICAL_RESTRICTIONS)
df.sort_values(by=['DATE', 'HOUR'], axis=0, inplace=True)
print(df)
```

REE API Wrapper usage example:
```python
from ree_client import REEClient
from enums.all_enums import TimeAggregation, Region, Language

with REEClient(language=Language.ENGLISH) as client:
    # Get demand evolution data, for pensiular system
    df = client.demand.get_evolution(
        start_date="2024-01-01",
        end_date="2024-01-31",
        time_trunc=TimeAggregation.DAY,
        region=Region.PENINSULAR
    )
    print(df)
    
    # Get data for specific autonomous community
    # Note: sources impose that only monthly/yearly are available options for CCAAs
    df_cataluna = client.demand.get_evolution(
        start_date="2024-01-01", 
        end_date="2024-01-31",
        time_trunc=TimeAggregation.MONTH,  
        region=Region.CATALUNA
    )
    print(df)

    # Another approach can be a manual geo parameters approach, alternatively to using region
    df_manual = client.demand.get_evolution(
        start_date="2024-01-01",
        end_date="2024-01-31", 
        time_trunc=TimeAggregation.DAY,
        geo_limit=GeoLimit.PENINSULAR,
        geo_ids=8741
    )
    print(df)

```
#### Installation 

Not covered nor available


## Descriptive changes:

Acknowledging and considering the limitations of current contributions, they are:

1. **OMIEData**: Extend the OMIEData's python package functionalities and data sources, embbeding new contributions into the already existing architecture, "data flow", and data extraction pattern/process: User Request → Importer → Downloader → FileReader → DataFrame.
As such, contributions are:

***OMIESupplyDemandCurvesExtendedImporter***
Extends original demand supply curve importer to support multi-hour demand and supply curves query. Two distinct approaches were implemented, still to be validates/tested. Next steps are included.

***OMIECommercialCapacitiesImporter***
High-level importer for OMIE's commercial interconnection capacity data of Spain. The data includes import/export capacities, their occupation levels, and remaining free capacities for each hourly period after the day-ahead market auction process. This funcitonality provides flexible support across multiple cross-border connections (Portugal, France and Morocco) while also supporting flexible option of capacity type (after market clearance or after techincal contraints/restrictions). 

***OMIECommercialCapacitiesDownloader***
Handles the download of the capacity data detailed above. As part of the extraction process, the Downloader is reponsible to handle the construction of border- and category-specific URLs, using templated patterns and supports flexible broder control (e.g., only one, two/three, 'all') and data catalog category options ("After Market Clearance" or "Aftter Technical Constraints/Restrictions").

***OMIECommercialCapacitiesFileReader***
Extending from OMIEFileReader (and overwritting methods), it parses and processes commercial capacity data files from OMIE cross-border exchanges and capacities. The FileReader is responsible to parse the .txt files (available data sources from OMIE), returned by the requests. In line with other implementations, final version uses a simpler and less manual approach of capturing data (via read csv method *vs* manual idenfication of rows and columns and headers). Get formatted concepts and "metadata" information on the data collected.

2. **REE API**: Integrating 
Loosely inspired in [hectorespert's REE lib](https://github.com/hectorespert/ree), this API Wrapper is an ongoing project to provide a fully (programatically) accessible API wrapper to the [REE's open API](https://www.ree.es/en/datos/apidata) and all of its data catalog. For now, it is a working in progress as it only supports 'Demand''s category 'evolution' widget. It is structured in a multi-layered approach, with clear separations of actions at each level, in a widget-centric design. 

**folder** ***client***
Contains the low-level base client for all REE API's HTTP communications, and a "abstraction" layer to simplify verbose code to use Wrapper (when more widgets and categories are covered)
**folder** ***widgets***
Contains the widget classes, for each data category & widget combination. This approach was chosen so as each widget enum contains its own parameter validation rules for widget constraints; enable specialized methods for each.
**folder** ***exceptions***
Contains dedicated exceptions for the package layers
**folder** ***enums***
Contains all enums needed for parameters, validation, lists of possible values and respective attributes.
**folder** ***utils***
Contains all utilities implemented (e.g., response parsing, date validation and the respective error handling)

Moreover, it also provides support for all of the geographies available, fully integrated with all REE's geo_ids, includes proper response processing, enums-ensured parameter validation from source's data catalog conditions, parameter validation and error handling. Finally, a draft for a flexible interface is included (see below)
```python
# High-level convenience methods
df = client.demand.get_evolution(start_date, end_date, TimeAggregation.DAY)

# Lower-level control
df = client.demand.get_data(DemandWidget.EVOLUTION, start_date, end_date, TimeAggregation.DAY)
```

Additional consideration for the inclusion of error handling, provided scripts for usage example, suggestions for resolving upstream TODO, pontential different approaches/avenues to a problems  (e.g., OMIESupplyDemandCurvesExtendedImporter), for each functionality, next steps in specific files, and the recquired documentation throughout the repo.


## Next steps:
Ideas fot future implementation and developments of repo:
- [x] Draft OMIEData package extension
- [x] Draft REE API wrapper
- [ ] Unit tests coverage
- [ ] Integrate REN PT-TSO data sources
- [ ] Progressively cover entire OMIE's data catalog
- [ ] Progressively cover entire REE's data catalog
