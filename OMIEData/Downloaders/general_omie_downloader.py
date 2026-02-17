
import requests as req
import datetime as dt
import os
from OMIEData.Downloaders.omie_downloader import OMIEDownloader


class GeneralOMIEDownloader(OMIEDownloader):

    _base_url = 'https://www.omie.es/sites/default/files/dados/'
    url_mask: str
    output_folder: str
    output_mask: str

    def __init__(self, url_mask: str, output_mask: str):

        self.url_mask = url_mask
        self.output_mask = output_mask

    def get_complete_url(self) -> str:
        return self._base_url + self.url_mask

    def download_data(self, date_ini: dt.datetime, date_end: dt.datetime, output_folder: str, verbose=False) -> int:

        error = 0
        dt_aux = date_ini

        while dt_aux <= date_end:

            dd = f'{dt_aux.day:02}'
            mm = f'{dt_aux.month:02}'
            yyyy = f'{dt_aux.year:04}'

            # There could be errors when downloading or writtng to file... try-catch ??
            url_aux = self.get_complete_url()
            url_aux = url_aux.replace('DD', dd).replace('MM', mm).replace('YYYY', yyyy)

            file_aux = self.output_mask.replace('DD', dd).replace('MM', mm).replace('YYYY', yyyy)
            file_aux = os.path.join(output_folder, file_aux)

            if verbose:
                print('Downloading {} ...'.format(url_aux))
            response = req.get(url_aux, allow_redirects=True)

            if verbose:
                print('Copying to {} ...'.format(file_aux))
            f = open(file_aux, 'wb').write(response.content)

            dt_aux = dt_aux + dt.timedelta(days=+1)

        return error

    def get_expected_filename(self, date: dt.datetime) -> str:
        """Generate expected output filename for a given date without downloading.

        Args:
            date: Date to generate filename for

        Returns:
            Expected filename based on output_mask pattern
        """
        dd = f'{date.day:02d}'
        mm = f'{date.month:02d}'
        yyyy = f'{date.year:04d}'

        filename = self.output_mask
        filename = filename.replace('DD', dd)
        filename = filename.replace('MM', mm)
        filename = filename.replace('YYYY', yyyy)

        return filename

    def get_response_for_date(self, date: dt.datetime, verbose: bool = False) -> req.Response:
        """Get HTTP response for a single date.

        Args:
            date: Date to download data for
            verbose: Print progress messages

        Returns:
            HTTP Response object
        """
        dd = f'{date.day:02d}'
        mm = f'{date.month:02d}'
        yyyy = f'{date.year:04d}'

        url = self.get_complete_url()
        url = url.replace('DD', dd).replace('MM', mm).replace('YYYY', yyyy)

        if verbose:
            print(f'Requesting {url} ...')

        return req.get(url, allow_redirects=True)

    def _date_range(self, start: dt.datetime, end: dt.datetime):
        """Generate dates from start to end (inclusive).

        Args:
            start: Start date
            end: End date

        Yields:
            datetime objects for each day in range
        """
        current = start
        while current <= end:
            yield current
            current += dt.timedelta(days=1)

    def url_responses(self, date_ini: dt.datetime, date_end: dt.datetime, verbose=False):

        dt_aux = date_ini

        while dt_aux <= date_end:

            dd = f'{dt_aux.day:02}'
            mm = f'{dt_aux.month:02}'
            yyyy = f'{dt_aux.year:04}'

            # There could be errors when downloading or writing to file... try-catch ??
            url_aux = self.get_complete_url()
            url_aux = url_aux.replace('DD', dd).replace('MM', mm).replace('YYYY', yyyy)

            if verbose:
                print('Requesting {} ...'.format(url_aux))

            yield req.get(url_aux, allow_redirects=True)

            dt_aux = dt_aux + dt.timedelta(days=+1)
