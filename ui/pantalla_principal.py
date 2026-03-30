import customtkinter as ctk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.app import App

from ui.formularios import FormularioLiga
from core import DatabaseException
from ui.dialogs import mostrar_error, mostrar_exito


class PantallaPrincipal(ctk.CTkFrame):
    def __init__(self, parent, controller: "App"):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(
            self, text="Ligas de Futbol", font=ctk.CTkFont(size=28, weight="bold")
        ).pack(pady=30)

        self.ligas_listbox = ctk.CTkScrollableFrame(self, height=300, width=500)
        self.ligas_listbox.pack(pady=20)

        ctk.CTkButton(
            self, text="+ Agregar Liga", command=self.abrir_formulario_agregar, width=200, height=40
        ).pack(pady=20)

        self.cargar_ligas()

    def cargar_ligas(self):
        for widget in self.ligas_listbox.winfo_children():
            widget.destroy()

        try:
            from database import get_db, LigaRepository
            db = get_db()
            repo = LigaRepository(db)
            ligas = repo.obtener_todos()

            if not ligas:
                ctk.CTkLabel(
                    self.ligas_listbox, text="No hay ligas. Agrega una!", text_color="gray"
                ).pack(pady=20)
                return

            for liga in ligas:
                frame = ctk.CTkFrame(self.ligas_listbox, fg_color=("gray80", "gray30"))
                frame.pack(fill="x", pady=5, padx=10)

                ctk.CTkButton(
                    frame, text=f"{liga['nombre']} ({liga['pais']})",
                    command=lambda lid=liga['id']: self.ver_liga(lid),
                    fg_color="transparent", hover_color=("gray70", "gray40"), height=45, width=400
                ).pack(side="left", padx=(5, 0))

                ctk.CTkButton(
                    frame, text="x", command=lambda lid=liga['id']: self.eliminar_liga(lid),
                    width=40, fg_color="transparent", text_color=("red", "#ff6666"),
                    hover_color=("gray70", "gray40")
                ).pack(side="right", padx=(0, 5))

        except DatabaseException as e:
            mostrar_error(self, str(e))

    def abrir_formulario_agregar(self):
        FormularioLiga(self, callback=self.cargar_ligas)

    def ver_liga(self, liga_id: int):
        self.controller.show_frame("PantallaLiga", liga_id=liga_id)

    def eliminar_liga(self, liga_id: int):
        try:
            from database import get_db, LigaRepository
            db = get_db()
            repo = LigaRepository(db)
            repo.eliminar(liga_id)
            mostrar_exito(self, "Liga eliminada exitosamente")
            self.cargar_ligas()
        except DatabaseException as e:
            mostrar_error(self, str(e))
