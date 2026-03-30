from typing import List, Dict, Any
from database.connection import get_db


def calcular_promedio_goles_por_liga(liga_id: int) -> float:
    db = get_db()
    cursor = db.get_connection().cursor()
    cursor.execute(
        """
        SELECT 
            AVG(p.goles_local + p.goles_visitante) as promedio
        FROM partidos p
        JOIN temporadas t ON p.temporada_id = t.id
        WHERE t.liga_id = ? AND p.goles_local IS NOT NULL
        """,
        (liga_id,),
    )
    resultado = cursor.fetchone()
    return resultado["promedio"] if resultado["promedio"] else 0.0


def contar_partidos_mas_3_goles(liga_id: int) -> int:
    db = get_db()
    cursor = db.get_connection().cursor()
    cursor.execute(
        """
        SELECT COUNT(*) as total
        FROM partidos p
        JOIN temporadas t ON p.temporada_id = t.id
        WHERE t.liga_id = ? AND (p.goles_local + p.goles_visitante) > 3
        """,
        (liga_id,),
    )
    return cursor.fetchone()["total"]


def contar_partidos_menor_igual_3_goles(liga_id: int) -> int:
    db = get_db()
    cursor = db.get_connection().cursor()
    cursor.execute(
        """
        SELECT COUNT(*) as total
        FROM partidos p
        JOIN temporadas t ON p.temporada_id = t.id
        WHERE t.liga_id = ? AND (p.goles_local + p.goles_visitante) <= 3
        """,
        (liga_id,),
    )
    return cursor.fetchone()["total"]


def ranking_ligas_por_promedio_goles() -> List[Dict[str, Any]]:
    db = get_db()
    cursor = db.get_connection().cursor()
    cursor.execute(
        """
        SELECT 
            l.id,
            l.nombre,
            l.pais,
            AVG(p.goles_local + p.goles_visitante) as promedio_goles,
            COUNT(p.id) as total_partidos
        FROM ligas l
        LEFT JOIN temporadas t ON t.liga_id = l.id
        LEFT JOIN partidos p ON p.temporada_id = t.id AND p.goles_local IS NOT NULL
        GROUP BY l.id
        ORDER BY promedio_goles DESC
        """
    )
    return [dict(row) for row in cursor.fetchall()]


def obtener_estadisticas_liga(liga_id: int) -> Dict[str, Any]:
    db = get_db()
    cursor = db.get_connection().cursor()

    cursor.execute(
        """
        SELECT 
            AVG(p.goles_local + p.goles_visitante) as promedio,
            COUNT(p.id) as total_partidos,
            SUM(CASE WHEN (p.goles_local + p.goles_visitante) > 3 THEN 1 ELSE 0 END) as partidos_alto,
            SUM(CASE WHEN (p.goles_local + p.goles_visitante) <= 3 THEN 1 ELSE 0 END) as partidos_bajo
        FROM partidos p
        JOIN temporadas t ON p.temporada_id = t.id
        WHERE t.liga_id = ?
        """,
        (liga_id,),
    )
    stats = cursor.fetchone()

    return {
        "liga_id": liga_id,
        "promedio_goles": round(stats["promedio"], 2) if stats["promedio"] else 0.0,
        "total_partidos": stats["total_partidos"],
        "partidos_mas_3_goles": stats["partidos_alto"],
        "partidos_menos_igual_3_goles": stats["partidos_bajo"],
    }
