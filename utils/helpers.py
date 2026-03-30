from typing import Optional, List, Dict, Any, Callable
from functools import wraps
from core.logger import get_logger

logger = get_logger(__name__)


def handle_errors(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error en {func.__name__}: {str(e)}")
            raise
    return wrapper


def safe_execute(func: Callable, default: any = None) -> any:
    try:
        return func()
    except Exception as e:
        logger.error(f"Error en safe_execute: {str(e)}")
        return default


def format_fecha(fecha: Optional[str]) -> str:
    if not fecha:
        return "N/A"
    return fecha[:10]


def formatear_resultado(goles_local: int, goles_visitante: int) -> str:
    return f"{goles_local} - {goles_visitante}"


def get_resultado_partido(goles_local: int, goles_visitante: int) -> str:
    if goles_local > goles_visitante:
        return "local"
    elif goles_local < goles_visitante:
        return "visitante"
    return "empate"


def calcular_puntos(resultado: str) -> tuple:
    if resultado == "ganado":
        return 3, 1, 0, 0
    elif resultado == "empate":
        return 1, 0, 1, 0
    return 0, 0, 0, 1


def convertir_a_dict(row) -> Dict[str, Any]:
    if row is None:
        return {}
    if hasattr(row, '_row'):
        return dict(row._row)
    return dict(row)
