import unicodedata
from io import BytesIO

import pandas as pd
from requests import Response

from OMIEData.FileReaders.omie_file_reader import OMIEFileReader
from OMIEData.Enums.all_enums import TechnologyType


def _strip_accents(s: str) -> str:
    """Remove accents/diacritics for accent-insensitive column matching."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


class EnergyByTechnologyHourlyFileReader(OMIEFileReader):

    def __init__(self, types=None):

        self.conceptsToLoad = [v for v in TechnologyType] if not types else types

        self._dict_column_concept = {'Fecha': 'DATE',
                                     'Hora': 'HOUR',
                                     'CARBÓN': 'COAL',
                                     'FUEL-GAS': 'FUEL_GAS',
                                     'AUTOPRODUCTOR': 'SELF_PRODUCER',
                                     'NUCLEAR': 'NUCLEAR',
                                     'HIDRÁULICA': 'HYDRO',
                                     'CICLO COMBINADO': 'COMBINED_CYCLE',
                                     'EÓLICA': 'WIND',
                                     'SOLAR TÉRMICA': 'THERMAL_SOLAR',
                                     'SOLAR FOTOVOLTAICA': 'PHOTOVOLTAIC_SOLAR',
                                     'COGENERACIÓN/RESIDUOS/MINI HIDRA': 'RESIDUALS',
                                     'IMPORTACIÓN INTER.': 'IMPORT',
                                     'IMPORTACIÓN INTER. SIN MIBEL': 'IMPORT_WITHOUT_MIBEL'}

    def get_keys(self) -> list:

        key_list_retrieve = ['DATE', 'HOUR']
        key_list_retrieve.extend([str(v) for v in self.conceptsToLoad])
        return key_list_retrieve

    def get_data_from_response(self, response: Response) -> pd.DataFrame:

        return self._get_data_from_file_like(file_like=BytesIO(response.content))

    def get_data_from_file(self, filename: str) -> pd.DataFrame:

        return self._get_data_from_file_like(file_like=filename)

    def _get_data_from_file_like(self, file_like) -> pd.DataFrame:

        # decimal/thousands handled by read_csv -> no locale.setlocale needed
        # (the old locale call failed on macOS/Linux).
        df = pd.read_csv(file_like, sep=';', skiprows=2, header=0, encoding='latin-1', skipfooter=1, engine='python',
                         decimal=",", thousands='.')

        # Drop trailing unnamed columns (created by a trailing ';' separator).
        df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

        # Accent-insensitive rename from the configured concepts, plus the newer
        # column names: 'Periodo' (quarter-hour) and the 2025+ technologies.
        norm_mapping = {_strip_accents(k).lower(): v for k, v in self._dict_column_concept.items()}
        norm_mapping["periodo"] = "HOUR"
        norm_mapping["almacenamiento"] = "STORAGE"
        norm_mapping["hibridacion"] = "HYBRIDIZATION"

        rename_map = {}
        for col in df.columns:
            col_norm = _strip_accents(col.strip()).lower()
            if col_norm in norm_mapping:
                rename_map[col] = norm_mapping[col_norm]
        df = df.rename(columns=rename_map)

        # From 2025-10-01 the period is expressed in quarter-hours (H1Q1..H24Q4). Each
        # value is the average power (MW) for that 15-minute slot, NOT additive energy, so
        # the reader preserves every period faithfully (the full 96/day) and does not
        # aggregate - collapsing to hourly is the consumer's choice (hourly MWh = mean of
        # the quarters). HOUR carries 1..24 and QUARTER 1..4.
        if "HOUR" in df.columns and not pd.api.types.is_numeric_dtype(df["HOUR"]):
            hour_match = df["HOUR"].astype(str).str.extract(r"H(\d+)Q(\d+)")
            if not hour_match.isna().all().all():
                df["HOUR"] = hour_match[0].astype(int)
                df["QUARTER"] = hour_match[1].astype(int)
                value_cols = [c for c in df.columns if c not in ("DATE", "HOUR", "QUARTER")]
                for vc in value_cols:
                    df[vc] = pd.to_numeric(df[vc], errors="coerce")

        # Keep the configured keys that are present, plus QUARTER (15-min files) and the
        # newer technologies.
        expected = [k for k in self.get_keys() if k in df.columns]
        if "QUARTER" in df.columns and "HOUR" in expected:
            expected.insert(expected.index("HOUR") + 1, "QUARTER")
        for extra in ("STORAGE", "HYBRIDIZATION"):
            if extra in df.columns and extra not in expected:
                expected.append(extra)
        df = df[expected]

        return df
