from enum import Enum, auto


class SystemType(Enum):

    SPAIN = 1
    PORTUGAL = 2
    IBERIAN = 9


class TechnologyType(Enum):

    COAL = auto()
    FUEL_GAS = auto()
    SELF_PRODUCER = auto()
    NUCLEAR = auto()
    HYDRO = auto()
    COMBINED_CYCLE = auto()
    WIND = auto()
    THERMAL_SOLAR = auto()
    PHOTOVOLTAIC_SOLAR = auto()
    RESIDUALS = auto()
    IMPORT = auto()
    IMPORT_WITHOUT_MIBEL = auto()

    __dict_concept_str__ = {COAL: ('COAL', 'CARBÓN'),
                            FUEL_GAS: ('FUEL_GAS', 'FUEL-GAS'),
                            SELF_PRODUCER: ('SELF_PRODUCER', 'AUTOPRODUCTOR'),
                            NUCLEAR: ('NUCLEAR', 'NUCLEAR'),
                            HYDRO: ('HYDRO', 'HIDRÁULICA'),
                            COMBINED_CYCLE: ('COMBINED_CYCLE', 'CICLO COMBINADO'),
                            WIND: ('WIND', 'EÓLICA'),
                            THERMAL_SOLAR: ('THERMAL_SOLAR', 'SOLAR TÉRMICA'),
                            PHOTOVOLTAIC_SOLAR: ('PHOTOVOLTAIC_SOLAR', 'SOLAR FOTOVOLTAICA'),
                            RESIDUALS: ('RESIDUALS', 'COGENERACIÓN/RESIDUOS/MINI HIDRA'),
                            IMPORT: ('IMPORT', 'IMPORTACIÓN INTER.'),
                            IMPORT_WITHOUT_MIBEL: ('IMPORT_WITHOUT_MIBEL', 'IMPORTACIÓN INTER. SIN MIBEL')}

    def __str__(self):
        return self.__dict_concept_str__[self.value][0]

    def name_in_file(self):
        return self.__dict_concept_str__[self.value][1]


class DataTypeInMarginalPriceFile(Enum):

    PRICE_SPAIN = auto()
    PRICE_PORTUGAL = auto()
    ENERGY_IBERIAN = auto()
    ENERGY_IBERIAN_WITH_BILLATERAL = auto()

    __dict_concept_str__ = {PRICE_SPAIN: 'PRICE_SP',
                            PRICE_PORTUGAL: 'PRICE_PT',
                            ENERGY_IBERIAN: 'ENER_IB',
                            ENERGY_IBERIAN_WITH_BILLATERAL: 'ENER_IB_BILLAT'}

    def __str__(self):
        return self.__dict_concept_str__[self.value]
    
class BorderType(Enum):
    """Border identifiers for cross-border exchanges with Spain."""
    PORTUGAL = 2
    FRANCE = 3
    MOROCCO = 5
    
    @classmethod
    def get_all_borders(cls):
        """Return all available border types."""
        return [cls.PORTUGAL, cls.FRANCE, cls.MOROCCO]
    
    def get_country_name(self):
        """Return the country name for display purposes."""
        country_names = {
            BorderType.PORTUGAL: "Portugal",
            BorderType.FRANCE: "France", 
            BorderType.MOROCCO: "Morocco"
        }
        return country_names.get(self, "Unknown")

class CommercialCapacityDataType(Enum):
    """Data types available in commercial capacities files."""
    IMPORT_CAPACITY = "IMPORT_CAPACITY"
    IMPORT_OCCUPATION = "IMPORT_OCCUPATION" 
    FREE_IMPORT_CAPACITY = "FREE_IMPORT_CAPACITY"
    EXPORT_CAPACITY = "EXPORT_CAPACITY"
    EXPORT_OCCUPATION = "EXPORT_OCCUPATION"
    FREE_EXPORT_CAPACITY = "FREE_EXPORT_CAPACITY"
    
class CapacityType(Enum):
    """Interconnection export capacity and occupation type - after market clearance (default) and after technical constraints/restrictions."""
    
    AFTER_MARKET_CLEARANCE = "market_clearance"
    AFTER_TECHNICAL_RESTRICTIONS = "technical_restrictions"
    
    def get_url_suffix(self):
        """Return the URL pattern suffix for each capacity type."""
        if self == CapacityType.AFTER_MARKET_CLEARANCE:
            return "INT_CAPACIDAD_INTER_D_BB_DD_MM_YYYY_DD_MM_YYYY.TXT"
        elif self == CapacityType.AFTER_TECHNICAL_RESTRICTIONS:
            return "INT_CAPACIDAD_INTER_D_PVP_BB_DD_MM_YYYY_DD_MM_YYYY.TXT"
    
    def get_description(self):
        """Human-readable description."""
        if self == CapacityType.AFTER_MARKET_CLEARANCE:
            return "Commercial Interconnection Capacities After Market Clearance"
        elif self == CapacityType.AFTER_TECHNICAL_RESTRICTIONS:
            return "Commercial Interconnection Capacities After Technical Restrictions"