from enum import Enum
from typing import Dict, Optional

class Language(Enum):
    SPANISH = "es"
    ENGLISH = "en"

class TimeAggregation(Enum):
    HOUR = "hour"
    DAY = "day"
    MONTH = "month"
    YEAR = "year"

class Region(Enum):
    """REE geographical regions with their geo_ids and geo_limits"""
    # System level regions
    PENINSULAR = ("peninsular", 8741, "peninsular")
    CANARIAS = ("canarias", 8742, "ccaa")
    BALEARES = ("baleares", 8743, "ccaa")
    CEUTA = ("ceuta", 8744, "ccaa")
    MELILLA = ("melilla", 8745, "ccaa")
    
    # Autonomous Communities
    ANDALUCIA = ("Andalucía", 4, "ccaa")
    ARAGON = ("Aragón", 5, "ccaa")
    CANTABRIA = ("Cantabria", 6, "ccaa")
    CASTILLA_LA_MANCHA = ("Castilla la Mancha", 7, "ccaa")
    CASTILLA_Y_LEON = ("Castilla y León", 8, "ccaa")
    CATALUNA = ("Cataluña", 9, "ccaa")
    PAIS_VASCO = ("País Vasco", 10, "ccaa")
    ASTURIAS = ("Principado de Asturias", 11, "ccaa")
    CEUTA_CCAA = ("Comunidad de Ceuta", 8744, "ccaa")
    MELILLA_CCAA = ("Comunidad de Melilla", 8745, "ccaa")
    MADRID = ("Comunidad de Madrid", 13, "ccaa")
    NAVARRA = ("Comunidad de Navarra", 14, "ccaa")
    VALENCIA = ("Comunidad Valenciana", 15, "ccaa")
    EXTREMADURA = ("Extremadura", 16, "ccaa")
    GALICIA = ("Galicia", 17, "ccaa")
    BALEARES_CCAA = ("Islas Baleares", 8743, "ccaa")
    CANARIAS_CCAA = ("Islas Canarias", 8742, "ccaa")
    LA_RIOJA = ("La Rioja", 20, "ccaa")
    MURCIA = ("Región de Murcia", 21, "ccaa")

    
    def __init__(self, display_name: str, geo_id: int, geo_limit: str):
        self.display_name = display_name
        self.geo_id = geo_id
        self.geo_limit = geo_limit
    
    @property
    def is_peninsular(self) -> bool:
        """Check if region is peninsular (default national scope)"""
        return self == Region.PENINSULAR
    
    @property
    def is_system_level(self) -> bool:
        """Check if region is system-level (islands + peninsular)"""
        return self in [Region.PENINSULAR, Region.CANARIAS, Region.BALEARES, 
                       Region.CEUTA, Region.MELILLA]
    
    @property
    def requires_geo_params(self) -> bool:
        """Check if region requires geo parameters in API call"""
        return not self.is_peninsular
    
    @classmethod
    def get_by_geo_id(cls, geo_id: int) -> Optional['Region']:
        """Get region by geo_id"""
        for region in cls:
            if region.geo_id == geo_id:
                return region
        return None
    

class GeoLimit(Enum):
    PENINSULAR = "peninsular"
    CANARIAS = "canarias"
    BALEARES = "baleares"
    CEUTA = "ceuta"
    MELILLA = "melilla"
    CCAA = "ccaa"  # Autonomous communities

class Category(Enum):
    DEMAND = "demanda"
    GENERATION = "generacion"
    BALANCE = "balance"

class DemandWidget(Enum):
    """Available demand widgets"""
    EVOLUCION = "evolucion"
    VARIACION_COMPONENTES = "variacion-componentes"
    VARIACION_INTERANUAL = "variacion-interanual"
    IRE_GENERAL = "ire-general"
    # ...
    
