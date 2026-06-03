"""Offline tests for the locale-free OMIE file readers.

These exercise the parsing fixes without any network access:
  - locale-free numeric parsing (safe_atof / _process_line)
  - energy-by-technology quarter-hour ('Periodo') aggregation + new techs
  - commercial-capacities accent-insensitive rename + Unnamed-column drop
  - supply/demand and energy legacy ('Hora') formats

All inputs are synthetic latin-1 CSV bytes shaped like real OMIE files:
two header rows (skiprows=2), the column header, data rows, one footer row
(skipfooter=1), and a trailing ';' that yields an Unnamed column.
"""
from io import BytesIO

import numpy as np
import pandas as pd

from OMIEData.Enums.all_enums import DataTypeInMarginalPriceFile
from OMIEData.FileReaders.marginal_price_file_reader import (
    MarginalPriceFileReader,
    safe_atof,
)
from OMIEData.FileReaders.energy_by_technology_files_reader import (
    EnergyByTechnologyHourlyFileReader,
)
from OMIEData.FileReaders.commercial_capacities_file_reader import (
    CommercialCapacitiesFileReader,
)
from OMIEData.FileReaders.supply_demand_curve_file_reader import (
    SupplyDemandCurvesReader,
)


def _latin1(text):
    return BytesIO(text.encode("latin-1"))


def test_safe_atof_european_format():
    assert safe_atof("1.234,56") == 1234.56
    assert safe_atof("12,5") == 12.5
    assert safe_atof("100") == 100.0
    assert safe_atof("-3,0") == -3.0


def test_marginal_process_line_is_locale_free():
    reader = MarginalPriceFileReader()
    concept = list(DataTypeInMarginalPriceFile)[0]
    values = [f"{h},5" for h in range(1, 25)]  # 24 hours: "1,5".."24,5"

    result = reader._process_line(date="2024-01-01", concept=concept, values=values)

    assert result["H1"] == 1.5
    assert result["H24"] == 24.5
    assert result["H25"] is None  # 24-hour day leaves H25 unset


def test_marginal_process_line_handles_short_day():
    reader = MarginalPriceFileReader()
    concept = list(DataTypeInMarginalPriceFile)[0]
    # 23 valid values then an unparseable 24th -> H24/H25 become NaN.
    values = [f"{h},0" for h in range(1, 24)] + ["-"]

    result = reader._process_line(date="2024-01-01", concept=concept, values=values)

    assert result["H23"] == 23.0
    assert np.isnan(result["H24"])
    assert np.isnan(result["H25"])


ENERGY_QUARTER_HOUR = (
    "OMIE energy by technology;;;;;;\n"
    "units MWh;;;;;;\n"
    "Fecha;Periodo;NUCLEAR;EÓLICA;ALMACENAMIENTO;HIBRIDACIÓN;\n"
    "01/01/2025;H1Q1;100;10;5;1;\n"
    "01/01/2025;H1Q2;100;10;5;1;\n"
    "01/01/2025;H2Q1;200;20;6;2;\n"
    "* footer line\n"
)


def test_energy_quarter_hour_aggregates_and_adds_new_techs():
    df = EnergyByTechnologyHourlyFileReader().get_data_from_file(_latin1(ENERGY_QUARTER_HOUR))

    assert "STORAGE" in df.columns
    assert "HYBRIDIZATION" in df.columns
    assert "Unnamed" not in "".join(df.columns)

    hour1 = df[df["HOUR"] == 1].iloc[0]
    assert hour1["NUCLEAR"] == 200  # 100 + 100 across quarter-hours
    assert hour1["WIND"] == 20
    assert hour1["STORAGE"] == 10
    assert hour1["HYBRIDIZATION"] == 2


ENERGY_HOURLY_LEGACY = (
    "OMIE energy by technology;;;\n"
    "units MWh;;;\n"
    "Fecha;Hora;NUCLEAR;EÓLICA;\n"
    "01/01/2024;1;100;10;\n"
    "01/01/2024;2;200;20;\n"
    "* footer line\n"
)


def test_energy_legacy_hourly_format_still_parses():
    df = EnergyByTechnologyHourlyFileReader().get_data_from_file(_latin1(ENERGY_HOURLY_LEGACY))
    assert list(df["HOUR"]) == [1, 2]
    assert df[df["HOUR"] == 1].iloc[0]["NUCLEAR"] == 100


# Header without the accent on 'importacion' to prove accent-insensitive matching.
COMMERCIAL = (
    "OMIE commercial capacities;;;;;;;;;\n"
    "border ES-FR;;;;;;;;;\n"
    "Fecha;Hora;Frontera;Capacidad importacion;Ocupación Importación;"
    "Capacidad libre de importación;Capacidad exportación;Ocupación exportación;"
    "Capacidad libre de exportación;\n"
    "01/01/2024;1;ES-FR;1.000,5;100,0;900,5;2.000,0;200,0;1.800,0;\n"
    "* footer line\n"
)


def test_commercial_capacities_accent_insensitive_and_drops_unnamed():
    df = CommercialCapacitiesFileReader()._get_data_from_file_like(_latin1(COMMERCIAL))

    assert "Unnamed" not in "".join(df.columns)
    assert "IMPORT_CAPACITY" in df.columns  # matched despite missing accent
    row = df.iloc[0]
    assert row["HOUR"] == 1
    assert row["IMPORT_CAPACITY"] == 1000.5
    assert "COUNTRY" in df.columns


SUPPLY_DEMAND = (
    "OMIE supply demand curve;;;;;;;\n"
    "units;;;;;;;\n"
    "Fecha;Hora;Pais;Unidad;Tipo Oferta;Energía Compra/Venta;Precio Compra/Venta;Ofertada (O)/Casada (C)\n"
    "01/01/2024;1;ES;U1;C;1.234,5;50,25;O\n"
    "* footer line\n"
)


def test_supply_demand_curves_locale_free():
    df = SupplyDemandCurvesReader().get_data_from_file(_latin1(SUPPLY_DEMAND))
    row = df.iloc[0]
    assert row["ENERGY"] == 1234.5
    assert row["PRICE"] == 50.25
    assert row["COUNTRY"] == "ES"
