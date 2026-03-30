import customtkinter as ctk
from typing import Callable, Optional

from config import APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT, THEME
from core import get_logger

ctk.set_appearance_mode(THEME["appearance_mode"])
ctk.set_default_color_theme(THEME["color_theme"])

logger = get_logger(__name__)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(True, True)

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        self.frames: dict = {}
        self.current_frame: Optional[ctk.CTkFrame] = None

        self._registrar_pantallas()
        self.show_frame("PantallaPrincipal")

        logger.info("Aplicación iniciada")

    def _registrar_pantallas(self):
        from ui.pantalla_principal import PantallaPrincipal
        from ui.pantalla_liga import PantallaLiga
        from ui.pantalla_estadisticas import PantallaEstadisticas

        self.frames["PantallaPrincipal"] = PantallaPrincipal
        self.frames["PantallaLiga"] = PantallaLiga
        self.frames["PantallaEstadisticas"] = PantallaEstadisticas

    def show_frame(self, name: str, **kwargs):
        frame_class = self.frames.get(name)
        if frame_class is None:
            logger.warning(f"Pantalla no encontrada: {name}")
            return

        if self.current_frame is not None:
            self.current_frame.pack_forget()

        frame = frame_class(self.container, self, **kwargs)
        frame.pack(fill="both", expand=True)
        self.current_frame = frame

        logger.info(f"Navegando a: {name}")

    def volver(self):
        if self.current_frame:
            nombre = type(self.current_frame).__name__
            logger.info(f"Volviendo desde: {nombre}")
