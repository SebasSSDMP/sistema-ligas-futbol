import logging
from pathlib import Path
from datetime import datetime

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_DIR / f"app_{datetime.now():%Y%m%d}.log"),
        logging.StreamHandler(),
    ],
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
