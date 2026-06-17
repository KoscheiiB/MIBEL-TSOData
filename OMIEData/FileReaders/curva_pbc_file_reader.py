import pandas as pd
from requests import Response
from io import BytesIO

from OMIEData.FileReaders.omie_file_reader import OMIEFileReader


class CurvaPBCReader(OMIEFileReader):
    """Reader for the post 2025-10-01 day-ahead aggregated curve file ``curva_pbc_*``.

    Header row (line 3): ``Periodo;Fecha;Pais;Unidad;Tipo Oferta;Potencia
    Compra/Venta;Precio Compra/Venta;Ofertada (O)/Casada (C);Tipología de Oferta``.

    Differences vs the legacy ``SupplyDemandCurvesReader`` (which read the per-hour
    ``Hora`` file): the period field is ``Periodo`` = ``HnQn`` (hour + quarter), the
    quantity column is ``Potencia`` (power, MW) instead of ``Energía``, and there is an
    extra ``Tipología de Oferta`` column. We emit HOUR + QUARTER (ints) so the caller can
    stamp a 15-minute timestamp; the quantity is exposed under ``ENERGY`` to match the
    existing curve schema (it is a power magnitude per quarter-hour).
    """

    def __init__(self):
        self._dict_column_concept = {'Periodo': 'PERIOD',
                                     'Fecha': 'DATE',
                                     'Pais': 'COUNTRY',
                                     'Unidad': 'UNIT',
                                     'Tipo Oferta': 'OFFER_TYPE',
                                     'Potencia Compra/Venta': 'ENERGY',
                                     'Precio Compra/Venta': 'PRICE',
                                     'Ofertada (O)/Casada (C)': 'MATCHED'}

    def get_keys(self) -> list:
        return ['DATE', 'HOUR', 'QUARTER', 'COUNTRY', 'UNIT', 'OFFER_TYPE',
                'ENERGY', 'PRICE', 'MATCHED']

    def get_data_from_response(self, response: Response) -> pd.DataFrame:
        return self._get_data_from_file_like(file_like=BytesIO(response.content))

    def get_data_from_file(self, filename: str) -> pd.DataFrame:
        return self._get_data_from_file_like(file_like=filename)

    def _get_data_from_file_like(self, file_like) -> pd.DataFrame:
        # decimal/thousands handled by read_csv (no locale.setlocale -> portable).
        df = pd.read_csv(file_like, sep=';', skiprows=2, header=0, encoding='latin-1',
                         skipfooter=1, engine='python', decimal=',', thousands='.')
        df = df.rename({k: v for k, v in self._dict_column_concept.items()}, axis=1)

        # Periodo "HnQn" -> HOUR (1..24) + QUARTER (1..4).
        period = df['PERIOD'].astype(str).str.extract(r'H(\d+)Q(\d+)')
        df['HOUR'] = pd.to_numeric(period[0], errors='coerce').astype('Int64')
        df['QUARTER'] = pd.to_numeric(period[1], errors='coerce').astype('Int64')

        return df[[x for x in self.get_keys() if x in df.columns]]
