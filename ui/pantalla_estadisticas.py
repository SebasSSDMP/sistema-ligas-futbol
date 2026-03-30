import customtkinter as ctk
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ui.app import App

from ui.graficas import GraficaFrame


class PantallaEstadisticas(ctk.CTkFrame):
    def __init__(self, parent, controller: "App", liga_id: int):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.liga_id = liga_id
        self.graficas: list = []

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=20, padx=40)

        ctk.CTkButton(header, text="← Volver", command=self.volver, width=100).pack(side="left")

        from database import get_db, LigaRepository
        db = get_db()
        liga = LigaRepository(db).obtener_por_id(liga_id)

        ctk.CTkLabel(header, text=f"Estadísticas: {liga['nombre'] if liga else 'Liga'}",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(side="left", padx=20)

        self.content = ctk.CTkScrollableFrame(self, height=550, width=900)
        self.content.pack(pady=20, padx=40, fill="both", expand=True)

        self.graficas_container = ctk.CTkFrame(self.content, fg_color="transparent")
        self.graficas_container.pack(fill="both", expand=True, pady=10)

        self.info_container = ctk.CTkFrame(self.content, fg_color="transparent")
        self.info_container.pack(fill="x", pady=10)

        self.cargar_estadisticas()

    def volver(self):
        self.limpiar_graficas()
        self.controller.show_frame("PantallaLiga", liga_id=self.liga_id)

    def limpiar_graficas(self):
        for g in self.graficas:
            g.destruir()
        self.graficas = []

    def cargar_estadisticas(self):
        from database import (
            obtener_estadisticas_liga,
            ranking_ligas_por_promedio_goles,
        )

        stats = obtener_estadisticas_liga(self.liga_id)
        ranking = ranking_ligas_por_promedio_goles()
        posicion_ranking = next((i+1 for i, r in enumerate(ranking) if r["id"] == self.liga_id), "N/A")

        graficas_row = ctk.CTkFrame(self.graficas_container, fg_color="transparent")
        graficas_row.pack(fill="x", pady=10)

        frame_grafica1 = ctk.CTkFrame(graficas_row, fg_color=("gray90", "gray20"), corner_radius=10)
        frame_grafica1.pack(side="left", padx=10, fill="both", expand=True)
        ctk.CTkLabel(frame_grafica1, text="Partidos por cantidad de goles",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        grafica1 = GraficaFrame(frame_grafica1, width=350, height=280)
        grafica1.graficar_comparacion_goles(stats["partidos_mas_3_goles"], stats["partidos_menos_igual_3_goles"])
        self.graficas.append(grafica1)

        frame_grafica2 = ctk.CTkFrame(graficas_row, fg_color=("gray90", "gray20"), corner_radius=10)
        frame_grafica2.pack(side="left", padx=10, fill="both", expand=True)
        ctk.CTkLabel(frame_grafica2, text="Promedio de goles",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        grafica2 = GraficaFrame(frame_grafica2, width=350, height=280)
        grafica2.graficar_promedio_goles(stats["promedio_goles"], stats["total_partidos"])
        self.graficas.append(grafica2)

        section = ctk.CTkFrame(self.info_container, fg_color="transparent")
        section.pack(fill="x", pady=10)

        ctk.CTkLabel(section, text="Resumen de la Liga", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")

        metricas = [
            ("Promedio de goles por partido", f"{stats['promedio_goles']:.2f}"),
            ("Total de partidos jugados", str(stats['total_partidos'])),
            ("Partidos con más de 3 goles", str(stats['partidos_mas_3_goles'])),
            ("Partidos con 3 o menos goles", str(stats['partidos_menos_igual_3_goles'])),
            ("Posición en ranking de promedio", f"#{posicion_ranking}"),
        ]

        for label, valor in metricas:
            row = ctk.CTkFrame(self.info_container, fg_color=("gray85", "gray25"), corner_radius=5)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=14)).pack(side="left", padx=15, pady=10)
            ctk.CTkLabel(row, text=valor, font=ctk.CTkFont(size=14, weight="bold")).pack(side="right", padx=15, pady=10)

        frame_grafica3 = ctk.CTkFrame(self.info_container, fg_color=("gray90", "gray20"), corner_radius=10, width=700)
        frame_grafica3.pack(fill="x", pady=15)
        ctk.CTkLabel(frame_grafica3, text="Top 5 Ranking de Promedio de Goles",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        grafica3 = GraficaFrame(frame_grafica3, width=650, height=250)
        grafica3.graficar_ranking_goles(ranking)
        self.graficas.append(grafica3)
