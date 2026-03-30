import customtkinter as ctk
from typing import Optional

from core import DatabaseException, ValidationError, ResourceNotFoundError


class MensajeDialog(ctk.CTkToplevel):
    def __init__(self, parent, titulo: str, mensaje: str, tipo: str = "info"):
        super().__init__(parent)
        self.title(titulo)
        self.geometry("400x180")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        color_map = {
            "error": ("#FF5252", "#FFCDD2"),
            "success": ("#4CAF50", "#C8E6C9"),
            "warning": ("#FFC107", "#FFF9C4"),
            "info": ("#2196F3", "#BBDEFB"),
        }
        bg_color, highlight_color = color_map.get(tipo, color_map["info"])

        frame = ctk.CTkFrame(self, fg_color=("white", "#2b2b2b"))
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        indicador = ctk.CTkFrame(frame, width=50, height=50, fg_color=highlight_color, corner_radius=25)
        indicador.pack(pady=(0, 15))

        simbolos = {"error": "✕", "success": "✓", "warning": "⚠", "info": "i"}
        ctk.CTkLabel(
            indicador, text=simbolos.get(tipo, "i"),
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=bg_color
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            frame, text=mensaje, font=ctk.CTkFont(size=14),
            wraplength=350, justify="center"
        ).pack(pady=(0, 15))

        ctk.CTkButton(frame, text="Aceptar", command=self.destroy, width=120).pack()


def mostrar_error(parent, mensaje: str, titulo: str = "Error"):
    MensajeDialog(parent, titulo, mensaje, "error")


def mostrar_exito(parent, mensaje: str, titulo: str = "Éxito"):
    MensajeDialog(parent, titulo, mensaje, "success")


def mostrar_info(parent, mensaje: str, titulo: str = "Información"):
    MensajeDialog(parent, titulo, mensaje, "info")


def manejar_error_ui(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            parent = args[0] if args else None
            if parent:
                mostrar_error(parent, str(e))
        except DatabaseException as e:
            parent = args[0] if args else None
            if parent:
                mostrar_error(parent, str(e), "Error de Base de Datos")
        except ResourceNotFoundError as e:
            parent = args[0] if args else None
            if parent:
                mostrar_error(parent, str(e), "Recurso No Encontrado")
        except Exception as e:
            parent = args[0] if args else None
            if parent:
                mostrar_error(parent, f"Error inesperado: {str(e)}")
    return wrapper
