import psycopg2
import psycopg2.extras
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── football-data.org v4 ──────────────────────────────────────────────────────
API_BASE = "https://api.football-data.org/v4"
API_KEY  = os.environ.get("FOOTBALL_DATA_KEY", "")
HEADERS  = {"X-Auth-Token": API_KEY} if API_KEY else {}

TTL_CONFIG = {
    "ligas":    timedelta(hours=24),
    "equipos":  timedelta(hours=24),
    "partidos": timedelta(hours=1),
}


class APIFootballCache:
    def __init__(self):
        self._init_cache_tables()

    # ── DB helpers ────────────────────────────────────────────────────────────

    def _get_connection(self):
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(database_url)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn

    def _init_cache_tables(self):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    key        TEXT PRIMARY KEY,
                    data_type  TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ligas_cache (
                    id         INTEGER PRIMARY KEY,
                    name       TEXT,
                    country    TEXT,
                    logo       TEXT,
                    season     INTEGER,
                    fetched_at TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS equipos_cache (
                    id         INTEGER PRIMARY KEY,
                    liga_id    INTEGER,
                    name       TEXT,
                    logo       TEXT,
                    fetched_at TIMESTAMP
                )
            """)

            # jornada es INTEGER en football-data.org (matchday)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS partidos_cache (
                    id                   INTEGER PRIMARY KEY,
                    equipo_local_id      INTEGER,
                    equipo_visitante_id  INTEGER,
                    fecha                TEXT,
                    jornada              INTEGER,
                    goles_local          INTEGER,
                    goles_visitante      INTEGER,
                    estado               TEXT,
                    tiempo               INTEGER,
                    liga_id              INTEGER,
                    temporada            INTEGER,
                    fetched_at           TIMESTAMP
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
                "SELECT expires_at FROM cache_metadata WHERE key = %s",
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
            ttl        = TTL_CONFIG.get(data_type, timedelta(hours=24))
            now        = datetime.now()
            expires_at = now + ttl
            cursor.execute("""
                INSERT INTO cache_metadata (key, data_type, created_at, expires_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (key) DO UPDATE SET
                    data_type  = EXCLUDED.data_type,
                    created_at = EXCLUDED.created_at,
                    expires_at = EXCLUDED.expires_at
            """, (f"cache_{cache_key}", data_type, now, expires_at))
            conn.commit()
        except Exception as e:
            logger.error(f"Error setting cache metadata: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    # ── HTTP ──────────────────────────────────────────────────────────────────

    def _call_api(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Llama a football-data.org v4.
        Autenticación: header X-Auth-Token.
        Rate-limit free tier: 10 req/min.
        """
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
                logger.error("Acceso denegado — verifica FOOTBALL_DATA_KEY o el plan de suscripción")
                return None
            else:
                logger.error(f"API Error {response.status_code}: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    # ── LIGAS ─────────────────────────────────────────────────────────────────

    def get_ligas(self, force_refresh: bool = False) -> List[Dict]:
        """
        GET /v4/competitions
        Respuesta: { "competitions": [ { "id", "name", "area": {"name"}, "emblem",
                                         "currentSeason": {"startDate", "endDate"} } ] }
        """
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
        conn  = None
        try:
            conn   = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ligas_cache")

            for comp in result.get("competitions", []):
                current_season = comp.get("currentSeason") or {}
                # El año de la temporada se saca del startDate, ej. "2024-08-16" → 2024
                start_date = current_season.get("startDate", "")
                season_year = int(start_date[:4]) if start_date else None

                liga_data = {
                    "id":      comp.get("id"),
                    "name":    comp.get("name"),
                    "country": (comp.get("area") or {}).get("name"),
                    "logo":    comp.get("emblem"),       # football-data usa "emblem"
                    "season":  season_year,
                }
                ligas.append(liga_data)

                cursor.execute("""
                    INSERT INTO ligas_cache (id, name, country, logo, season, fetched_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name       = EXCLUDED.name,
                        country    = EXCLUDED.country,
                        logo       = EXCLUDED.logo,
                        season     = EXCLUDED.season,
                        fetched_at = EXCLUDED.fetched_at
                """, (
                    liga_data["id"], liga_data["name"], liga_data["country"],
                    liga_data["logo"], liga_data["season"], datetime.now()
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

    # ── EQUIPOS ───────────────────────────────────────────────────────────────

    def get_equipos(self, liga_id: int, force_refresh: bool = False) -> List[Dict]:
        """
        GET /v4/competitions/{id}/teams
        Respuesta: { "teams": [ { "id", "name", "crest" } ] }

        Nota: liga_id es el ID numérico de la competición en football-data.org,
        ej. 2021 = Premier League, 2014 = La Liga, etc.
        """
        cache_key = f"equipos_{liga_id}"

        if not force_refresh and self._is_cache_valid(cache_key):
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM equipos_cache WHERE liga_id = %s", (liga_id,))
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
        conn    = None
        try:
            conn   = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM equipos_cache WHERE liga_id = %s", (liga_id,))

            for team in result.get("teams", []):
                equipo_data = {
                    "id":      team.get("id"),
                    "liga_id": liga_id,
                    "name":    team.get("name"),
                    "logo":    team.get("crest"),   # football-data usa "crest"
                }
                equipos.append(equipo_data)

                cursor.execute("""
                    INSERT INTO equipos_cache (id, liga_id, name, logo, fetched_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        liga_id    = EXCLUDED.liga_id,
                        name       = EXCLUDED.name,
                        logo       = EXCLUDED.logo,
                        fetched_at = EXCLUDED.fetched_at
                """, (
                    equipo_data["id"], equipo_data["liga_id"],
                    equipo_data["name"], equipo_data["logo"], datetime.now()
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

    # ── PARTIDOS ──────────────────────────────────────────────────────────────

    def get_partidos(self, liga_id: int, temporada: int = 2024, force_refresh: bool = False) -> List[Dict]:
        """
        GET /v4/competitions/{id}/matches?season={YYYY}&status=FINISHED
        Respuesta:
        {
          "matches": [
            {
              "id", "utcDate", "status", "matchday",
              "homeTeam": { "id", "name" },
              "awayTeam":  { "id", "name" },
              "score": {
                "fullTime": { "home": int|null, "away": int|null }
              },
              "minute": int|null     ← tiempo transcurrido
            }
          ]
        }
        """
        cache_key = f"partidos_{liga_id}_{temporada}"

        if not force_refresh and self._is_cache_valid(cache_key):
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM partidos_cache
                    WHERE liga_id = %s AND temporada = %s
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
        conn     = None
        try:
            conn   = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM partidos_cache WHERE liga_id = %s AND temporada = %s",
                (liga_id, temporada)
            )

            for match in result.get("matches", []):
                score     = match.get("score", {})
                full_time = score.get("fullTime", {})

                partido_data = {
                    "id":                  match.get("id"),
                    "equipo_local_id":     (match.get("homeTeam") or {}).get("id"),
                    "equipo_visitante_id": (match.get("awayTeam") or {}).get("id"),
                    "fecha":               match.get("utcDate"),       # ISO-8601 con Z
                    "jornada":             match.get("matchday"),       # entero
                    "goles_local":         full_time.get("home"),
                    "goles_visitante":     full_time.get("away"),
                    "estado":              match.get("status"),         # "FINISHED", "SCHEDULED", etc.
                    "tiempo":              match.get("minute"),         # minuto transcurrido o null
                    "liga_id":             liga_id,
                    "temporada":           temporada,
                }
                partidos.append(partido_data)

                cursor.execute("""
                    INSERT INTO partidos_cache
                        (id, equipo_local_id, equipo_visitante_id, fecha, jornada,
                         goles_local, goles_visitante, estado, tiempo, liga_id, temporada, fetched_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        equipo_local_id      = EXCLUDED.equipo_local_id,
                        equipo_visitante_id  = EXCLUDED.equipo_visitante_id,
                        fecha                = EXCLUDED.fecha,
                        jornada              = EXCLUDED.jornada,
                        goles_local          = EXCLUDED.goles_local,
                        goles_visitante      = EXCLUDED.goles_visitante,
                        estado               = EXCLUDED.estado,
                        tiempo               = EXCLUDED.tiempo,
                        liga_id              = EXCLUDED.liga_id,
                        temporada            = EXCLUDED.temporada,
                        fetched_at           = EXCLUDED.fetched_at
                """, (
                    partido_data["id"],          partido_data["equipo_local_id"],
                    partido_data["equipo_visitante_id"], partido_data["fecha"],
                    partido_data["jornada"],     partido_data["goles_local"],
                    partido_data["goles_visitante"], partido_data["estado"],
                    partido_data["tiempo"],      partido_data["liga_id"],
                    partido_data["temporada"],   datetime.now()
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

    # ── CACHE STATUS / CLEAR ──────────────────────────────────────────────────

    def get_cache_status(self) -> Dict:
        conn = None
        try:
            conn   = self._get_connection()
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
            conn   = self._get_connection()
            cursor = conn.cursor()

            if data_type in ("ligas", None):
                cursor.execute("DELETE FROM ligas_cache")
                cursor.execute("DELETE FROM cache_metadata WHERE key = %s", ("cache_ligas",))

            if data_type in ("equipos", None):
                cursor.execute("DELETE FROM equipos_cache")
                cursor.execute("DELETE FROM cache_metadata WHERE key LIKE %s", ("cache_equipos_%",))

            if data_type in ("partidos", None):
                cursor.execute("DELETE FROM partidos_cache")
                cursor.execute("DELETE FROM cache_metadata WHERE key LIKE %s", ("cache_partidos_%",))

            conn.commit()
            logger.info(f"Cache cleared: {data_type or 'all'}")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()