
from OMIEData.Downloaders.general_omie_downloader import GeneralOMIEDownloader


class IntraDayPriceDownloader(GeneralOMIEDownloader):

    url_year = 'AGNO_YYYY'
    url_month = '/MES_MM/TXT/'
    url_name = 'INT_PIB_EV_H_1_SS_DD_MM_YYYY_DD_MM_YYYY.TXT'
    output_mask = 'PrecioIntra_SS_YYYYMMDD.txt'

    def __init__(self, session: int):

        self.session = session
        str_session = f'{session:01}'
        self.output_mask = self.output_mask.replace('SS', str_session)

        url1 = self.url_year + self.url_month + self.url_name
        url1 = url1.replace('SS', str_session)

        GeneralOMIEDownloader.__init__(self,
                                       url_mask=url1,
                                       output_mask=self.output_mask)

    def get_expected_filename(self, date) -> str:
        """Generate expected output filename for a given date, including session.

        Overrides parent to handle session-specific filename generation.
        Note: Session is already embedded in output_mask during __init__,
        so we just call parent's implementation.

        Args:
            date: Date to generate filename for

        Returns:
            Expected filename with session already substituted
        """
        # Session is already replaced in output_mask during __init__
        return super().get_expected_filename(date)
