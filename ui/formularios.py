import customtkinter as ctk
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from ui.app import App

from core import DatabaseException, ValidationError
from ui.dialogs import mostrar_error, mostrar_exito


class FormularioBase(ctk.CTkToplevel):
    def __init__(self, parent, titulo: str, callback: Optional[Callable] = None):
        super().__init__(parent)
        self.title(titulo)
        self.callback = callback
        self.transient(parent)
        self.grab_set()

    def destruir(self):
        if self.callback:
            self.callback()
        self.destroy()


class FormularioLiga(FormularioBase):
    def __init__(self, parent, callback: Optional[Callable] = None):
        super().__init__(parent, "Nueva Liga", callback)
        self.geometry("400x250")

        ctk.CTkLabel(self, text="Nombre de la liga:", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        self.entry_nombre = ctk.CTkEntry(self, width=300)
        self.entry_nombre.pack()

        ctk.CTkLabel(self, text="Pais:", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 5))
        self.entry_pais = ctk.CTkEntry(self, width=300)
        self.entry_pais.pack()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="Cancelar", command=self.destroy, width=120).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Guardar", command=self._guardar, width=120).pack(side="left", padx=10)

    def _guardar(self):
        try:
            from database import LigaRepository, get_db
            db = get_db()
            repo = LigaRepository(db)
            repo.crear(self.entry_nombre.get(), self.entry_pais.get())
            mostrar_exito(self, "Liga creada exitosamente")
            self.destruir()
        except (DatabaseException, ValidationError) as e:
            mostrar_error(self, str(e))


class FormularioTemporada(FormularioBase):
    def __init__(self, parent, liga_id: int, callback: Optional[Callable] = None):
        super().__init__(parent, "Nueva Temporada", callback)
        self.liga_id = liga_id
        self.geometry("400x300")

        ctk.CTkLabel(self, text="Nombre:", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        self.entry_nombre = ctk.CTkEntry(self, width=300, placeholder_text="Ej: 2024-2025")
        self.entry_nombre.pack()

        ctk.CTkLabel(self, text="Fecha Inicio:", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 5))
        self.entry_inicio = ctk.CTkEntry(self, width=300, placeholder_text="YYYY-MM-DD")
        self.entry_inicio.pack()

        ctk.CTkLabel(self, text="Fecha Fin:", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 5))
        self.entry_fin = ctk.CTkEntry(self, width=300, placeholder_text="YYYY-MM-DD")
        self.entry_fin.pack()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="Cancelar", command=self.destroy, width=120).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Guardar", command=self._guardar, width=120).pack(side="left", padx=10)

    def _guardar(self):
        try:
            from database import TemporadaRepository, get_db
            db = get_db()
            repo = TemporadaRepository(db)
            repo.crear(
                self.entry_nombre.get(),
                self.entry_inicio.get() or "2024-01-01",
                self.entry_fin.get() or "2024-12-31",
                self.liga_id
            )
            mostrar_exito(self, "Temporada creada exitosamente")
            self.destruir()
        except (DatabaseException, ValidationError) as e:
            mostrar_error(self, str(e))


class FormularioEquipo(FormularioBase):
    def __init__(self, parent, liga_id: int, callback: Optional[Callable] = None):
        super().__init__(parent, "Nuevo Equipo", callback)
        self.liga_id = liga_id
        self.geometry("400x200")

        ctk.CTkLabel(self, text="Nombre del equipo:", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        self.entry_nombre = ctk.CTkEntry(self, width=300)
        self.entry_nombre.pack()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="Cancelar", command=self.destroy, width=120).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Guardar", command=self._guardar, width=120).pack(side="left", padx=10)

    def _guardar(self):
        try:
            from database import EquipoRepository, get_db
            db = get_db()
            repo = EquipoRepository(db)
            repo.crear(self.entry_nombre.get(), self.liga_id)
            mostrar_exito(self, "Equipo creado exitosamente")
            self.destruir()
        except (DatabaseException, ValidationError) as e:
            mostrar_error(self, str(e))


class FormularioPartido(FormularioBase):
    def __init__(self, parent, liga_id: int, callback: Optional[Callable] = None):
        super().__init__(parent, "Nuevo Partido", callback)
        self.liga_id = liga_id
        self.geometry("400x450")

        from database import get_db, EquipoRepository, TemporadaRepository
        db = get_db()
        self.equipos = EquipoRepository(db).obtener_por_liga(liga_id)
        self.temporadas = TemporadaRepository(db).obtener_por_liga(liga_id)

        ctk.CTkLabel(self, text="Fecha:", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        self.entry_fecha = ctk.CTkEntry(self, width=300, placeholder_text="YYYY-MM-DD HH:MM")
        self.entry_fecha.pack()

        ctk.CTkLabel(self, text="Temporada:", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 5))
        self.combo_temporada = ctk.CTkComboBox(self, width=300, values=[t["nombre"] for t in self.temporadas])
        if self.temporadas:
            self.combo_temporada.set(self.temporadas[0]["nombre"])
        self.combo_temporada.pack()

        ctk.CTkLabel(self, text="Equipo Local:", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 5))
        self.combo_local = ctk.CTkComboBox(self, width=300, values=[e["nombre"] for e in self.equipos])
        if self.equipos:
            self.combo_local.set(self.equipos[0]["nombre"])
        self.combo_local.pack()

        ctk.CTkLabel(self, text="Equipo Visitante:", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 5))
        self.combo_visitante = ctk.CTkComboBox(self, width=300, values=[e["nombre"] for e in self.equipos])
        if len(self.equipos) > 1:
            self.combo_visitante.set(self.equipos[1]["nombre"])
        self.combo_visitante.pack()

        ctk.CTkLabel(self, text="Arbitro:", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 5))
        self.entry_arbitro = ctk.CTkEntry(self, width=300)
        self.entry_arbitro.pack()

        ctk.CTkLabel(self, text="Estadio:", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 5))
        self.entry_estadio = ctk.CTkEntry(self, width=300)
        self.entry_estadio.pack()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="Cancelar", command=self.destroy, width=120).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Guardar", command=self._guardar, width=120).pack(side="left", padx=10)

    def _guardar(self):
        try:
            if not self.temporadas:
                mostrar_error(self, "Debe crear una temporada primero")
                return

            if len(self.equipos) < 2:
                mostrar_error(self, "Debe crear al menos 2 equipos primero")
                return

            from database import PartidoRepository, get_db
            db = get_db()
            repo = PartidoRepository(db)

            temp_idx = self.combo_temporada.cget("values").index(self.combo_temporada.get())
            local_idx = self.combo_local.cget("values").index(self.combo_local.get())
            visitante_idx = self.combo_visitante.cget("values").index(self.combo_visitante.get())

            repo.crear(
                fecha=self.entry_fecha.get() or "2024-01-01 00:00",
                equipo_local=self.equipos[local_idx]["id"],
                equipo_visitante=self.equipos[visitante_idx]["id"],
                goles_local=0,
                goles_visitante=0,
                arbitro=self.entry_arbitro.get() or "Por definir",
                estadio=self.entry_estadio.get() or "Por definir",
                temporada_id=self.temporadas[temp_idx]["id"]
            )
            mostrar_exito(self, "Partido creado exitosamente")
            self.destruir()
        except (DatabaseException, ValidationError) as e:
            mostrar_error(self, str(e))
