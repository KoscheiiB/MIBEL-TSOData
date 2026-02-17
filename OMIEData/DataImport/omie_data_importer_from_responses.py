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

    def read_to_dataframe(self,
                          verbose: bool = False,
                          save_raw_data_path: Optional[str] = None,
                          skip_existing: bool = True,
                          read_from_disk: bool = False) -> pd.DataFrame:
        """
        Read data to DataFrame with support for resume and read-from-disk modes.

        Args:
            verbose: Print progress messages
            save_raw_data_path: Optional path to save/read raw .txt files. If provided, raw files
                               will be saved before processing. Path will be created if it doesn't exist.
            skip_existing: If True and save_raw_data_path is provided, skip downloading files that
                          already exist on disk and read them instead. Enables resume functionality.
            read_from_disk: If True, read all files from save_raw_data_path without making any HTTP
                           requests. Requires save_raw_data_path to be provided.

        Returns:
            pd.DataFrame: Processed data

        Raises:
            ValueError: If read_from_disk=True but save_raw_data_path is not provided
        """
        # Create directory if save path is provided
        if save_raw_data_path:
            os.makedirs(save_raw_data_path, exist_ok=True)
            if verbose:
                print(f'Raw data will be saved to: {save_raw_data_path}')

        # Mode 3: Read-only from disk
        if read_from_disk:
            if not save_raw_data_path:
                raise ValueError("save_raw_data_path required when read_from_disk=True")
            return self._read_from_local_files(save_raw_data_path, verbose)

        # Mode 1 & 2: Download (with optional skip)
        df = pd.DataFrame(columns=self.fileReader.get_keys())

        for date in self.fileDownloader._date_range(self.date_ini, self.date_end):
            expected_filename = self.fileDownloader.get_expected_filename(date)
            filepath = os.path.join(save_raw_data_path, expected_filename) if save_raw_data_path else None

            # Check if file exists and skip_existing is True
            if skip_existing and filepath and os.path.exists(filepath):
                if verbose:
                    print(f'File exists, reading from disk: {expected_filename}')
                try:
                    df = pd.concat([df, self.fileReader.get_data_from_file(filepath)], ignore_index=True)
                except Exception as exc:
                    print(f'Error reading local file {expected_filename}: {exc}')
                continue

            # Download file
            try:
                response = self.fileDownloader.get_response_for_date(date, verbose=verbose)

                # Check if the response is successful (status code 200)
                if response.status_code != 200:
                    if verbose:
                        print(f'Skipping {response.url} (HTTP {response.status_code})')
                    continue

                # Save raw data if path is provided
                if filepath:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)

                    if verbose:
                        print(f'Saved raw file: {expected_filename}')

                # Process response
                df = pd.concat([df, self.fileReader.get_data_from_response(response=response)], ignore_index=True)

                if verbose:
                    print(f'Url: {response.url} successfully processed')

            except Exception as exc:
                print(f'There was error processing date {date.strftime("%Y-%m-%d")}: {exc}')

        return df

    def _read_from_local_files(self, folder_path: str, verbose: bool) -> pd.DataFrame:
        """Read all .TXT files from local folder without downloading.

        Args:
            folder_path: Path to folder containing .TXT files
            verbose: Print progress messages

        Returns:
            pd.DataFrame: Processed data from local files
        """
        df = pd.DataFrame(columns=self.fileReader.get_keys())

        # List all .TXT files
        try:
            all_files = os.listdir(folder_path)
        except FileNotFoundError:
            print(f'Folder not found: {folder_path}')
            return df

        filenames = [f for f in all_files
                     if os.path.isfile(os.path.join(folder_path, f)) and f.upper().endswith('.TXT')]

        if verbose:
            print(f'Reading {len(filenames)} files from {folder_path}')

        for filename in sorted(filenames):
            filepath = os.path.join(folder_path, filename)
            try:
                df = pd.concat([df, self.fileReader.get_data_from_file(filepath)], ignore_index=True)
                if verbose:
                    print(f'Processed: {filename}')
            except Exception as exc:
                print(f'Error processing {filename}: {exc}')

        return df
