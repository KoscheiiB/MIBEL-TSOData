import datetime as dt
import requests as req

from OMIEData.Downloaders.general_omie_downloader import GeneralOMIEDownloader


class CurvaPBCDownloader(GeneralOMIEDownloader):
    """Day-ahead aggregated supply/demand curve, post 2025-10-01 quarter-hour market.

    OMIE replaced the legacy per-hour graphical file
    (``INT_CURVA_ACUM_UO_MIB_1_HH_DD_MM_YYYY_DD_MM_YYYY.TXT`` under
    ``/sites/default/files/dados/AGNO_YYYY/MES_MM/TXT/``) with a single file per day,
    ``curva_pbc_YYYYMMDD.v`` (v = version), served from a different endpoint:

        https://www.omie.es/es/file-download?parents=curva_pbc&filename=curva_pbc_YYYYMMDD.v

    The file holds all 96 quarter-hour periods (``Periodo`` = HnQn). Version is ``.1``
    on the normal publication and ``.2``+ only on a revision, so we probe ascending
    versions and take the first that resolves.
    """

    _download_url = 'https://www.omie.es/es/file-download?parents=curva_pbc&filename='
    _max_version = 5

    def __init__(self):
        # url_mask/output_mask are unused (we override URL building) but the base
        # ctor requires them; keep get_expected_filename working off output_mask.
        super().__init__(url_mask='', output_mask='curva_pbc_YYYYMMDD')

    def _stem(self, date: dt.datetime) -> str:
        return f'curva_pbc_{date.year:04d}{date.month:02d}{date.day:02d}'

    def get_expected_filename(self, date: dt.datetime) -> str:
        return self._stem(date) + '.1'

    def get_response_for_date(self, date: dt.datetime, verbose: bool = False) -> req.Response:
        stem = self._stem(date)
        last = None
        for v in range(1, self._max_version + 1):
            url = f'{self._download_url}{stem}.{v}'
            if verbose:
                print(f'Requesting {url} ...')
            last = req.get(url, allow_redirects=True)
            if last.status_code == 200:
                return last
        return last  # final 404 -> importer skips this date
