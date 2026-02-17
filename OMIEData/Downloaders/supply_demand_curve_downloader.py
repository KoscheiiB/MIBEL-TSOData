
from OMIEData.Downloaders.general_omie_downloader import GeneralOMIEDownloader


class SupplyDemandCurveDownloader(GeneralOMIEDownloader):

    url_year = 'AGNO_YYYY'
    url_month = '/MES_MM/TXT/'
    url_name = 'INT_CURVA_ACUM_UO_MIB_1_HH_DD_MM_YYYY_DD_MM_YYYY.TXT'
    output_mask = 'OfferAndDemandCurve_HH_YYYYMMDD.txt'

    def __init__(self, hour: int):

        self.hour = hour
        str_hour = f'{hour:01}'
        self.output_mask = self.output_mask.replace('HH', str_hour)

        url1 = self.url_year + self.url_month + self.url_name
        url1 = url1.replace('HH', str_hour)

        GeneralOMIEDownloader.__init__(self, url_mask=url1, output_mask=self.output_mask)

    def get_expected_filename(self, date) -> str:
        """Generate expected output filename for a given date, including hour.

        Overrides parent to handle hour-specific filename generation.
        Note: Hour is already embedded in output_mask during __init__,
        so we just call parent's implementation.

        Args:
            date: Date to generate filename for

        Returns:
            Expected filename with hour already substituted
        """
        # Hour is already replaced in output_mask during __init__
        return super().get_expected_filename(date)
