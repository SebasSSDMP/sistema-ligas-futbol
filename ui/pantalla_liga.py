import customtkinter as ctk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.app import App

from ui.formularios import FormularioTemporada, FormularioPartido, FormularioEquipo


class PantallaLiga(ctk.CTkFrame):
    def __init__(self, parent, controller: "App", liga_id: int):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.liga_id = liga_id

        from database import get_db, LigaRepository
        db = get_db()
        liga = LigaRepository(db).obtener_por_id(liga_id)
        if not liga:
            self.volver()
            return

        self.nombre_liga = liga["nombre"]
        self.pais_liga = liga["pais"]

        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=20, padx=40)

        ctk.CTkButton(self.header, text="← Volver", command=self.volver, width=100).pack(side="left")

        ctk.CTkLabel(
            self.header, text=self.nombre_liga, font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left", padx=20)

        ctk.CTkLabel(self.header, text=f"País: {self.pais_liga}", font=ctk.CTkFont(size=14)).pack(side="left")

        self.tabs = ctk.CTkTabview(self, width=700, height=400)
        self.tabs.pack(pady=20, padx=40, fill="both", expand=True)

        self.tabs.add("Temporadas")
        self.tabs.add("Equipos")
        self.tabs.add("Partidos")
        self.tabs.add("Acciones")

        self.cargar_temporadas()
        self.cargar_equipos()
        self.cargar_partidos()
        self.configurar_acciones()

    def volver(self):
        self.controller.show_frame("PantallaPrincipal")

    def cargar_temporadas(self):
        frame = self.tabs.tab("Temporadas")
        for widget in frame.winfo_children():
            widget.destroy()

        from database import get_db, TemporadaRepository
        db = get_db()
        temporadas = TemporadaRepository(db).obtener_por_liga(self.liga_id)

        listbox = ctk.CTkScrollableFrame(frame, height=280)
        listbox.pack(fill="both", expand=True, padx=10, pady=10)

        if not temporadas:
            ctk.CTkLabel(listbox, text="No hay temporadas", text_color="gray").pack(pady=20)
        else:
            for t in temporadas:
                ctk.CTkLabel(listbox, text=f"{t['nombre']} ({t['fecha_inicio']} - {t['fecha_fin']})",
                             font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5, padx=10)

    def cargar_equipos(self):
        frame = self.tabs.tab("Equipos")
        for widget in frame.winfo_children():
            widget.destroy()

        from database import get_db, EquipoRepository
        db = get_db()
        equipos = EquipoRepository(db).obtener_por_liga(self.liga_id)

        listbox = ctk.CTkScrollableFrame(frame, height=280)
        listbox.pack(fill="both", expand=True, padx=10, pady=10)

        if not equipos:
            ctk.CTkLabel(listbox, text="No hay equipos", text_color="gray").pack(pady=20)
        else:
            for e in equipos:
                ctk.CTkLabel(listbox, text=e["nombre"], font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5, padx=10)

    def cargar_partidos(self):
        frame = self.tabs.tab("Partidos")
        for widget in frame.winfo_children():
            widget.destroy()

        from database import get_db, PartidoRepository, TemporadaRepository, EquipoRepository
        db = get_db()
        temporadas = TemporadaRepository(db).obtener_por_liga(self.liga_id)
        equipos = {e["id"]: e["nombre"] for e in EquipoRepository(db).obtener_por_liga(self.liga_id)}

        listbox = ctk.CTkScrollableFrame(frame, height=280)
        listbox.pack(fill="both", expand=True, padx=10, pady=10)

        if not temporadas:
            ctk.CTkLabel(listbox, text="Agrega una temporada para ver partidos", text_color="gray").pack(pady=20)
            return

        for temp in temporadas:
            partidos = PartidoRepository(db).obtener_por_temporada(temp["id"])
            if partidos:
                ctk.CTkLabel(listbox, text=f"Temporada {temp['nombre']}:", 
                             font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5), padx=5)
                for p in partidos:
                    local = equipos.get(p["equipo_local"], "N/A")
                    visitante = equipos.get(p["equipo_visitante"], "N/A")
                    resultado = f"{p['goles_local']} - {p['goles_visitante']}"
                    ctk.CTkLabel(
                        listbox, 
                        text=f"  {local} {resultado} {visitante} | {p['fecha'][:10]}"
                    ).pack(anchor="w", pady=2, padx=15)

    def configurar_acciones(self):
        frame = self.tabs.tab("Acciones")
        
        acciones = [
            ("+ Agregar Temporada", lambda: FormularioTemporada(self, self.liga_id, callback=self.recargar)),
            ("+ Agregar Equipo", lambda: FormularioEquipo(self, self.liga_id, callback=self.recargar)),
            ("+ Agregar Partido", lambda: FormularioPartido(self, self.liga_id, callback=self.recargar)),
            ("📊 Ver Estadísticas", self.ver_estadisticas),
        ]

        for texto, comando in acciones:
            btn = ctk.CTkButton(frame, text=texto, command=comando, height=45, width=280)
            btn.pack(pady=10)

    def recargar(self):
        self.cargar_temporadas()
        self.cargar_equipos()
        self.cargar_partidos()

    def ver_estadisticas(self):
        self.controller.show_frame("PantallaEstadisticas", liga_id=self.liga_id)
