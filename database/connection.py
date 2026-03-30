import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from config import DATABASE_PATH
from core import get_logger, DatabaseException

logger = get_logger(__name__)


class DatabaseConnection:
    _instance: Optional["DatabaseConnection"] = None
    _connection: Optional[sqlite3.Connection] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._connection is None:
            self._connect()

    def _connect(self):
        try:
            DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._create_tables()
            logger.info(f"Base de datos conectada: {DATABASE_PATH}")
        except sqlite3.Error as e:
            logger.error(f"Error conectando a la base de datos: {e}")
            raise DatabaseException("Error al conectar con la base de datos", str(e))

    def _create_tables(self):
        cursor = self._connection.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS ligas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                pais TEXT
            );

            CREATE TABLE IF NOT EXISTS temporadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                fecha_inicio DATE,
                fecha_fin DATE,
                liga_id INTEGER NOT NULL,
                FOREIGN KEY (liga_id) REFERENCES ligas(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS equipos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                liga_id INTEGER NOT NULL,
                FOREIGN KEY (liga_id) REFERENCES ligas(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS partidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP,
                equipo_local INTEGER NOT NULL,
                equipo_visitante INTEGER NOT NULL,
                goles_local INTEGER DEFAULT 0,
                goles_visitante INTEGER DEFAULT 0,
                arbitro TEXT,
                estadio TEXT,
                temporada_id INTEGER NOT NULL,
                FOREIGN KEY (equipo_local) REFERENCES equipos(id) ON DELETE CASCADE,
                FOREIGN KEY (equipo_visitante) REFERENCES equipos(id) ON DELETE CASCADE,
                FOREIGN KEY (temporada_id) REFERENCES temporadas(id) ON DELETE CASCADE
            );
        """)
        self._connection.commit()

    def get_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            raise DatabaseException("No hay conexión activa")
        return self._connection

    @contextmanager
    def transaction(self):
        cursor = self._connection.cursor()
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            logger.error(f"Error en transacción: {e}")
            raise

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Conexión cerrada")


def get_db() -> DatabaseConnection:
    return DatabaseConnection()
