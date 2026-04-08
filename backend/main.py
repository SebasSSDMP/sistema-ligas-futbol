import sqlite3
import os
import logging
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

from backend.models import (
    Liga, LigaCreate, LigaUpdate,
    Temporada, TemporadaCreate,
    Equipo, EquipoCreate, EquipoUpdate,
    Partido, PartidoCreate, PartidoUpdate,
    EstadisticasLiga, RankingLiga, RankingEquipo,
    LigaCache, EquipoCache, PartidoCache, CacheStatus
)
from backend.api_football import APIFootballCache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
DATABASE_PATH = BASE_DIR / "data" / "futbol.db"


def get_database_path():
    path = Path(DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def get_connection():
    conn = sqlite3.connect(get_database_path())
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    conn = None
    try:
        conn = get_connection()
        yield conn
    finally:
        if conn:
            conn.close()


def init_db():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ligas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                pais TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equipos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                liga_id INTEGER REFERENCES ligas(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS temporadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                liga_id INTEGER REFERENCES ligas(id),
                fecha_inicio DATE,
                fecha_fin DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS partidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE,
                equipo_local INTEGER REFERENCES equipos(id),
                equipo_visitante INTEGER REFERENCES equipos(id),
                goles_local INTEGER DEFAULT 0,
                goles_visitante INTEGER DEFAULT 0,
                arbitro TEXT,
                estadio TEXT,
                temporada_id INTEGER REFERENCES temporadas(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS temporada_equipos (
                temporada_id INTEGER REFERENCES temporadas(id) ON DELETE CASCADE,
                equipo_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
                PRIMARY KEY (temporada_id, equipo_id)
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipos_liga_id ON equipos(liga_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_temporadas_liga_id ON temporadas(liga_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_partidos_temporada_id ON partidos(temporada_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_partidos_equipo_local ON partidos(equipo_local)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_partidos_equipo_visit ON partidos(equipo_visitante)")

        conn.commit()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


app = FastAPI(title="API Gestion de Ligas de Futbol", version="1.0.0")

api_key = os.environ.get("FOOTBALL_DATA_KEY")
if not api_key:
    logger.warning("FOOTBALL_DATA_KEY environment variable not set!")
else:
    logger.info("FOOTBALL_DATA_KEY is configured")


@app.on_event("startup")
async def startup():
    init_db()
    cache = APIFootballCache()
    cache._init_cache_tables()
    logger.info("Database and cache tables initialized on startup")


origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/")
def root():
    return {"message": "API Gestion de Ligas de Futbol", "status": "running"}


@app.get("/ligas", response_model=List[Liga])
def obtener_ligas():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, pais FROM ligas ORDER BY nombre")
        return [dict(row) for row in cursor.fetchall()]


@app.post("/ligas", response_model=Liga)
def crear_liga(liga: LigaCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ligas (nombre, pais) VALUES (?, ?)",
            (liga.nombre, liga.pais)
        )
        conn.commit()
        liga_id = cursor.lastrowid
        cursor.execute("SELECT id, nombre, pais FROM ligas WHERE id = ?", (liga_id,))
        return dict(cursor.fetchone())


@app.put("/ligas/{liga_id}", response_model=Liga)
def actualizar_liga(liga_id: int, liga: LigaUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ligas SET nombre = ?, pais = ? WHERE id = ?",
            (liga.nombre, liga.pais, liga_id)
        )
        conn.commit()
        cursor.execute("SELECT id, nombre, pais FROM ligas WHERE id = ?", (liga_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Liga no encontrada")
        return dict(result)


@app.delete("/ligas/{liga_id}")
def eliminar_liga(liga_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM partidos WHERE temporada_id IN (SELECT id FROM temporadas WHERE liga_id = ?)",
            (liga_id,)
        )
        cursor.execute("DELETE FROM equipos WHERE liga_id = ?", (liga_id,))
        cursor.execute("DELETE FROM temporadas WHERE liga_id = ?", (liga_id,))
        cursor.execute("DELETE FROM ligas WHERE id = ?", (liga_id,))
        conn.commit()
        return {"message": "Liga eliminada"}


@app.get("/ligas/{liga_id}/temporadas", response_model=List[Temporada])
def obtener_temporadas(liga_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, fecha_inicio, fecha_fin, liga_id FROM temporadas WHERE liga_id = ? ORDER BY nombre",
            (liga_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


@app.post("/temporadas", response_model=Temporada)
def crear_temporada(temporada: TemporadaCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO temporadas (nombre, fecha_inicio, fecha_fin, liga_id) VALUES (?, ?, ?, ?)",
            (temporada.nombre, temporada.fecha_inicio, temporada.fecha_fin, temporada.liga_id),
        )
        conn.commit()
        temp_id = cursor.lastrowid
        cursor.execute(
            "SELECT id, nombre, fecha_inicio, fecha_fin, liga_id FROM temporadas WHERE id = ?",
            (temp_id,)
        )
        return dict(cursor.fetchone())


@app.get("/ligas/{liga_id}/equipos", response_model=List[Equipo])
def obtener_equipos(liga_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, liga_id FROM equipos WHERE liga_id = ? ORDER BY nombre",
            (liga_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


@app.post("/equipos", response_model=Equipo)
def crear_equipo(equipo: EquipoCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO equipos (nombre, liga_id) VALUES (?, ?)",
            (equipo.nombre, equipo.liga_id)
        )
        conn.commit()
        equipo_id = cursor.lastrowid
        cursor.execute("SELECT id, nombre, liga_id FROM equipos WHERE id = ?", (equipo_id,))
        return dict(cursor.fetchone())


@app.put("/equipos/{equipo_id}", response_model=Equipo)
def actualizar_equipo(equipo_id: int, equipo: EquipoUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        if equipo.liga_id is not None:
            cursor.execute("UPDATE equipos SET nombre = ?, liga_id = ? WHERE id = ?",
                          (equipo.nombre, equipo.liga_id, equipo_id))
        else:
            cursor.execute("UPDATE equipos SET nombre = ? WHERE id = ?",
                          (equipo.nombre, equipo_id))
        conn.commit()
        cursor.execute("SELECT id, nombre, liga_id FROM equipos WHERE id = ?", (equipo_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Equipo no encontrado")
        return dict(result)


@app.delete("/equipos/{equipo_id}")
def eliminar_equipo(equipo_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM equipos WHERE id = ?", (equipo_id,))
        conn.commit()
        return {"message": "Equipo eliminado"}


@app.get("/temporadas/{temporada_id}/equipos", response_model=List[Equipo])
def obtener_equipos_temporada(temporada_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT e.id, e.nombre, e.liga_id FROM equipos e
            JOIN temporada_equipos te ON e.id = te.equipo_id
            WHERE te.temporada_id = ?
            ORDER BY e.nombre
            """,
            (temporada_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


@app.post("/temporadas/{temporada_id}/equipos/{equipo_id}")
def asociar_equipo_temporada(temporada_id: int, equipo_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO temporada_equipos (temporada_id, equipo_id) VALUES (?, ?)",
            (temporada_id, equipo_id)
        )
        conn.commit()
        return {"message": "Equipo asociado a temporada"}


@app.delete("/temporadas/{temporada_id}/equipos/{equipo_id}")
def desasociar_equipo_temporada(temporada_id: int, equipo_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM temporada_equipos WHERE temporada_id = ? AND equipo_id = ?",
            (temporada_id, equipo_id)
        )
        conn.commit()
        return {"message": "Equipo desasociado de temporada"}


@app.get("/temporadas/{temporada_id}/partidos", response_model=List[Partido])
def obtener_partidos(temporada_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, fecha, equipo_local, equipo_visitante,
                   goles_local, goles_visitante, temporada_id
            FROM partidos WHERE temporada_id = ? ORDER BY fecha
            """,
            (temporada_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


@app.post("/partidos", response_model=Partido)
def crear_partido(partido: PartidoCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO partidos
               (fecha, equipo_local, equipo_visitante, goles_local, goles_visitante, temporada_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                partido.fecha, partido.equipo_local, partido.equipo_visitante,
                partido.goles_local, partido.goles_visitante, partido.temporada_id,
            ),
        )
        conn.commit()
        partido_id = cursor.lastrowid
        cursor.execute(
            "SELECT id, fecha, equipo_local, equipo_visitante, goles_local, goles_visitante, temporada_id FROM partidos WHERE id = ?",
            (partido_id,)
        )
        return dict(cursor.fetchone())


@app.put("/partidos/{partido_id}", response_model=Partido)
def actualizar_partido(partido_id: int, partido: PartidoUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE partidos
               SET goles_local = ?, goles_visitante = ?, fecha = ?
               WHERE id = ?""",
            (partido.goles_local, partido.goles_visitante, partido.fecha, partido_id)
        )
        conn.commit()
        cursor.execute(
            "SELECT id, fecha, equipo_local, equipo_visitante, goles_local, goles_visitante, temporada_id FROM partidos WHERE id = ?",
            (partido_id,)
        )
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Partido no encontrado")
        return dict(result)


@app.get("/ligas/{liga_id}/estadisticas", response_model=EstadisticasLiga)
def obtener_estadisticas(
    liga_id: int,
    temporada_id: Optional[int] = Query(None),
):
    with get_db() as conn:
        cursor = conn.cursor()

        if temporada_id:
            cursor.execute(
                """
                SELECT
                    AVG(p.goles_local + p.goles_visitante) AS promedio,
                    COUNT(p.id) AS total_partidos,
                    SUM(CASE WHEN (p.goles_local + p.goles_visitante) >= 3 THEN 1 ELSE 0 END) AS partidos_alto,
                    SUM(CASE WHEN (p.goles_local + p.goles_visitante) < 3 THEN 1 ELSE 0 END) AS partidos_bajo
                FROM partidos p
                JOIN temporadas t ON p.temporada_id = t.id
                WHERE t.liga_id = ? AND p.temporada_id = ?
                """,
                (liga_id, temporada_id),
            )
        else:
            cursor.execute(
                """
                SELECT
                    AVG(p.goles_local + p.goles_visitante) AS promedio,
                    COUNT(p.id) AS total_partidos,
                    SUM(CASE WHEN (p.goles_local + p.goles_visitante) >= 3 THEN 1 ELSE 0 END) AS partidos_alto,
                    SUM(CASE WHEN (p.goles_local + p.goles_visitante) < 3 THEN 1 ELSE 0 END) AS partidos_bajo
                FROM partidos p
                JOIN temporadas t ON p.temporada_id = t.id
                WHERE t.liga_id = ?
                """,
                (liga_id,),
            )

        row = cursor.fetchone()
        if row:
            return {
                "liga_id": liga_id,
                "promedio_goles": round(float(row["promedio"]), 2) if row["promedio"] else 0.0,
                "total_partidos": row["total_partidos"] or 0,
                "partidos_mas_3_goles": row["partidos_alto"] or 0,      # ahora >= 3
                "partidos_menos_igual_3_goles": row["partidos_bajo"] or 0,  # ahora < 3
                "umbral_goles": 3,
                "temporada_id": temporada_id,
            }
        return {
            "liga_id": liga_id, "promedio_goles": 0.0,
            "total_partidos": 0, "partidos_mas_3_goles": 0,
            "partidos_menos_igual_3_goles": 0, "umbral_goles": 3,
            "temporada_id": temporada_id,
        }


@app.get("/ranking", response_model=List[RankingLiga])
def ranking_ligas():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                l.id, l.nombre, l.pais,
                COALESCE(AVG(p.goles_local + p.goles_visitante), 0) AS promedio_goles,
                COUNT(p.id) AS total_partidos
            FROM ligas l
            LEFT JOIN temporadas t ON t.liga_id = l.id
            LEFT JOIN partidos p ON p.temporada_id = t.id
            GROUP BY l.id
            ORDER BY promedio_goles DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]


@app.get("/ligas/{liga_id}/ranking", response_model=List[RankingEquipo])
def ranking_liga(liga_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            WITH stats AS (
                SELECT
                    e.id AS equipo_id,
                    e.nombre,
                    COUNT(p.id) AS partidos_jugados,
                    SUM(CASE
                        WHEN p.equipo_local = e.id AND p.goles_local > p.goles_visitante THEN 1
                        WHEN p.equipo_visitante = e.id AND p.goles_visitante > p.goles_local THEN 1
                        ELSE 0
                    END) AS victorias,
                    SUM(CASE
                        WHEN p.goles_local = p.goles_visitante THEN 1
                        ELSE 0
                    END) AS empates,
                    SUM(CASE
                        WHEN p.equipo_local = e.id AND p.goles_local < p.goles_visitante THEN 1
                        WHEN p.equipo_visitante = e.id AND p.goles_visitante < p.goles_local THEN 1
                        ELSE 0
                    END) AS derrotas,
                    SUM(CASE
                        WHEN p.equipo_local = e.id THEN p.goles_local
                        ELSE p.goles_visitante
                    END) AS goles_favor,
                    SUM(CASE
                        WHEN p.equipo_local = e.id THEN p.goles_visitante
                        ELSE p.goles_local
                    END) AS goles_contra
                FROM equipos e
                JOIN partidos p ON (p.equipo_local = e.id OR p.equipo_visitante = e.id)
                JOIN temporadas t ON p.temporada_id = t.id
                WHERE t.liga_id = ? AND e.liga_id = ?
                GROUP BY e.id, e.nombre
            )
            SELECT
                equipo_id, nombre, partidos_jugados, victorias, empates, derrotas,
                goles_favor, goles_contra,
                (goles_favor - goles_contra) AS diferencia_goles,
                (victorias * 3 + empates) AS puntos
            FROM stats
            ORDER BY puntos DESC, (goles_favor - goles_contra) DESC
            """,
            (liga_id, liga_id)
        )
        return [dict(row) for row in cursor.fetchall()]


@app.post("/reset-db")
def reset_database():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM partidos")
        cursor.execute("DELETE FROM temporada_equipos")
        cursor.execute("DELETE FROM equipos")
        cursor.execute("DELETE FROM temporadas")
        cursor.execute("DELETE FROM ligas")
        conn.commit()
        return {"message": "Base de datos limpiada"}


@app.get("/external/ligas", response_model=List[LigaCache])
def obtener_ligas_externas(force_refresh: bool = Query(False)):
    cache = APIFootballCache()
    return cache.get_ligas(force_refresh=force_refresh)


@app.get("/external/equipos/{liga_id}", response_model=List[EquipoCache])
def obtener_equipos_externos(liga_id: int, force_refresh: bool = Query(False)):
    cache = APIFootballCache()
    return cache.get_equipos(liga_id, force_refresh=force_refresh)


@app.get("/external/partidos/{liga_id}", response_model=List[PartidoCache])
def obtener_partidos_externos(
    liga_id: int,
    temporada: int = Query(2024),
    force_refresh: bool = Query(False),
):
    cache = APIFootballCache()
    return cache.get_partidos(liga_id, temporada=temporada, force_refresh=force_refresh)


@app.get("/external/cache-status", response_model=CacheStatus)
def estado_cache():
    cache = APIFootballCache()
    return cache.get_cache_status()


@app.post("/external/cache/clear")
def limpiar_cache(tipo: Optional[str] = Query(None)):
    cache = APIFootballCache()
    cache.clear_cache(tipo if tipo else None)
    return {"message": f"Cache limpiado: {tipo or 'todo'}"}


@app.post("/importar-liga/{liga_id}")
def importar_liga(liga_id: int, temporada: int = Query(2024)):
    logger.info(f"{'='*50}\nIMPORTANDO LIGA ID: {liga_id}\n{'='*50}")

    try:
        cache = APIFootballCache()
        liga_externa = cache.get_ligas(force_refresh=False)
        equipos_externos = cache.get_equipos(liga_id, force_refresh=False)
        partidos_externos = cache.get_partidos(liga_id, temporada=temporada, force_refresh=False)

        liga_data = next((l for l in liga_externa if l.get("id") == liga_id), None)
        if not liga_data:
            raise HTTPException(status_code=404, detail=f"Liga {liga_id} no encontrada en football-data.org")

        logger.info(f"Liga: {liga_data.get('name')} ({liga_data.get('country')})")
        logger.info(f"Equipos: {len(equipos_externos)}  |  Partidos: {len(partidos_externos)}")

        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id FROM ligas WHERE nombre = ? AND pais = ?",
                (liga_data.get("name"), liga_data.get("country")),
            )
            liga_existente = cursor.fetchone()

            if liga_existente:
                local_liga_id = liga_existente["id"]
            else:
                cursor.execute(
                    "INSERT INTO ligas (nombre, pais) VALUES (?, ?)",
                    (liga_data.get("name"), liga_data.get("country")),
                )
                conn.commit()
                local_liga_id = cursor.lastrowid
                logger.info(f"Liga guardada: ID {local_liga_id}")

            cursor.execute(
                "SELECT id FROM temporadas WHERE liga_id = ? AND nombre = ?",
                (local_liga_id, str(temporada)),
            )
            temp_row = cursor.fetchone()

            if temp_row:
                local_temporada_id = temp_row["id"]
            else:
                cursor.execute(
                    "INSERT INTO temporadas (nombre, liga_id) VALUES (?, ?)",
                    (str(temporada), local_liga_id),
                )
                conn.commit()
                local_temporada_id = cursor.lastrowid
                logger.info(f"Temporada creada: ID {local_temporada_id}")

            equipos_guardados = 0
            equipos_map = {}

            for eq in equipos_externos:
                if not eq.get("id") or not eq.get("name"):
                    continue
                cursor.execute(
                    "SELECT id FROM equipos WHERE nombre = ? AND liga_id = ?",
                    (eq.get("name"), local_liga_id),
                )
                eq_existente = cursor.fetchone()
                if eq_existente:
                    local_eq_id = eq_existente["id"]
                    equipos_map[eq["id"]] = local_eq_id
                else:
                    cursor.execute(
                        "INSERT INTO equipos (nombre, liga_id) VALUES (?, ?)",
                        (eq.get("name"), local_liga_id),
                    )
                    conn.commit()
                    local_eq_id = cursor.lastrowid
                    equipos_map[eq["id"]] = local_eq_id
                    equipos_guardados += 1
                    logger.info(f"Equipo: {eq.get('name')} (ID local: {local_eq_id})")

                cursor.execute(
                    "INSERT OR IGNORE INTO temporada_equipos (temporada_id, equipo_id) VALUES (?, ?)",
                    (local_temporada_id, local_eq_id)
                )

            conn.commit()
            logger.info(f"Equipos nuevos: {equipos_guardados}")

            partidos_guardados = 0
            partidos_error = 0

            for part in partidos_externos:
                try:
                    if not part.get("id"):
                        continue
                    local_local_id = equipos_map.get(part.get("equipo_local_id"))
                    local_visitante_id = equipos_map.get(part.get("equipo_visitante_id"))
                    if not local_local_id or not local_visitante_id:
                        logger.warning(f"Partido {part.get('id')}: equipos no encontrados en mapeo")
                        continue

                    cursor.execute(
                        "SELECT id FROM partidos WHERE equipo_local = ? AND equipo_visitante = ? AND fecha = ?",
                        (local_local_id, local_visitante_id, part.get("fecha")),
                    )
                    if cursor.fetchone():
                        continue

                    cursor.execute(
                        """INSERT INTO partidos
                           (fecha, equipo_local, equipo_visitante, goles_local, goles_visitante, temporada_id)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            part.get("fecha"),
                            local_local_id,
                            local_visitante_id,
                            part.get("goles_local") or 0,
                            part.get("goles_visitante") or 0,
                            local_temporada_id,
                        ),
                    )
                    conn.commit()
                    partidos_guardados += 1
                except Exception as e:
                    partidos_error += 1
                    logger.error(f"Error guardando partido {part.get('id')}: {e}")

            logger.info(f"Partidos nuevos: {partidos_guardados}  |  Errores: {partidos_error}")

            return {
                "liga": liga_data.get("name"),
                "liga_id": local_liga_id,
                "temporada": str(temporada),
                "equipos_guardados": equipos_guardados,
                "partidos_guardados": partidos_guardados,
                "partidos_omitidos": len(partidos_externos) - partidos_guardados,
                "temporada_id": local_temporada_id,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ERROR EN IMPORTACION: {e}")
        raise HTTPException(status_code=500, detail=f"Error al importar liga: {str(e)}")


@app.post("/actualizar-liga/{liga_id}")
def actualizar_liga_externa(liga_id: int, temporada: int = Query(2024)):
    logger.info(f"{'='*50}\nACTUALIZANDO LIGA ID: {liga_id}\n{'='*50}")

    try:
        cache = APIFootballCache()
        equipos_externos = cache.get_equipos(liga_id, force_refresh=True)
        partidos_externos = cache.get_partidos(liga_id, temporada=temporada, force_refresh=True)
        liga_externa = cache.get_ligas(force_refresh=False)

        liga_data = next((l for l in liga_externa if l.get("id") == liga_id), None)
        if not liga_data:
            raise HTTPException(status_code=404, detail="Liga no encontrada en football-data.org")

        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id FROM ligas WHERE nombre = ? AND pais = ?",
                (liga_data.get("name"), liga_data.get("country")),
            )
            liga_row = cursor.fetchone()
            if not liga_row:
                raise HTTPException(status_code=404, detail="Liga no existe localmente. Importar primero.")

            local_liga_id = liga_row["id"]

            cursor.execute(
                "SELECT id FROM temporadas WHERE liga_id = ? AND nombre = ?",
                (local_liga_id, str(temporada)),
            )
            temp_row = cursor.fetchone()
            if not temp_row:
                cursor.execute(
                    "INSERT INTO temporadas (nombre, liga_id) VALUES (?, ?)",
                    (str(temporada), local_liga_id),
                )
                conn.commit()
                local_temporada_id = cursor.lastrowid
            else:
                local_temporada_id = temp_row["id"]

            equipos_guardados = 0
            equipos_map = {}

            for eq in equipos_externos:
                if not eq.get("id") or not eq.get("name"):
                    continue
                cursor.execute(
                    "SELECT id FROM equipos WHERE nombre = ? AND liga_id = ?",
                    (eq.get("name"), local_liga_id),
                )
                eq_existente = cursor.fetchone()
                if eq_existente:
                    local_eq_id = eq_existente["id"]
                    equipos_map[eq["id"]] = local_eq_id
                else:
                    cursor.execute(
                        "INSERT INTO equipos (nombre, liga_id) VALUES (?, ?)",
                        (eq.get("name"), local_liga_id),
                    )
                    conn.commit()
                    local_eq_id = cursor.lastrowid
                    equipos_map[eq["id"]] = local_eq_id
                    equipos_guardados += 1

                cursor.execute(
                    "INSERT OR IGNORE INTO temporada_equipos (temporada_id, equipo_id) VALUES (?, ?)",
                    (local_temporada_id, local_eq_id)
                )

            conn.commit()
            partidos_guardados = 0

            for part in partidos_externos:
                try:
                    local_local_id = equipos_map.get(part.get("equipo_local_id"))
                    local_visitante_id = equipos_map.get(part.get("equipo_visitante_id"))
                    if not local_local_id or not local_visitante_id:
                        continue

                    cursor.execute(
                        "SELECT id FROM partidos WHERE equipo_local = ? AND equipo_visitante = ? AND fecha = ?",
                        (local_local_id, local_visitante_id, part.get("fecha")),
                    )
                    if not cursor.fetchone():
                        cursor.execute(
                            """INSERT INTO partidos
                               (fecha, equipo_local, equipo_visitante, goles_local, goles_visitante, temporada_id)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (
                                part.get("fecha"),
                                local_local_id,
                                local_visitante_id,
                                part.get("goles_local") or 0,
                                part.get("goles_visitante") or 0,
                                local_temporada_id,
                            ),
                        )
                        conn.commit()
                        partidos_guardados += 1
                except Exception as e:
                    logger.error(f"Error guardando partido {part.get('id')}: {e}")

            return {
                "success": True,
                "liga": liga_data.get("name"),
                "equipos_nuevos": equipos_guardados,
                "partidos_nuevos": partidos_guardados,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
