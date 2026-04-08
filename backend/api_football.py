import sqlite3
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = "https://api.football-data.org/v4"
API_KEY = os.environ.get("FOOTBALL_DATA_KEY", "")
HEADERS = {"X-Auth-Token": API_KEY} if API_KEY else {}

TTL_CONFIG = {
    "ligas":    timedelta(hours=24),
    "equipos":  timedelta(hours=24),
    "partidos": timedelta(hours=1),
}

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


class APIFootballCache:
    def __init__(self):
        self._init_cache_tables()

    def _get_connection(self):
        return get_connection()

    def _init_cache_tables(self):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    key TEXT PRIMARY KEY,
                    data_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ligas_cache (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    country TEXT,
                    logo TEXT,
                    season INTEGER,
                    fetched_at TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS equipos_cache (
                    id INTEGER PRIMARY KEY,
                    liga_id INTEGER,
                    name TEXT,
                    logo TEXT,
                    fetched_at TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS partidos_cache (
                    id INTEGER PRIMARY KEY,
                    equipo_local_id INTEGER,
                    equipo_visitante_id INTEGER,
                    fecha TEXT,
                    jornada INTEGER,
                    goles_local INTEGER,
                    goles_visitante INTEGER,
                    estado TEXT,
                    tiempo INTEGER,
                    liga_id INTEGER,
                    temporada INTEGER,
                    fetched_at TEXT
                )
            """)

            conn.commit()
            logger.info("Cache tables initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing cache tables: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def _is_cache_valid(self, cache_key: str) -> bool:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT expires_at FROM cache_metadata WHERE key = ?",
                (f"cache_{cache_key}",)
            )
            row = cursor.fetchone()
            if not row:
                return False
            expires_at = row["expires_at"]
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            return datetime.now() < expires_at
        except Exception as e:
            logger.error(f"Error checking cache validity: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def _set_cache_metadata(self, cache_key: str, data_type: str):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            ttl = TTL_CONFIG.get(data_type, timedelta(hours=24))
            now = datetime.now()
            expires_at = now + ttl
            cursor.execute("""
                INSERT OR REPLACE INTO cache_metadata (key, data_type, created_at, expires_at)
                VALUES (?, ?, ?, ?)
            """, (f"cache_{cache_key}", data_type, now.isoformat(), expires_at.isoformat()))
            conn.commit()
        except Exception as e:
            logger.error(f"Error setting cache metadata: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def _call_api(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        try:
            url = f"{API_BASE}{endpoint}"
            logger.info(f"API Request: GET {url}  params={params}")
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded (10 req/min en free tier)")
                return None
            elif response.status_code == 403:
                logger.error("Acceso denegado - verifica FOOTBALL_DATA_KEY o el plan de suscripcion")
                return None
            else:
                logger.error(f"API Error {response.status_code}: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    def get_ligas(self, force_refresh: bool = False) -> List[Dict]:
        if not force_refresh and self._is_cache_valid("ligas"):
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ligas_cache")
                rows = [dict(row) for row in cursor.fetchall()]
                if rows:
                    logger.info("Returning cached leagues")
                    return rows
            except Exception as e:
                logger.error(f"Error reading ligas_cache: {e}")
            finally:
                if conn:
                    conn.close()

        result = self._call_api("/competitions")
        if not result or "competitions" not in result:
            return []

        ligas = []
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ligas_cache")

            for comp in result.get("competitions", []):
                current_season = comp.get("currentSeason") or {}
                start_date = current_season.get("startDate", "")
                season_year = int(start_date[:4]) if start_date else None

                liga_data = {
                    "id":      comp.get("id"),
                    "name":    comp.get("name"),
                    "country": (comp.get("area") or {}).get("name"),
                    "logo":    comp.get("emblem"),
                    "season":  season_year,
                }
                ligas.append(liga_data)

                cursor.execute("""
                    INSERT OR REPLACE INTO ligas_cache (id, name, country, logo, season, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    liga_data["id"], liga_data["name"], liga_data["country"],
                    liga_data["logo"], liga_data["season"], datetime.now().isoformat()
                ))

            conn.commit()
            self._set_cache_metadata("ligas", "ligas")
            logger.info(f"Cached {len(ligas)} leagues")
        except Exception as e:
            logger.error(f"Error caching leagues: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

        return ligas

    def get_equipos(self, liga_id: int, force_refresh: bool = False) -> List[Dict]:
        cache_key = f"equipos_{liga_id}"

        if not force_refresh and self._is_cache_valid(cache_key):
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM equipos_cache WHERE liga_id = ?", (liga_id,))
                rows = [dict(row) for row in cursor.fetchall()]
                if rows:
                    logger.info(f"Returning cached teams for competition {liga_id}")
                    return rows
            except Exception as e:
                logger.error(f"Error reading equipos_cache: {e}")
            finally:
                if conn:
                    conn.close()

        result = self._call_api(f"/competitions/{liga_id}/teams")
        if not result or "teams" not in result:
            return []

        equipos = []
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM equipos_cache WHERE liga_id = ?", (liga_id,))

            for team in result.get("teams", []):
                equipo_data = {
                    "id":      team.get("id"),
                    "liga_id": liga_id,
                    "name":    team.get("name"),
                    "logo":    team.get("crest"),
                }
                equipos.append(equipo_data)

                cursor.execute("""
                    INSERT OR REPLACE INTO equipos_cache (id, liga_id, name, logo, fetched_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    equipo_data["id"], equipo_data["liga_id"],
                    equipo_data["name"], equipo_data["logo"], datetime.now().isoformat()
                ))

            conn.commit()
            self._set_cache_metadata(cache_key, "equipos")
            logger.info(f"Cached {len(equipos)} teams for competition {liga_id}")
        except Exception as e:
            logger.error(f"Error caching teams: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

        return equipos

    def get_partidos(self, liga_id: int, temporada: int = 2024, force_refresh: bool = False) -> List[Dict]:
        cache_key = f"partidos_{liga_id}_{temporada}"

        if not force_refresh and self._is_cache_valid(cache_key):
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM partidos_cache
                    WHERE liga_id = ? AND temporada = ?
                """, (liga_id, temporada))
                rows = [dict(row) for row in cursor.fetchall()]
                if rows:
                    logger.info(f"Returning cached matches for competition {liga_id}")
                    return rows
            except Exception as e:
                logger.error(f"Error reading partidos_cache: {e}")
            finally:
                if conn:
                    conn.close()

        result = self._call_api(
            f"/competitions/{liga_id}/matches",
            {"season": temporada, "status": "FINISHED"}
        )
        if not result or "matches" not in result:
            return []

        partidos = []
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM partidos_cache WHERE liga_id = ? AND temporada = ?",
                (liga_id, temporada)
            )

            for match in result.get("matches", []):
                score = match.get("score", {})
                full_time = score.get("fullTime", {})

                partido_data = {
                    "id":                  match.get("id"),
                    "equipo_local_id":     (match.get("homeTeam") or {}).get("id"),
                    "equipo_visitante_id": (match.get("awayTeam") or {}).get("id"),
                    "fecha":               match.get("utcDate"),
                    "jornada":             match.get("matchday"),
                    "goles_local":         full_time.get("home"),
                    "goles_visitante":     full_time.get("away"),
                    "estado":              match.get("status"),
                    "tiempo":              match.get("minute"),
                    "liga_id":             liga_id,
                    "temporada":           temporada,
                }
                partidos.append(partido_data)

                cursor.execute("""
                    INSERT OR REPLACE INTO partidos_cache
                        (id, equipo_local_id, equipo_visitante_id, fecha, jornada,
                         goles_local, goles_visitante, estado, tiempo, liga_id, temporada, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    partido_data["id"],          partido_data["equipo_local_id"],
                    partido_data["equipo_visitante_id"], partido_data["fecha"],
                    partido_data["jornada"],     partido_data["goles_local"],
                    partido_data["goles_visitante"], partido_data["estado"],
                    partido_data["tiempo"],      partido_data["liga_id"],
                    partido_data["temporada"],   datetime.now().isoformat()
                ))

            conn.commit()
            self._set_cache_metadata(cache_key, "partidos")
            logger.info(f"Cached {len(partidos)} matches for competition {liga_id}")
        except Exception as e:
            logger.error(f"Error caching matches: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

        return partidos

    def get_cache_status(self) -> Dict:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM cache_metadata")
            cache_rows = cursor.fetchall()

            cursor.execute("SELECT COUNT(*) as count FROM ligas_cache")
            ligas_count = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM equipos_cache")
            equipos_count = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM partidos_cache")
            partidos_count = cursor.fetchone()["count"]

            cache_info = {}
            for row in cache_rows:
                expires_at = row["expires_at"]
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)
                is_valid = datetime.now() < expires_at
                cache_info[row["key"]] = {
                    "type":               row["data_type"],
                    "created_at":         row["created_at"],
                    "expires_at":         row["expires_at"],
                    "is_valid":           is_valid,
                    "expires_in_minutes": max(0, int((expires_at - datetime.now()).total_seconds() / 60))
                }

            return {
                "ligas_count":    ligas_count,
                "equipos_count":  equipos_count,
                "partidos_count": partidos_count,
                "cache_entries":  cache_info,
                "ttl_config": {
                    "ligas":    f"{int(TTL_CONFIG['ligas'].total_seconds()    / 3600)}h",
                    "equipos":  f"{int(TTL_CONFIG['equipos'].total_seconds()  / 3600)}h",
                    "partidos": f"{int(TTL_CONFIG['partidos'].total_seconds() / 3600)}h",
                }
            }
        except Exception as e:
            logger.error(f"Error getting cache status: {e}")
            return {
                "ligas_count": 0, "equipos_count": 0, "partidos_count": 0,
                "cache_entries": {},
                "ttl_config": {
                    "ligas":    f"{int(TTL_CONFIG['ligas'].total_seconds()    / 3600)}h",
                    "equipos":  f"{int(TTL_CONFIG['equipos'].total_seconds()  / 3600)}h",
                    "partidos": f"{int(TTL_CONFIG['partidos'].total_seconds() / 3600)}h",
                }
            }
        finally:
            if conn:
                conn.close()

    def clear_cache(self, data_type: Optional[str] = None):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if data_type in ("ligas", None):
                cursor.execute("DELETE FROM ligas_cache")
                cursor.execute("DELETE FROM cache_metadata WHERE key = ?", ("cache_ligas",))

            if data_type in ("equipos", None):
                cursor.execute("DELETE FROM equipos_cache")
                cursor.execute("DELETE FROM cache_metadata WHERE key LIKE ?", ("cache_equipos_%",))

            if data_type in ("partidos", None):
                cursor.execute("DELETE FROM partidos_cache")
                cursor.execute("DELETE FROM cache_metadata WHERE key LIKE ?", ("cache_partidos_%",))

            conn.commit()
            logger.info(f"Cache cleared: {data_type or 'all'}")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
