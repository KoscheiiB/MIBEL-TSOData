import datetime as dt
import unicodedata
import pandas as pd
from requests import Response
from io import BytesIO
from OMIEData.FileReaders.omie_file_reader import OMIEFileReader
from OMIEData.Enums.all_enums import BorderType


def _strip_accents(s: str) -> str:
    """Remove accents/diacritics for accent-insensitive column matching."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )

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

        return self._get_data_from_file_like(file_like=BytesIO(response.content))

    def get_data_from_file(self, filename: str) -> pd.DataFrame:
        """Read and parse data from a local file.

        Parsing is locale-free (pandas decimal/thousands handling in
        _get_data_from_file_like), so no locale juggling is needed.

        Args:
            filename: Path to the .txt file to read

        Returns:
            pd.DataFrame: Parsed commercial capacities data
        """
        with open(filename, 'rb') as f:
            return self._get_data_from_file_like(file_like=BytesIO(f.read()))
    
    def _get_data_from_file_like(self, file_like) -> pd.DataFrame:
        """Parse using pandas built-in CSV functionality."""
        try:
            # Read CSV with pandas, skipping header rows
            df = pd.read_csv(file_like, sep=';', skiprows=2, header=0, encoding='latin-1', skipfooter=1, engine='python', decimal=',', thousands='.')

            # Drop trailing unnamed columns (created by a trailing ';' separator).
            df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

            # Accent-insensitive rename so headers like 'Capacidad importacion'
            # match regardless of how accents survive the latin-1 decode.
            norm_mapping = {_strip_accents(k).lower(): v for k, v in self._dict_column_mapping.items()}
            rename_map = {}
            for col in df.columns:
                col_norm = _strip_accents(col.strip()).lower()
                if col_norm in norm_mapping:
                    rename_map[col] = norm_mapping[col_norm]
            df = df.rename(columns=rename_map)

            # Handle missing HOUR column (period-aggregated files carry 'Periodo'
            # instead); avoids a KeyError downstream in _standardize_columns.
            if 'HOUR' not in df.columns and 'Periodo' in df.columns:
                df = df.rename({'Periodo': 'HOUR'}, axis=1)
            elif 'HOUR' not in df.columns:
                df['HOUR'] = pd.NA

            # From 2025-10-01 the period is quarter-hourly (H1Q1..H24Q4). Split it into
            # numeric HOUR (1..24) + QUARTER (1..4) so the period is not lost to the
            # numeric coercion in _standardize_columns; legacy hourly files have no Q.
            if 'HOUR' in df.columns and df['HOUR'].astype(str).str.contains('Q', na=False).any():
                hq = df['HOUR'].astype(str).str.extract(r"H(\d+)Q(\d+)")
                df['HOUR'] = hq[0]
                df['QUARTER'] = hq[1]

            keep = [x for x in self.get_keys() if x in df.columns]
            if 'QUARTER' in df.columns:
                keep.append('QUARTER')
            df = df[keep]

            df = self._standardize_columns(df)

            return df
        except Exception as e:
            raise ValueError(f"Error parsing commercial capacities file: {str(e)}")
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """ Assert column types """

        # Type cast date column
        df['DATE'] = pd.to_datetime(df['DATE'], format='%d/%m/%Y')

        # Ensure proper data types
        numeric_columns = ['HOUR', 'IMPORT_CAPACITY', 'IMPORT_OCCUPATION', 'FREE_IMPORT_CAPACITY',
                        'EXPORT_CAPACITY', 'EXPORT_OCCUPATION', 'FREE_EXPORT_CAPACITY']

        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        if 'QUARTER' in df.columns:
            df['QUARTER'] = pd.to_numeric(df['QUARTER'], errors='coerce')
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