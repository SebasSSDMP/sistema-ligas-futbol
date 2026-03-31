import psycopg2
import psycopg2.extras
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = "https://v3.football.api-sports.io"
API_KEY = os.environ.get("API_FOOTBALL_KEY", "")
HEADERS = {"x-apisports-key": API_KEY} if API_KEY else {}

TTL_CONFIG = {
    "ligas": timedelta(hours=24),
    "equipos": timedelta(hours=24),
    "partidos": timedelta(hours=1),
}


class APIFootballCache:
    def __init__(self):
        self._init_cache_tables()
        # Initialize cache tables only when explicitly called
        pass
    
    def _get_connection(self):
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        
        # Handle postgres:// vs postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        conn = psycopg2.connect(database_url)
        # Return dict-like rows
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn
    
    def _init_cache_tables(self):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    key TEXT PRIMARY KEY,
                    data_type TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ligas_cache (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    country TEXT,
                    logo TEXT,
                    season INTEGER,
                    fetched_at TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS equipos_cache (
                    id INTEGER PRIMARY KEY,
                    liga_id INTEGER,
                    name TEXT,
                    logo TEXT,
                    fetched_at TIMESTAMP
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
                    tiempo TEXT,
                    liga_id INTEGER,
                    temporada INTEGER,
                    fetched_at TIMESTAMP
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
    
    def _is_cache_valid(self, data_type: str) -> bool:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT expires_at FROM cache_metadata WHERE key = %s",
                (f"cache_{data_type}",)
            )
            row = cursor.fetchone()
            
            if not row:
                return False
            
            expires_at = row["expires_at"]
            # Handle both string and datetime objects
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            return datetime.now() < expires_at
        except Exception as e:
            logger.error(f"Error checking cache validity: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def _set_cache_metadata(self, data_type: str):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            ttl = TTL_CONFIG.get(data_type, timedelta(hours=24))
            now = datetime.now()
            expires_at = now + ttl
            
            cursor.execute("""
                INSERT INTO cache_metadata (key, data_type, created_at, expires_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (key) DO UPDATE SET
                    data_type = EXCLUDED.data_type,
                    created_at = EXCLUDED.created_at,
                    expires_at = EXCLUDED.expires_at
            """, (f"cache_{data_type}", data_type, now, expires_at))
            
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
            logger.info(f"API Request: {endpoint} - {params}")
            response = requests.get(
                f"{API_BASE}{endpoint}",
                headers=HEADERS,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded")
                return None
            else:
                logger.error(f"API Error: {response.status_code} - {response.text}")
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
                logger.error(f"Error reading from ligas_cache: {e}")
            finally:
                if conn:
                    conn.close()
        
        result = self._call_api("/leagues", {"current": "true"})
        if not result or "response" not in result:
            return []
        
        ligas = []
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ligas_cache")
            
            for item in result.get("response", []):
                league = item.get("league", {})
                country = item.get("country", {})
                
                liga_data = {
                    "id": league.get("id"),
                    "name": league.get("name"),
                    "country": country.get("name"),
                    "logo": league.get("logo"),
                    "season": item.get("seasons", [{}])[-1].get("year") if item.get("seasons") else None,
                }
                ligas.append(liga_data)
                
                cursor.execute("""
                    INSERT INTO ligas_cache (id, name, country, logo, season, fetched_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        country = EXCLUDED.country,
                        logo = EXCLUDED.logo,
                        season = EXCLUDED.season,
                        fetched_at = EXCLUDED.fetched_at
                """, (
                    liga_data["id"], liga_data["name"], liga_data["country"],
                    liga_data["logo"], liga_data["season"], datetime.now()
                ))
            
            conn.commit()
            self._set_cache_metadata("ligas")
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
                cursor.execute("SELECT * FROM equipos_cache WHERE liga_id = %s", (liga_id,))
                rows = [dict(row) for row in cursor.fetchall()]
                if rows:
                    logger.info(f"Returning cached teams for league {liga_id}")
                    return rows
            except Exception as e:
                logger.error(f"Error reading from equipos_cache: {e}")
            finally:
                if conn:
                    conn.close()
        
        result = self._call_api("/teams", {"league": liga_id, "season": "2024"})
        if not result or "response" not in result:
            return []
        
        equipos = []
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM equipos_cache WHERE liga_id = %s", (liga_id,))
            
            for item in result.get("response", []):
                team = item.get("team", {})
                venue = item.get("venue", {})
                
                equipo_data = {
                    "id": team.get("id"),
                    "liga_id": liga_id,
                    "name": team.get("name"),
                    "logo": team.get("logo"),
                }
                equipos.append(equipo_data)
                
                cursor.execute("""
                    INSERT INTO equipos_cache (id, liga_id, name, logo, fetched_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        liga_id = EXCLUDED.liga_id,
                        name = EXCLUDED.name,
                        logo = EXCLUDED.logo,
                        fetched_at = EXCLUDED.fetched_at
                """, (
                    equipo_data["id"], equipo_data["liga_id"], equipo_data["name"],
                    equipo_data["logo"], datetime.now()
                ))
            
            conn.commit()
            
            # Update cache metadata
            cache_conn = None
            try:
                cache_conn = self._get_connection()
                cache_cursor = cache_conn.cursor()
                now = datetime.now()
                expires_at = now + TTL_CONFIG["equipos"]
                cache_cursor.execute("""
                    INSERT INTO cache_metadata (key, data_type, created_at, expires_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (key) DO UPDATE SET
                        data_type = EXCLUDED.data_type,
                        created_at = EXCLUDED.created_at,
                        expires_at = EXCLUDED.expires_at
                """, (cache_key, f"equipos_{liga_id}", now, expires_at))
                cache_conn.commit()
            except Exception as e:
                logger.error(f"Error updating cache metadata: {e}")
                if cache_conn:
                    cache_conn.rollback()
            finally:
                if cache_conn:
                    cache_conn.close()
            
            logger.info(f"Cached {len(equipos)} teams for league {liga_id}")
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
                    WHERE liga_id = %s AND temporada = %s
                """, (liga_id, temporada))
                rows = [dict(row) for row in cursor.fetchall()]
                if rows:
                    logger.info(f"Returning cached matches for league {liga_id}")
                    return rows
            except Exception as e:
                logger.error(f"Error reading from partidos_cache: {e}")
            finally:
                if conn:
                    conn.close()
        
        result = self._call_api("/fixtures", {
            "league": liga_id,
            "season": temporada,
            "status": "FT"
        })
        
        if not result or "response" not in result:
            return []
        
        partidos = []
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM partidos_cache WHERE liga_id = %s AND temporada = %s", (liga_id, temporada))
            
            for item in result.get("response", []):
                fixture = item.get("fixture", {})
                teams = item.get("teams", {})
                goals = item.get("goals", {})
                
                partido_data = {
                    "id": fixture.get("id"),
                    "equipo_local_id": teams.get("home", {}).get("id"),
                    "equipo_visitante_id": teams.get("away", {}).get("id"),
                    "fecha": fixture.get("date"),
                    "jornada": fixture.get("round", "").replace(f"Ronda {temporada} - ", ""),
                    "goles_local": goals.get("home"),
                    "goles_visitante": goals.get("away"),
                    "estado": fixture.get("status", {}).get("short"),
                    "tiempo": fixture.get("status", {}).get("elapsed"),
                    "liga_id": liga_id,
                    "temporada": temporada,
                }
                partidos.append(partido_data)
                
                cursor.execute("""
                    INSERT INTO partidos_cache 
                    (id, equipo_local_id, equipo_visitante_id, fecha, jornada, 
                     goles_local, goles_visitante, estado, tiempo, liga_id, temporada, fetched_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        equipo_local_id = EXCLUDED.equipo_local_id,
                        equipo_visitante_id = EXCLUDED.equipo_visitante_id,
                        fecha = EXCLUDED.fecha,
                        jornada = EXCLUDED.jornada,
                        goles_local = EXCLUDED.goles_local,
                        goles_visitante = EXCLUDED.goles_visitante,
                        estado = EXCLUDED.estado,
                        tiempo = EXCLUDED.tiempo,
                        liga_id = EXCLUDED.liga_id,
                        temporada = EXCLUDED.temporada,
                        fetched_at = EXCLUDED.fetched_at
                """, (
                    partido_data["id"], partido_data["equipo_local_id"],
                    partido_data["equipo_visitante_id"], partido_data["fecha"],
                    partido_data["jornada"], partido_data["goles_local"],
                    partido_data["goles_visitante"], partido_data["estado"],
                    partido_data["tiempo"], partido_data["liga_id"],
                    partido_data["temporada"], datetime.now()
                ))
            
            conn.commit()
            
            # Update cache metadata
            cache_conn = None
            try:
                cache_conn = self._get_connection()
                cache_cursor = cache_conn.cursor()
                now = datetime.now()
                expires_at = now + TTL_CONFIG["partidos"]
                cache_cursor.execute("""
                    INSERT INTO cache_metadata (key, data_type, created_at, expires_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (key) DO UPDATE SET
                        data_type = EXCLUDED.data_type,
                        created_at = EXCLUDED.created_at,
                        expires_at = EXCLUDED.expires_at
                """, (cache_key, cache_key, now, expires_at))
                cache_conn.commit()
            except Exception as e:
                logger.error(f"Error updating cache metadata: {e}")
                if cache_conn:
                    cache_conn.rollback()
            finally:
                if cache_conn:
                    cache_conn.close()
            
            logger.info(f"Cached {len(partidos)} matches for league {liga_id}")
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
                # Handle both string and datetime objects
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)
                is_valid = datetime.now() < expires_at
                cache_info[row["key"]] = {
                    "type": row["data_type"],
                    "created_at": row["created_at"],
                    "expires_at": row["expires_at"],
                    "is_valid": is_valid,
                    "expires_in_minutes": max(0, int((expires_at - datetime.now()).total_seconds() / 60))
                }
            
            return {
                "ligas_count": ligas_count,
                "equipos_count": equipos_count,
                "partidos_count": partidos_count,
                "cache_entries": cache_info,
                "ttl_config": {
                    "ligas": f"{int(TTL_CONFIG['ligas'].total_seconds() / 3600)}h",
                    "equipos": f"{int(TTL_CONFIG['equipos'].total_seconds() / 3600)}h",
                    "partidos": f"{int(TTL_CONFIG['partidos'].total_seconds() / 3600)}h"
                }
            }
        except Exception as e:
            logger.error(f"Error getting cache status: {e}")
            return {
                "ligas_count": 0,
                "equipos_count": 0,
                "partidos_count": 0,
                "cache_entries": {},
                "ttl_config": {
                    "ligas": f"{int(TTL_CONFIG['ligas'].total_seconds() / 3600)}h",
                    "equipos": f"{int(TTL_CONFIG['equipos'].total_seconds() / 3600)}h",
                    "partidos": f"{int(TTL_CONFIG['partidos'].total_seconds() / 3600)}h"
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
            
            if data_type == "ligas" or data_type is None:
                cursor.execute("DELETE FROM ligas_cache")
                cursor.execute("DELETE FROM cache_metadata WHERE key = %s", ("cache_ligas",))
            
            if data_type == "equipos" or data_type is None:
                cursor.execute("DELETE FROM equipos_cache")
                cursor.execute("DELETE FROM cache_metadata WHERE key LIKE %s", ("cache_equipos_%",))
            
            if data_type == "partidos" or data_type is None:
                cursor.execute("DELETE FROM partidos_cache")
                cursor.execute("DELETE FROM cache_metadata WHERE key LIKE %s", ("cache_partidos_%",))
            
            conn.commit()
            logger.info(f"Cache cleared for type: {data_type or 'all'}")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

# Cache instance will be created when needed in the API endpoints
# cache = APIFootballCache()
