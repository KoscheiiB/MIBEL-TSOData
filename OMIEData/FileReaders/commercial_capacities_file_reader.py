import datetime as dt
import pandas as pd
import locale
from requests import Response
from io import BytesIO
from OMIEData.FileReaders.omie_file_reader import OMIEFileReader
from OMIEData.Enums.all_enums import BorderType

# NEXT STEPS,
# 1. Incorporate upstream/downstream language parameter, controling language in "metada" and renamed columns.
class CommercialCapacitiesFileReader(OMIEFileReader):
    """Extending from OMIEFileReader, it parses and processes commercial capacity data files from OMIE cross-border exchanges.
    
    """
    # Define the column mapping
    _dict_column_mapping = {
        'Hora': 'HOUR',
        'Fecha': 'DATE',
        'Frontera': 'BORDER',
        'Capacidad importación': 'IMPORT_CAPACITY',
        'Ocupación Importación': 'IMPORT_OCCUPATION',
        'Capacidad libre de importación': 'FREE_IMPORT_CAPACITY',
        'Capacidad exportación': 'EXPORT_CAPACITY',
        'Ocupación exportación': 'EXPORT_OCCUPATION',
        'Capacidad libre de exportación': 'FREE_EXPORT_CAPACITY'
    }
    
    # Derive the key list from mapping + any computed columns
    __key_list_retrieve__ = list(_dict_column_mapping.values())
    
    # "metadata coverage" - include human readable and extra detailed info on the data read.
    __dic_static_concepts__ = {
        'IMPORT_CAPACITY': {'unit': 'MWh', 'description': 'Import capacity'},
        'IMPORT_OCCUPATION': {'unit': 'MWh', 'description': 'Import capacity occupation'},
        'FREE_IMPORT_CAPACITY': {'unit': 'MWh', 'description': 'Free import capacity'},
        'EXPORT_CAPACITY': {'unit': 'MWh', 'description': 'Export capacity'},
        'EXPORT_OCCUPATION': {'unit': 'MWh', 'description': 'Export capacity occupation'},
        'FREE_EXPORT_CAPACITY': {'unit': 'MWh', 'description': 'Free export capacity'},
    }

    
    @staticmethod
    def get_concepts_info():
        return CommercialCapacitiesFileReader.__dic_static_concepts__
    
    __dateFormatInFile__ = '%d/%m/%Y'
    
    def __init__(self, border_type: BorderType = None):
        """
        Initialize reader.
        
        Args:
            border_type: Expected border type (optional, will be detected from content)
        """
        self.expected_border_type = border_type
        
    
    def get_keys(self):
        return CommercialCapacitiesFileReader.__key_list_retrieve__
    
    def get_data_from_response(self, response: Response) -> pd.DataFrame:

        locale.setlocale(locale.LC_NUMERIC, "en_DK.UTF-8")
        return self._get_data_from_file_like(file_like=BytesIO(response.content))
    
    def _get_data_from_file_like(self, file_like) -> pd.DataFrame:
        """Parse using pandas built-in CSV functionality."""
        try:
            # Read CSV with pandas, skipping header rows
            df = pd.read_csv(file_like, sep=';', skiprows=2, header=0, encoding='latin-1', skipfooter=1, engine='python', decimal=',', thousands='.')
            
            # Rename columns using dictionary mapping
            df = df.rename(self._dict_column_mapping, axis=1)
            
            df = df[[x for x in self.get_keys()]]
            
            df = self._standardize_columns(df)
        
            return df
        except Exception as e:
            raise ValueError(f"Error parsing commercial capacities file: {str(e)}")
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """ Assert column types """

        # Type cast date column
        df['DATE'] = pd.to_datetime(df['DATE'], format='%d/%m/%Y')
        
        # Ensure proper data types
        numeric_columns = ['HOUR','IMPORT_CAPACITY', 'IMPORT_OCCUPATION', 'FREE_IMPORT_CAPACITY',
                        'EXPORT_CAPACITY', 'EXPORT_OCCUPATION', 'FREE_EXPORT_CAPACITY']
        
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        df['COUNTRY'] = df['BORDER'].apply(self._get_country_name)
        return df
    
    def _get_country_name(self, border_id):
        """Map border ID to country name."""
        try:
            border_type = BorderType(border_id)
            return border_type.get_country_name()
        except ValueError:
            return "Unknown"
        
    def print_concepts_info(self, detailed: bool = True):
        """Print formatted concepts information."""
        concepts = self.get_concepts_info()
        
        title = "Commercial Capacities Data Concepts"
            
        print("=" * len(title))
        print(title)
        print("=" * len(title))
        print()
        
        for key, info in concepts.items():
            unit_text = f" ({info['unit']})" if info['unit'] else ""
            print(f"• {key}{unit_text}: {info['description']}")
            if detailed:
                print()
        
        if not detailed:
            print()