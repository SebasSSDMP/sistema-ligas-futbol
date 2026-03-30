from .connection import DatabaseConnection, get_db
from .repositories import (
    LigaRepository,
    TemporadaRepository,
    EquipoRepository,
    PartidoRepository,
)
from .estadisticas import (
    calcular_promedio_goles_por_liga,
    contar_partidos_mas_3_goles,
    contar_partidos_menor_igual_3_goles,
    ranking_ligas_por_promedio_goles,
    obtener_estadisticas_liga,
)

__all__ = [
    "DatabaseConnection",
    "get_db",
    "LigaRepository",
    "TemporadaRepository",
    "EquipoRepository",
    "PartidoRepository",
    "calcular_promedio_goles_por_liga",
    "contar_partidos_mas_3_goles",
    "contar_partidos_menor_igual_3_goles",
    "ranking_ligas_por_promedio_goles",
    "obtener_estadisticas_liga",
]
