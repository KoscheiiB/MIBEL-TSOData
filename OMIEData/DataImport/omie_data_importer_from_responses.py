import pandas as pd
import datetime as dt
import os
from typing import Optional

from OMIEData.DataImport.omie_data_importer import OMIEDataImporter
from OMIEData.FileReaders.omie_file_reader import OMIEFileReader
from OMIEData.Downloaders.omie_downloader import OMIEDownloader


class OMIEDataImporterFromResponses(OMIEDataImporter):

    def __init__(self,
                 date_ini: dt.date,
                 date_end: dt.date,
                 file_downloader: OMIEDownloader,
                 file_reader: OMIEFileReader):

        self.fileDownloader = file_downloader
        self.fileReader = file_reader
        self.date_ini = date_ini
        self.date_end = date_end

    def read_to_dataframe(self, verbose=False, save_raw_data_path: Optional[str] = None) -> pd.DataFrame:
        """
        Read data to DataFrame, optionally saving raw downloaded files to disk.

        Args:
            verbose: Print progress messages
            save_raw_data_path: Optional path to save raw .txt files. If provided, raw files
                               will be saved before processing. Path will be created if it doesn't exist.

        Returns:
            pd.DataFrame: Processed data
        """
        # Create directory if save path is provided
        if save_raw_data_path:
            os.makedirs(save_raw_data_path, exist_ok=True)
            if verbose:
                print(f'Raw data will be saved to: {save_raw_data_path}')

        df = pd.DataFrame(columns=self.fileReader.get_keys())
        for response in self.fileDownloader.url_responses(date_ini=self.date_ini,
                                                          date_end=self.date_end,
                                                          verbose=verbose):
            try:
                # Check if the response is successful (status code 200)
                if response.status_code != 200:
                    if verbose:
                        print(f'Skipping {response.url} (HTTP {response.status_code})')
                    continue

                # Save raw data if path is provided
                if save_raw_data_path:
                    # Extract filename from URL (last part after /)
                    filename = response.url.split('/')[-1]
                    filepath = os.path.join(save_raw_data_path, filename)

                    with open(filepath, 'wb') as f:
                        f.write(response.content)

                    if verbose:
                        print(f'Saved raw file: {filename}')

                df = pd.concat([df, self.fileReader.get_data_from_response(response=response)], ignore_index=True)

            except Exception as exc:
                print('There was error processing file: ' + response.url)
                print('{}'.format(exc) + response.url)
            else:
                if verbose:
                    print('Url: ' + response.url + ' successfully processed')

        return df
