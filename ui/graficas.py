import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import TYPE_CHECKING

matplotlib.use("Agg")

if TYPE_CHECKING:
    from customtkinter import CTkFrame


class GraficaFrame:
    def __init__(self, parent: "CTkFrame", width: int = 350, height: int = 250):
        self.figure, self.ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def destruir(self):
        self.canvas.get_tk_widget().destroy()
        plt.close(self.figure)

    def graficar_comparacion_goles(self, mas_3: int, menos_3: int):
        self.ax.clear()
        categorias = ["≤ 3 goles", "> 3 goles"]
        valores = [menos_3, mas_3]
        colores = ["#4CAF50", "#FF5722"]

        barras = self.ax.bar(categorias, valores, color=colores, edgecolor="white", linewidth=1.5)
        
        for barra in barras:
            altura = barra.get_height()
            self.ax.text(barra.get_x() + barra.get_width()/2., altura,
                        f'{int(altura)}', ha='center', va='bottom', fontsize=12, fontweight='bold')

        self.ax.set_title("Partidos por cantidad de goles", fontsize=14, fontweight='bold', pad=10)
        self.ax.set_ylabel("Cantidad de partidos", fontsize=11)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.set_facecolor("#2b2b2b" if plt.get_fignums() else "white")
        self.figure.patch.set_facecolor("#2b2b2b")
        self.ax.tick_params(colors='white')
        self.ax.yaxis.label.set_color('white')
        self.ax.title.set_color('white')
        self.figure.tight_layout()
        self.canvas.draw()

    def graficar_promedio_goles(self, promedio: float, total_partidos: int):
        self.ax.clear()
        
        datos = [promedio, 3.0]
        categorias = ["Esta Liga", "Promedio general"]
        colores = ["#2196F3", "#9E9E9E"]

        barras = self.ax.bar(categorias, datos, color=colores, edgecolor="white", linewidth=1.5, width=0.5)
        
        for barra in barras:
            altura = barra.get_height()
            self.ax.text(barra.get_x() + barra.get_width()/2., altura,
                        f'{altura:.2f}', ha='center', va='bottom', fontsize=14, fontweight='bold')

        self.ax.set_title(f"Promedio de goles ({total_partidos} partidos)", fontsize=14, fontweight='bold', pad=10)
        self.ax.set_ylabel("Goles por partido", fontsize=11)
        self.ax.set_ylim(0, max(datos) * 1.3)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.tick_params(colors='white')
        self.ax.yaxis.label.set_color('white')
        self.ax.title.set_color('white')
        self.figure.patch.set_facecolor("#2b2b2b")
        self.figure.tight_layout()
        self.canvas.draw()

    def graficar_ranking_goles(self, ranking: list):
        self.ax.clear()
        
        nombres = [r["nombre"][:15] for r in ranking[:5]]
        promedios = [r["promedio_goles"] if r["promedio_goles"] else 0 for r in ranking[:5]]
        colores = ["#FFD700" if i == 0 else "#2196F3" for i in range(len(nombres))]

        y_pos = range(len(nombres))
        barras = self.ax.barh(y_pos, promedios, color=colores, edgecolor="white", linewidth=1)
        
        self.ax.set_yticks(y_pos)
        self.ax.set_yticklabels(nombres)
        
        for i, barra in enumerate(barras):
            ancho = barra.get_width()
            self.ax.text(ancho + 0.05, barra.get_y() + barra.get_height()/2.,
                        f'{promedios[i]:.2f}', va='center', fontsize=11, fontweight='bold')

        self.ax.set_title("Top 5 Ranking por Promedio de Goles", fontsize=14, fontweight='bold', pad=10)
        self.ax.set_xlabel("Promedio de goles", fontsize=11)
        self.ax.invert_yaxis()
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.set_xlim(0, max(promedios) * 1.3 if promedios else 5)
        self.ax.tick_params(colors='white')
        self.ax.yaxis.label.set_color('white')
        self.ax.xaxis.label.set_color('white')
        self.ax.title.set_color('white')
        self.figure.patch.set_facecolor("#2b2b2b")
        self.figure.tight_layout()
        self.canvas.draw()
