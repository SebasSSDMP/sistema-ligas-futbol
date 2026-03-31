from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
import psycopg2
import psycopg2.extras
import os
import logging
from datetime import datetime

from models import (
    Liga, LigaCreate, LigaUpdate,
    Temporada, TemporadaCreate,
    Equipo, EquipoCreate, EquipoUpdate,
    Partido, PartidoCreate,
    EstadisticasLiga, RankingLiga,
    LigaCache, EquipoCache, PartidoCache, CacheStatus
)
from api_football import APIFootballCache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_database_url():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return database_url


def get_connection():
    database_url = get_database_url()
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    conn = psycopg2.connect(database_url)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


def init_db():
    conn = None
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ligas (
                id         SERIAL PRIMARY KEY,
                nombre     VARCHAR(255) NOT NULL,
                pais       VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equipos (
                id         SERIAL PRIMARY KEY,
                nombre     VARCHAR(255) NOT NULL,
                liga_id    INTEGER REFERENCES ligas(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS temporadas (
                id          SERIAL PRIMARY KEY,
                nombre      VARCHAR(100) NOT NULL,
                liga_id     INTEGER REFERENCES ligas(id),
                fecha_inicio DATE,
                fecha_fin    DATE,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS partidos (
                id               SERIAL PRIMARY KEY,
                fecha            DATE,
                equipo_local     INTEGER REFERENCES equipos(id),
                equipo_visitante INTEGER REFERENCES equipos(id),
                goles_local      INTEGER DEFAULT 0,
                goles_visitante  INTEGER DEFAULT 0,
                arbitro          VARCHAR(255),
                estadio          VARCHAR(255),
                temporada_id     INTEGER REFERENCES temporadas(id),
                created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipos_liga_id         ON equipos(liga_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_temporadas_liga_id      ON temporadas(liga_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_partidos_temporada_id   ON partidos(temporada_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_partidos_equipo_local   ON partidos(equipo_local)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_partidos_equipo_visit   ON partidos(equipo_visitante)")

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


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Validar API key — ahora se llama FOOTBALL_DATA_KEY
    api_key = os.environ.get("FOOTBALL_DATA_KEY")
    if not api_key:
        logger.error("FOOTBALL_DATA_KEY environment variable is not set!")
    else:
        logger.info("FOOTBALL_DATA_KEY is configured")

    init_db()
    cache = APIFootballCache()
    cache._init_cache_tables()
    logger.info("Database and cache tables initialized on startup")
    yield


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="API Gestión de Ligas de Fútbol", version="1.0.0", lifespan=lifespan)

# ── CORS ──────────────────────────────────────────────────────────────────────
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

if not origins:
    origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

logger.info(f"CORS allowed origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── DB dependency ─────────────────────────────────────────────────────────────
def get_db():
    conn = None
    try:
        conn = get_connection()
        yield conn
    finally:
        if conn:
            conn.close()


# ── Endpoints básicos ─────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/")
def root():
    return {"message": "API Gestión de Ligas de Fútbol", "status": "running"}


# LIGAS
@app.get("/ligas", response_model=List[Liga])
def obtener_ligas(db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM ligas ORDER BY nombre")
    return [dict(row) for row in cursor.fetchall()]


@app.post("/ligas", response_model=Liga)
def crear_liga(liga: LigaCreate, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO ligas (nombre, pais) VALUES (%s, %s) RETURNING id",
        (liga.nombre, liga.pais)
    )
    db.commit()
    liga_id = cursor.fetchone()["id"]
    cursor.execute("SELECT * FROM ligas WHERE id = %s", (liga_id,))
    return dict(cursor.fetchone())


@app.put("/ligas/{liga_id}", response_model=Liga)
def actualizar_liga(liga_id: int, liga: LigaUpdate, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        "UPDATE ligas SET nombre = %s, pais = %s WHERE id = %s",
        (liga.nombre, liga.pais, liga_id)
    )
    db.commit()
    cursor.execute("SELECT * FROM ligas WHERE id = %s", (liga_id,))
    return dict(cursor.fetchone())


@app.delete("/ligas/{liga_id}")
def eliminar_liga(liga_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM partidos WHERE temporada_id IN (SELECT id FROM temporadas WHERE liga_id = %s)",
        (liga_id,)
    )
    cursor.execute("DELETE FROM equipos  WHERE liga_id = %s", (liga_id,))
    cursor.execute("DELETE FROM temporadas WHERE liga_id = %s", (liga_id,))
    cursor.execute("DELETE FROM ligas    WHERE id = %s", (liga_id,))
    db.commit()
    return {"message": "Liga eliminada"}


# TEMPORADAS
@app.get("/ligas/{liga_id}/temporadas", response_model=List[Temporada])
def obtener_temporadas(liga_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM temporadas WHERE liga_id = %s ORDER BY nombre", (liga_id,))
    return [dict(row) for row in cursor.fetchall()]


@app.post("/temporadas", response_model=Temporada)
def crear_temporada(temporada: TemporadaCreate, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO temporadas (nombre, fecha_inicio, fecha_fin, liga_id) VALUES (%s, %s, %s, %s) RETURNING id",
        (temporada.nombre, temporada.fecha_inicio, temporada.fecha_fin, temporada.liga_id),
    )
    db.commit()
    temp_id = cursor.fetchone()["id"]
    cursor.execute("SELECT * FROM temporadas WHERE id = %s", (temp_id,))
    return dict(cursor.fetchone())


# EQUIPOS
@app.get("/ligas/{liga_id}/equipos", response_model=List[Equipo])
def obtener_equipos(liga_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM equipos WHERE liga_id = %s ORDER BY nombre", (liga_id,))
    return [dict(row) for row in cursor.fetchall()]


@app.post("/equipos", response_model=Equipo)
def crear_equipo(equipo: EquipoCreate, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO equipos (nombre, liga_id) VALUES (%s, %s) RETURNING id",
        (equipo.nombre, equipo.liga_id)
    )
    db.commit()
    equipo_id = cursor.fetchone()["id"]
    cursor.execute("SELECT * FROM equipos WHERE id = %s", (equipo_id,))
    return dict(cursor.fetchone())


@app.put("/equipos/{equipo_id}", response_model=Equipo)
def actualizar_equipo(equipo_id: int, equipo: EquipoUpdate, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("UPDATE equipos SET nombre = %s WHERE id = %s", (equipo.nombre, equipo_id))
    db.commit()
    cursor.execute("SELECT * FROM equipos WHERE id = %s", (equipo_id,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return dict(result)


@app.delete("/equipos/{equipo_id}")
def eliminar_equipo(equipo_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("DELETE FROM equipos WHERE id = %s", (equipo_id,))
    db.commit()
    return {"message": "Equipo eliminado"}


# PARTIDOS
@app.get("/temporadas/{temporada_id}/partidos", response_model=List[Partido])
def obtener_partidos(temporada_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM partidos WHERE temporada_id = %s ORDER BY fecha",
        (temporada_id,)
    )
    return [dict(row) for row in cursor.fetchall()]


@app.post("/partidos", response_model=Partido)
def crear_partido(partido: PartidoCreate, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO partidos
           (fecha, equipo_local, equipo_visitante, goles_local, goles_visitante, arbitro, estadio, temporada_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (
            partido.fecha, partido.equipo_local, partido.equipo_visitante,
            partido.goles_local, partido.goles_visitante, partido.arbitro,
            partido.estadio, partido.temporada_id,
        ),
    )
    db.commit()
    partido_id = cursor.fetchone()["id"]
    cursor.execute("SELECT * FROM partidos WHERE id = %s", (partido_id,))
    return dict(cursor.fetchone())


# ESTADÍSTICAS
@app.get("/ligas/{liga_id}/estadisticas", response_model=EstadisticasLiga)
def obtener_estadisticas(liga_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT
            AVG(p.goles_local + p.goles_visitante)                                        AS promedio,
            COUNT(p.id)                                                                    AS total_partidos,
            SUM(CASE WHEN (p.goles_local + p.goles_visitante) > 3  THEN 1 ELSE 0 END)    AS partidos_alto,
            SUM(CASE WHEN (p.goles_local + p.goles_visitante) <= 3 THEN 1 ELSE 0 END)    AS partidos_bajo
        FROM partidos p
        JOIN temporadas t ON p.temporada_id = t.id
        WHERE t.liga_id = %s
        """,
        (liga_id,),
    )
    row = cursor.fetchone()
    if row:
        return {
            "liga_id":                        liga_id,
            "promedio_goles":                 round(row["promedio"], 2) if row["promedio"] else 0.0,
            "total_partidos":                 row["total_partidos"] or 0,
            "partidos_mas_3_goles":           row["partidos_alto"] or 0,
            "partidos_menos_igual_3_goles":   row["partidos_bajo"] or 0,
        }
    return {
        "liga_id": liga_id, "promedio_goles": 0.0,
        "total_partidos": 0, "partidos_mas_3_goles": 0, "partidos_menos_igual_3_goles": 0,
    }


# RANKING
@app.get("/ranking", response_model=List[RankingLiga])
def ranking_ligas(db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT
            l.id, l.nombre, l.pais,
            AVG(p.goles_local + p.goles_visitante) AS promedio_goles,
            COUNT(p.id)                             AS total_partidos
        FROM ligas l
        LEFT JOIN temporadas t ON t.liga_id = l.id
        LEFT JOIN partidos   p ON p.temporada_id = t.id
        GROUP BY l.id
        ORDER BY promedio_goles DESC
        """
    )
    return [dict(row) for row in cursor.fetchall()]


# RESET
@app.post("/reset-db")
def reset_database(db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("DELETE FROM partidos")
    cursor.execute("DELETE FROM equipos")
    cursor.execute("DELETE FROM temporadas")
    cursor.execute("DELETE FROM ligas")
    db.commit()
    return {"message": "Base de datos limpiada"}


# ── External API (football-data.org) ──────────────────────────────────────────
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


# ── Importar / Actualizar ─────────────────────────────────────────────────────
@app.post("/importar-liga/{liga_id}")
def importar_liga(liga_id: int, temporada: int = Query(2024)):
    """
    Importa una competición de football-data.org a la BD local.
    liga_id = ID numérico de la competición, ej. 2021 (Premier League), 2014 (La Liga).
    """
    logger.info(f"{'='*50}\nIMPORTANDO LIGA ID: {liga_id}\n{'='*50}")

    db = None
    try:
        db     = get_connection()
        cursor = db.cursor()

        cache             = APIFootballCache()
        liga_externa      = cache.get_ligas(force_refresh=False)
        equipos_externos  = cache.get_equipos(liga_id, force_refresh=False)
        partidos_externos = cache.get_partidos(liga_id, temporada=temporada, force_refresh=False)

        liga_data = next((l for l in liga_externa if l.get("id") == liga_id), None)
        if not liga_data:
            raise HTTPException(status_code=404, detail=f"Liga {liga_id} no encontrada en football-data.org")

        logger.info(f"Liga: {liga_data.get('name')} ({liga_data.get('country')})")
        logger.info(f"Equipos: {len(equipos_externos)}  |  Partidos: {len(partidos_externos)}")

        # ── Liga local ────────────────────────────────────────────────────────
        cursor.execute(
            "SELECT id FROM ligas WHERE nombre = %s AND pais = %s",
            (liga_data.get("name"), liga_data.get("country")),
        )
        liga_existente = cursor.fetchone()

        if liga_existente:
            local_liga_id = liga_existente["id"]
        else:
            cursor.execute(
                "INSERT INTO ligas (nombre, pais) VALUES (%s, %s) RETURNING id",
                (liga_data.get("name"), liga_data.get("country")),
            )
            db.commit()
            local_liga_id = cursor.fetchone()["id"]
            logger.info(f"✓ Liga guardada: ID {local_liga_id}")

        # ── Temporada local ───────────────────────────────────────────────────
        cursor.execute(
            "SELECT id FROM temporadas WHERE liga_id = %s AND nombre = %s",
            (local_liga_id, str(temporada)),
        )
        temp_row = cursor.fetchone()

        if temp_row:
            local_temporada_id = temp_row["id"]
        else:
            cursor.execute(
                "INSERT INTO temporadas (nombre, liga_id) VALUES (%s, %s) RETURNING id",
                (str(temporada), local_liga_id),
            )
            db.commit()
            local_temporada_id = cursor.fetchone()["id"]
            logger.info(f"✓ Temporada creada: ID {local_temporada_id}")

        # ── Equipos ───────────────────────────────────────────────────────────
        equipos_guardados = 0
        equipos_map       = {}

        for eq in equipos_externos:
            if not eq.get("id") or not eq.get("name"):
                continue
            cursor.execute(
                "SELECT id FROM equipos WHERE nombre = %s AND liga_id = %s",
                (eq.get("name"), local_liga_id),
            )
            eq_existente = cursor.fetchone()
            if eq_existente:
                equipos_map[eq["id"]] = eq_existente["id"]
            else:
                cursor.execute(
                    "INSERT INTO equipos (nombre, liga_id) VALUES (%s, %s) RETURNING id",
                    (eq.get("name"), local_liga_id),
                )
                db.commit()
                result = cursor.fetchone()
                if result is None:
                    raise Exception("Failed to insert equipo")
                local_eq_id = result["id"]
                equipos_map[eq["id"]] = local_eq_id
                equipos_guardados += 1
                logger.info(f"✓ Equipo: {eq.get('name')} (ID local: {local_eq_id})")

        logger.info(f"Equipos nuevos: {equipos_guardados}")

        # ── Partidos ──────────────────────────────────────────────────────────
        partidos_guardados = 0
        partidos_error     = 0

        for part in partidos_externos:
            try:
                if not part.get("id"):
                    continue
                local_local_id     = equipos_map.get(part.get("equipo_local_id"))
                local_visitante_id = equipos_map.get(part.get("equipo_visitante_id"))
                if not local_local_id or not local_visitante_id:
                    logger.warning(f"Partido {part.get('id')}: equipos no encontrados en mapeo")
                    continue

                cursor.execute(
                    "SELECT id FROM partidos WHERE equipo_local = %s AND equipo_visitante = %s AND fecha = %s",
                    (local_local_id, local_visitante_id, part.get("fecha")),
                )
                if cursor.fetchone():
                    continue

                cursor.execute(
                    """INSERT INTO partidos
                       (fecha, equipo_local, equipo_visitante, goles_local, goles_visitante,
                        arbitro, estadio, temporada_id)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        part.get("fecha"),
                        local_local_id,
                        local_visitante_id,
                        part.get("goles_local")     or 0,
                        part.get("goles_visitante") or 0,
                        "Por definir",
                        "Por definir",
                        local_temporada_id,
                    ),
                )
                db.commit()
                partidos_guardados += 1
            except Exception as e:
                partidos_error += 1
                logger.error(f"Error guardando partido {part.get('id')}: {e}")

        logger.info(f"Partidos nuevos: {partidos_guardados}  |  Errores: {partidos_error}")

        return {
            "liga":              liga_data.get("name"),
            "liga_id":           local_liga_id,
            "temporada":         str(temporada),
            "equipos_guardados": equipos_guardados,
            "partidos_guardados": partidos_guardados,
            "partidos_omitidos": len(partidos_externos) - partidos_guardados,
            "temporada_id":      local_temporada_id,
        }

    except HTTPException:
        if db:
            db.rollback()
        raise
    except Exception as e:
        logger.error(f"ERROR EN IMPORTACIÓN: {e}")
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al importar liga: {str(e)}")
    finally:
        if db:
            db.close()


@app.post("/actualizar-liga/{liga_id}")
def actualizar_liga_externa(liga_id: int, temporada: int = Query(2024)):
    logger.info(f"{'='*50}\nACTUALIZANDO LIGA ID: {liga_id}\n{'='*50}")

    db = None
    try:
        db     = get_connection()
        cursor = db.cursor()

        cache             = APIFootballCache()
        equipos_externos  = cache.get_equipos(liga_id, force_refresh=True)
        partidos_externos = cache.get_partidos(liga_id, temporada=temporada, force_refresh=True)
        liga_externa      = cache.get_ligas(force_refresh=False)

        liga_data = next((l for l in liga_externa if l.get("id") == liga_id), None)
        if not liga_data:
            raise HTTPException(status_code=404, detail="Liga no encontrada en football-data.org")

        cursor.execute(
            "SELECT id FROM ligas WHERE nombre = %s AND pais = %s",
            (liga_data.get("name"), liga_data.get("country")),
        )
        liga_row = cursor.fetchone()
        if not liga_row:
            raise HTTPException(status_code=404, detail="Liga no existe localmente. Importar primero.")

        local_liga_id = liga_row["id"]

        cursor.execute(
            "SELECT id FROM temporadas WHERE liga_id = %s AND nombre = %s",
            (local_liga_id, str(temporada)),
        )
        temp_row = cursor.fetchone()
        if not temp_row:
            cursor.execute(
                "INSERT INTO temporadas (nombre, liga_id) VALUES (%s, %s) RETURNING id",
                (str(temporada), local_liga_id),
            )
            db.commit()
            local_temporada_id = cursor.fetchone()["id"]
        else:
            local_temporada_id = temp_row["id"]

        equipos_guardados = 0
        equipos_map       = {}

        for eq in equipos_externos:
            if not eq.get("id") or not eq.get("name"):
                continue
            cursor.execute(
                "SELECT id FROM equipos WHERE nombre = %s AND liga_id = %s",
                (eq.get("name"), local_liga_id),
            )
            eq_existente = cursor.fetchone()
            if eq_existente:
                equipos_map[eq["id"]] = eq_existente["id"]
            else:
                cursor.execute(
                    "INSERT INTO equipos (nombre, liga_id) VALUES (%s, %s) RETURNING id",
                    (eq.get("name"), local_liga_id),
                )
                db.commit()
                result = cursor.fetchone()
                if result is None:
                    raise Exception("Failed to insert equipo")
                equipo_id = result["id"]
                equipos_map[eq["id"]] = equipo_id
                equipos_guardados += 1

        partidos_guardados = 0

        for part in partidos_externos:
            try:
                local_local_id     = equipos_map.get(part.get("equipo_local_id"))
                local_visitante_id = equipos_map.get(part.get("equipo_visitante_id"))
                if not local_local_id or not local_visitante_id:
                    continue

                cursor.execute(
                    "SELECT id FROM partidos WHERE equipo_local = %s AND equipo_visitante = %s AND fecha = %s",
                    (local_local_id, local_visitante_id, part.get("fecha")),
                )
                if not cursor.fetchone():
                    cursor.execute(
                        """INSERT INTO partidos
                           (fecha, equipo_local, equipo_visitante, goles_local, goles_visitante,
                            arbitro, estadio, temporada_id)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            part.get("fecha"),
                            local_local_id,
                            local_visitante_id,
                            part.get("goles_local")     or 0,
                            part.get("goles_visitante") or 0,
                            "Por definir",
                            "Por definir",
                            local_temporada_id,
                        ),
                    )
                    db.commit()
                    partidos_guardados += 1
            except Exception as e:
                logger.error(f"Error guardando partido {part.get('id')}: {e}")

        return {
            "success":        True,
            "liga":           liga_data.get("name"),
            "equipos_nuevos": equipos_guardados,
            "partidos_nuevos": partidos_guardados,
        }

    except HTTPException:
        if db:
            db.rollback()
        raise
    except Exception as e:
        logger.error(f"ERROR: {e}")
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db:
            db.close()


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)