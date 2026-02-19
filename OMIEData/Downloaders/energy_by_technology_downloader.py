
from OMIEData.Downloaders.general_omie_downloader import GeneralOMIEDownloader
from OMIEData.Enums.all_enums import SystemType


class EnergyByTechnologyDownloader(GeneralOMIEDownloader):

    url_year = 'AGNO_YYYY'
    url_month = '/MES_MM/TXT/'
    url_name = 'INT_PBC_TECNOLOGIAS_H_SYS_DD_MM_YYYY_DD_MM_YYYY.TXT'
    output_mask = 'omie_EnergyByTechnology_SYS_YYYYMMDD.txt'

    def __init__(self, system: SystemType):

        self.system = system
        str_system = f'{system.value:01}'
        self.output_mask = self.output_mask.replace('SYS', str_system)

        url1 = self.url_year + self.url_month + self.url_name
        url1 = url1.replace('SYS', str_system)

        GeneralOMIEDownloader.__init__(self,
                                       url_mask=url1,
                                       output_mask=self.output_mask)

    def get_expected_filename(self, date) -> str:
        """Generate expected output filename for a given date, including system type.

        Overrides parent to handle system-specific filename generation.
        Note: System type is already embedded in output_mask during __init__,
        so we just call parent's implementation.

        Args:
            date: Date to generate filename for

        Returns:
            Expected filename with system type already substituted
        """
        # System type is already replaced in output_mask during __init__
        return super().get_expected_filename(date)
