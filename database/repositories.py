from typing import List, Dict, Any, Optional
from database.connection import DatabaseConnection
from core import get_logger, DatabaseException, ResourceNotFoundError
from utils import validar_nombre_texto, validar_pais, validar_id, validar_texto_opcional

logger = get_logger(__name__)


class BaseRepository:
    def __init__(self, db: DatabaseConnection, table_name: str):
        self.db = db
        self.table_name = table_name
        self._conn = db.get_connection()

    def _row_to_dict(self, row) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        return dict(row)

    def _rows_to_list(self, rows) -> List[Dict[str, Any]]:
        return [dict(row) for row in rows]


class LigaRepository(BaseRepository):
    def __init__(self, db: DatabaseConnection):
        super().__init__(db, "ligas")

    def crear(self, nombre: str, pais: str = None) -> int:
        try:
            nombre = validar_nombre_texto(nombre, "nombre")
            pais = validar_pais(pais)
            
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT INTO ligas (nombre, pais) VALUES (?, ?)",
                (nombre, pais)
            )
            self._conn.commit()
            liga_id = cursor.lastrowid
            logger.info(f"Liga creada: {nombre} (ID: {liga_id})")
            return liga_id
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Error creando liga: {e}")
            raise DatabaseException("Error al crear liga", str(e))

    def obtener_todos(self) -> List[Dict[str, Any]]:
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM ligas ORDER BY nombre")
            return self._rows_to_list(cursor.fetchall())
        except Exception as e:
            logger.error(f"Error obteniendo ligas: {e}")
            raise DatabaseException("Error al obtener ligas", str(e))

    def obtener_por_id(self, id: int) -> Optional[Dict[str, Any]]:
        try:
            validar_id(id, "id")
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM ligas WHERE id = ?", (id,))
            return self._row_to_dict(cursor.fetchone())
        except Exception as e:
            logger.error(f"Error obteniendo liga {id}: {e}")
            raise DatabaseException("Error al obtener liga", str(e))

    def actualizar(self, id: int, nombre: str, pais: str = None) -> bool:
        try:
            validar_id(id, "id")
            nombre = validar_nombre_texto(nombre, "nombre")
            pais = validar_pais(pais)
            
            cursor = self._conn.cursor()
            cursor.execute(
                "UPDATE ligas SET nombre = ?, pais = ? WHERE id = ?",
                (nombre, pais, id)
            )
            self._conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Error actualizando liga: {e}")
            raise DatabaseException("Error al actualizar liga", str(e))

    def eliminar(self, id: int) -> bool:
        try:
            validar_id(id, "id")
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM ligas WHERE id = ?", (id,))
            self._conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Error eliminando liga: {e}")
            raise DatabaseException("Error al eliminar liga", str(e))


class TemporadaRepository(BaseRepository):
    def __init__(self, db: DatabaseConnection):
        super().__init__(db, "temporadas")

    def crear(self, nombre: str, fecha_inicio: str, fecha_fin: str, liga_id: int) -> int:
        try:
            nombre = validar_nombre_texto(nombre, "nombre")
            liga_id = validar_id(liga_id, "liga_id")
            
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT INTO temporadas (nombre, fecha_inicio, fecha_fin, liga_id) VALUES (?, ?, ?, ?)",
                (nombre, fecha_inicio, fecha_fin, liga_id)
            )
            self._conn.commit()
            temp_id = cursor.lastrowid
            logger.info(f"Temporada creada: {nombre} (ID: {temp_id})")
            return temp_id
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Error creando temporada: {e}")
            raise DatabaseException("Error al crear temporada", str(e))

    def obtener_por_liga(self, liga_id: int) -> List[Dict[str, Any]]:
        try:
            liga_id = validar_id(liga_id, "liga_id")
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT * FROM temporadas WHERE liga_id = ? ORDER BY nombre",
                (liga_id,)
            )
            return self._rows_to_list(cursor.fetchall())
        except Exception as e:
            logger.error(f"Error obteniendo temporadas: {e}")
            raise DatabaseException("Error al obtener temporadas", str(e))

    def obtener_por_id(self, id: int) -> Optional[Dict[str, Any]]:
        try:
            validar_id(id, "id")
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM temporadas WHERE id = ?", (id,))
            return self._row_to_dict(cursor.fetchone())
        except Exception as e:
            logger.error(f"Error obteniendo temporada {id}: {e}")
            raise DatabaseException("Error al obtener temporada", str(e))


class EquipoRepository(BaseRepository):
    def __init__(self, db: DatabaseConnection):
        super().__init__(db, "equipos")

    def crear(self, nombre: str, liga_id: int) -> int:
        try:
            nombre = validar_nombre_texto(nombre, "nombre")
            liga_id = validar_id(liga_id, "liga_id")
            
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT INTO equipos (nombre, liga_id) VALUES (?, ?)",
                (nombre, liga_id)
            )
            self._conn.commit()
            equipo_id = cursor.lastrowid
            logger.info(f"Equipo creado: {nombre} (ID: {equipo_id})")
            return equipo_id
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Error creando equipo: {e}")
            raise DatabaseException("Error al crear equipo", str(e))

    def obtener_todos(self) -> List[Dict[str, Any]]:
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM equipos ORDER BY nombre")
            return self._rows_to_list(cursor.fetchall())
        except Exception as e:
            logger.error(f"Error obteniendo equipos: {e}")
            raise DatabaseException("Error al obtener equipos", str(e))

    def obtener_por_liga(self, liga_id: int) -> List[Dict[str, Any]]:
        try:
            liga_id = validar_id(liga_id, "liga_id")
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT * FROM equipos WHERE liga_id = ? ORDER BY nombre",
                (liga_id,)
            )
            return self._rows_to_list(cursor.fetchall())
        except Exception as e:
            logger.error(f"Error obteniendo equipos por liga: {e}")
            raise DatabaseException("Error al obtener equipos", str(e))

    def obtener_por_id(self, id: int) -> Optional[Dict[str, Any]]:
        try:
            validar_id(id, "id")
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM equipos WHERE id = ?", (id,))
            return self._row_to_dict(cursor.fetchone())
        except Exception as e:
            logger.error(f"Error obteniendo equipo {id}: {e}")
            raise DatabaseException("Error al obtener equipo", str(e))


class PartidoRepository(BaseRepository):
    def __init__(self, db: DatabaseConnection):
        super().__init__(db, "partidos")

    def crear(
        self,
        fecha: str,
        equipo_local: int,
        equipo_visitante: int,
        goles_local: int,
        goles_visitante: int,
        arbitro: str,
        estadio: str,
        temporada_id: int,
    ) -> int:
        try:
            equipo_local = validar_id(equipo_local, "equipo_local")
            equipo_visitante = validar_id(equipo_visitante, "equipo_visitante")
            temporada_id = validar_id(temporada_id, "temporada_id")
            
            if equipo_local == equipo_visitante:
                raise DatabaseException("El equipo local y visitante no pueden ser el mismo")
            
            cursor = self._conn.cursor()
            cursor.execute(
                """INSERT INTO partidos 
                (fecha, equipo_local, equipo_visitante, goles_local, goles_visitante, arbitro, estadio, temporada_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (fecha, equipo_local, equipo_visitante, goles_local, goles_visitante, arbitro, estadio, temporada_id)
            )
            self._conn.commit()
            partido_id = cursor.lastrowid
            logger.info(f"Partido creado (ID: {partido_id})")
            return partido_id
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Error creando partido: {e}")
            raise DatabaseException("Error al crear partido", str(e))

    def obtener_todos(self) -> List[Dict[str, Any]]:
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM partidos ORDER BY fecha")
            return self._rows_to_list(cursor.fetchall())
        except Exception as e:
            logger.error(f"Error obteniendo partidos: {e}")
            raise DatabaseException("Error al obtener partidos", str(e))

    def obtener_por_temporada(self, temporada_id: int) -> List[Dict[str, Any]]:
        try:
            temporada_id = validar_id(temporada_id, "temporada_id")
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT * FROM partidos WHERE temporada_id = ? ORDER BY fecha",
                (temporada_id,)
            )
            return self._rows_to_list(cursor.fetchall())
        except Exception as e:
            logger.error(f"Error obteniendo partidos por temporada: {e}")
            raise DatabaseException("Error al obtener partidos", str(e))

    def obtener_por_id(self, id: int) -> Optional[Dict[str, Any]]:
        try:
            validar_id(id, "id")
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM partidos WHERE id = ?", (id,))
            return self._row_to_dict(cursor.fetchone())
        except Exception as e:
            logger.error(f"Error obteniendo partido {id}: {e}")
            raise DatabaseException("Error al obtener partido", str(e))

    def actualizar_resultado(self, id: int, goles_local: int, goles_visitante: int) -> bool:
        try:
            validar_id(id, "id")
            goles_local = validar_id(goles_local, "goles_local")
            goles_visitante = validar_id(goles_visitante, "goles_visitante")
            
            cursor = self._conn.cursor()
            cursor.execute(
                "UPDATE partidos SET goles_local = ?, goles_visitante = ? WHERE id = ?",
                (goles_local, goles_visitante, id)
            )
            self._conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Error actualizando resultado: {e}")
            raise DatabaseException("Error al actualizar resultado", str(e))
