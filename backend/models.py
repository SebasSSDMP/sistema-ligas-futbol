from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import date, datetime


class LigaBase(BaseModel):
    nombre: str
    pais: Optional[str] = None


class LigaCreate(LigaBase):
    pass


class LigaUpdate(BaseModel):
    nombre: str
    pais: Optional[str] = None


class Liga(LigaBase):
    id: int

    class Config:
        from_attributes = True


class TemporadaBase(BaseModel):
    nombre: str
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    liga_id: int


class TemporadaCreate(TemporadaBase):
    pass


class Temporada(TemporadaBase):
    id: int

    class Config:
        from_attributes = True
        json_encoders = {date: lambda v: v.isoformat() if v else None}


class EquipoBase(BaseModel):
    nombre: str
    liga_id: int


class EquipoCreate(EquipoBase):
    pass


class EquipoUpdate(BaseModel):
    nombre: str
    liga_id: Optional[int] = None


class Equipo(EquipoBase):
    id: int

    class Config:
        from_attributes = True


class PartidoBase(BaseModel):
    fecha: Optional[date] = None
    equipo_local: int
    equipo_visitante: int
    goles_local: int = 0
    goles_visitante: int = 0
    arbitro: Optional[str] = None
    estadio: Optional[str] = None
    temporada_id: int


class PartidoCreate(PartidoBase):
    pass


class Partido(PartidoBase):
    id: int

    class Config:
        from_attributes = True
        json_encoders = {date: lambda v: v.isoformat() if v else None}


class EstadisticasLiga(BaseModel):
    liga_id: int
    promedio_goles: float
    total_partidos: int
    partidos_mas_3_goles: int
    partidos_menos_igual_3_goles: int


class RankingLiga(BaseModel):
    id: int
    nombre: str
    pais: Optional[str]
    promedio_goles: Optional[float]
    total_partidos: int


class LigaCache(BaseModel):
    id: int
    name: Optional[str] = None
    country: Optional[str] = None
    logo: Optional[str] = None
    season: Optional[int] = None

    class Config:
        from_attributes = True


class EquipoCache(BaseModel):
    id: int
    liga_id: Optional[int] = None
    name: Optional[str] = None
    logo: Optional[str] = None

    class Config:
        from_attributes = True


class PartidoCache(BaseModel):
    id: int
    equipo_local_id: Optional[int] = None
    equipo_visitante_id: Optional[int] = None
    fecha: Optional[str] = None
    jornada: Optional[str] = None
    goles_local: Optional[int] = None
    goles_visitante: Optional[int] = None
    estado: Optional[str] = None
    tiempo: Optional[int] = None
    liga_id: Optional[int] = None
    temporada: Optional[int] = None

    class Config:
        from_attributes = True


class CacheStatus(BaseModel):
    ligas_count: int
    equipos_count: int
    partidos_count: int
    cache_entries: Dict[str, Any]
    ttl_config: Dict[str, str]