from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATABASE_DIR = BASE_DIR / "data"
DATABASE_PATH = DATABASE_DIR / "futbol.db"

DATABASE_DIR.mkdir(parents=True, exist_ok=True)

APP_NAME = "Gestión de Ligas de Fútbol"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 650

THEME = {
    "appearance_mode": "dark",
    "color_theme": "blue",
}

DATABASE_TABLES = [
    "ligas",
    "temporadas",
    "equipos",
    "partidos",
]
