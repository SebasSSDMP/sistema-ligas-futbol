import { useState, useEffect, useCallback, useRef } from 'react';
import {
  obtenerTemporadas,
  crearTemporada,
  obtenerEquipos,
  crearEquipo,
  actualizarEquipo,
  eliminarEquipo,
  obtenerPartidos,
  crearPartido,
  obtenerEstadisticas,
  cancelAllRequests,
} from '../api';
import Estadisticas from './Estadisticas';
import { EquipoCard } from './EquipoCard';
import { EquipoForm } from './EquipoForm';
import { Modal, ConfirmDialog } from './Modal';
import { Toast } from './Toast';

export default function LigaDashboard({ liga, onVolver }) {
  const [seccion, setSeccion] = useState('menu');
  const [temporadas, setTemporadas] = useState([]);
  const [equipos, setEquipos] = useState([]);
  const [partidos, setPartidos] = useState([]);
  const [temporadaSeleccionada, setTemporadaSeleccionada] = useState(null);

  const [loadingTemporadas, setLoadingTemporadas] = useState(true);
  const [loadingEquipos, setLoadingEquipos] = useState(true);
  const [loadingPartidos, setLoadingPartidos] = useState(false);
  const [errorTemporadas, setErrorTemporadas] = useState(null);
  const [errorEquipos, setErrorEquipos] = useState(null);
  const [errorPartidos, setErrorPartidos] = useState(null);

  const [actionLoading, setActionLoading] = useState(false);

  const [mostrarFormEquipo, setMostrarFormEquipo] = useState(false);
  const [equipoEditando, setEquipoEditando] = useState(null);
  const [equipoEliminando, setEquipoEliminando] = useState(null);
  const [mostrarConfirmEliminar, setMostrarConfirmEliminar] = useState(false);

  const [mostrarFormPartido, setMostrarFormPartido] = useState(false);
  const [mostrarFormTemporada, setMostrarFormTemporada] = useState(false);

  const [toast, setToast] = useState(null);
  const isMountedRef = useRef(true);
  const requestIdRef = useRef(0);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      cancelAllRequests();
    };
  }, []);

  const showToast = useCallback((message, type = 'success') => {
    if (isMountedRef.current) {
      setToast({ message, type });
    }
  }, []);

  const hideToast = useCallback(() => {
    if (isMountedRef.current) {
      setToast(null);
    }
  }, []);

  const cargarTemporadas = useCallback(async () => {
    if (!liga?.id || !isMountedRef.current) return;

    const requestId = ++requestIdRef.current;
    console.log(`[LigaDashboard] Cargando temporadas, requestId: ${requestId}`);

    setLoadingTemporadas(true);
    setErrorTemporadas(null);

    try {
      const data = await obtenerTemporadas(liga.id, `temp-${liga.id}-${requestId}`);

      if (!isMountedRef.current || requestId !== requestIdRef.current) return;

      setTemporadas(Array.isArray(data) ? data : []);
      console.log(`[LigaDashboard] Temporadas: ${Array.isArray(data) ? data.length : 0}`);
    } catch (error) {
      if (!isMountedRef.current || requestId !== requestIdRef.current) return;
      console.error(`[LigaDashboard] Error temporadas:`, error);
      setErrorTemporadas(error.message || 'Error al cargar temporadas');
    } finally {
      if (isMountedRef.current && requestId === requestIdRef.current) {
        setLoadingTemporadas(false);
      }
    }
  }, [liga?.id]);

  const cargarEquipos = useCallback(async () => {
    if (!liga?.id || !isMountedRef.current) return;

    const requestId = ++requestIdRef.current;
    console.log(`[LigaDashboard] Cargando equipos, requestId: ${requestId}`);

    setLoadingEquipos(true);
    setErrorEquipos(null);

    try {
      const data = await obtenerEquipos(liga.id, `equipos-${liga.id}-${requestId}`);

      if (!isMountedRef.current || requestId !== requestIdRef.current) return;

      setEquipos(Array.isArray(data) ? data : []);
      console.log(`[LigaDashboard] Equipos: ${Array.isArray(data) ? data.length : 0}`);
    } catch (error) {
      if (!isMountedRef.current || requestId !== requestIdRef.current) return;
      console.error(`[LigaDashboard] Error equipos:`, error);
      setErrorEquipos(error.message || 'Error al cargar equipos');
    } finally {
      if (isMountedRef.current && requestId === requestIdRef.current) {
        setLoadingEquipos(false);
      }
    }
  }, [liga?.id]);

  const cargarPartidos = useCallback(async () => {
    if (!temporadaSeleccionada?.id || !isMountedRef.current) return;

    const requestId = ++requestIdRef.current;
    console.log(`[LigaDashboard] Cargando partidos, requestId: ${requestId}`);

    setLoadingPartidos(true);
    setErrorPartidos(null);

    try {
      const data = await obtenerPartidos(temporadaSeleccionada.id, `partidos-${temporadaSeleccionada.id}-${requestId}`);

      if (!isMountedRef.current || requestId !== requestIdRef.current) return;

      setPartidos(Array.isArray(data) ? data : []);
      console.log(`[LigaDashboard] Partidos: ${Array.isArray(data) ? data.length : 0}`);
    } catch (error) {
      if (!isMountedRef.current || requestId !== requestIdRef.current) return;
      console.error(`[LigaDashboard] Error partidos:`, error);
      setErrorPartidos(error.message || 'Error al cargar partidos');
    } finally {
      if (isMountedRef.current && requestId === requestIdRef.current) {
        setLoadingPartidos(false);
      }
    }
  }, [temporadaSeleccionada]);

  useEffect(() => {
    if (liga?.id) {
      setTemporadas([]);
      setEquipos([]);
      setPartidos([]);
      setTemporadaSeleccionada(null);
      setSeccion('menu');
      setErrorTemporadas(null);
      setErrorEquipos(null);
      setErrorPartidos(null);
      cargarTemporadas();
      cargarEquipos();
    }
  }, [liga?.id, cargarTemporadas, cargarEquipos]);

  useEffect(() => {
    if (temporadaSeleccionada) {
      cargarPartidos();
    } else {
      setPartidos([]);
      setLoadingPartidos(false);
    }
  }, [temporadaSeleccionada, cargarPartidos]);

  const seleccionarTemporada = useCallback((temp) => {
    if (!temp?.id || !isMountedRef.current) return;
    setTemporadaSeleccionada(temp);
  }, []);

  const abrirFormCrearEquipo = () => {
    setEquipoEditando(null);
    setMostrarFormEquipo(true);
  };

  const abrirFormEditarEquipo = (equipo) => {
    setEquipoEditando(equipo);
    setMostrarFormEquipo(true);
  };

  const handleSubmitEquipo = useCallback(
    async (data) => {
      if (!liga?.id) return;

      setActionLoading(true);
      try {
        if (equipoEditando) {
          await actualizarEquipo(equipoEditando.id, data);
          showToast('Equipo actualizado', 'success');
        } else {
          await crearEquipo({ ...data, liga_id: liga.id });
          showToast('Equipo creado', 'success');
        }
        setMostrarFormEquipo(false);
        setEquipoEditando(null);
        cargarEquipos();
      } catch (error) {
        showToast(error.message || 'Error al guardar equipo', 'error');
      } finally {
        setActionLoading(false);
      }
    },
    [liga?.id, equipoEditando, showToast, cargarEquipos]
  );

  const confirmarEliminarEquipo = (equipo) => {
    setEquipoEliminando(equipo);
    setMostrarConfirmEliminar(true);
  };

  const handleEliminarEquipo = useCallback(async () => {
    if (!equipoEliminando?.id) return;

    setActionLoading(true);
    try {
      await eliminarEquipo(equipoEliminando.id);
      showToast('Equipo eliminado', 'success');
      setMostrarConfirmEliminar(false);
      setEquipoEliminando(null);
      cargarEquipos();
    } catch (error) {
      showToast(error.message || 'Error al eliminar equipo', 'error');
    } finally {
      setActionLoading(false);
    }
  }, [equipoEliminando, showToast, cargarEquipos]);

  const handleCrearTemporada = useCallback(
    async (e) => {
      e.preventDefault();
      if (!liga?.id) return;

      const form = e.target;
      setActionLoading(true);
      try {
        await crearTemporada({
          nombre: form.nombre.value,
          fecha_inicio: form.fecha_inicio.value || null,
          fecha_fin: form.fecha_fin.value || null,
          liga_id: liga.id,
        });
        setMostrarFormTemporada(false);
        showToast('Temporada creada', 'success');
        cargarTemporadas();
      } catch (error) {
        showToast(error.message || 'Error al crear temporada', 'error');
      } finally {
        setActionLoading(false);
      }
    },
    [liga?.id, showToast, cargarTemporadas]
  );

  const handleCrearPartido = useCallback(
    async (e) => {
      e.preventDefault();
      if (!temporadaSeleccionada) {
        showToast('Selecciona una temporada', 'warning');
        return;
      }

      const form = e.target;

      if (form.equipo_local.value === form.equipo_visitante.value) {
        showToast('Los equipos no pueden ser iguales', 'warning');
        return;
      }

      setActionLoading(true);
      try {
        await crearPartido({
          fecha: form.fecha.value || '2024-01-01 00:00',
          equipo_local: parseInt(form.equipo_local.value),
          equipo_visitante: parseInt(form.equipo_visitante.value),
          goles_local: parseInt(form.goles_local.value) || 0,
          goles_visitante: parseInt(form.goles_visitante.value) || 0,
          arbitro: form.arbitro.value || 'Por definir',
          estadio: form.estadio.value || 'Por definir',
          temporada_id: temporadaSeleccionada.id,
        });
        setMostrarFormPartido(false);
        showToast('Partido creado', 'success');
        cargarPartidos();
      } catch (error) {
        showToast(error.message || 'Error al crear partido', 'error');
      } finally {
        setActionLoading(false);
      }
    },
    [temporadaSeleccionada, showToast, cargarPartidos]
  );

  const getNombreEquipo = useCallback(
    (id) => {
      const eq = equipos.find((e) => e.id === id);
      return eq ? eq.nombre : 'N/A';
    },
    [equipos]
  );

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">{liga?.nombre || 'Liga'}</h2>
        <p className="text-gray-400">{liga?.pais || 'Sin país'} - Panel de Gestión</p>
      </div>

      {seccion === 'menu' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <button
            onClick={() => setSeccion('temporadas')}
            className="bg-dark-card rounded-2xl p-6 border border-dark-border hover:border-accent-green transition-all hover:scale-[1.02] text-left group"
          >
            <div className="w-14 h-14 bg-accent-green/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <span className="text-3xl">📅</span>
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Temporadas</h3>
            <p className="text-gray-400 text-sm">
              {loadingTemporadas ? 'Cargando...' : `${temporadas.length} temporada(s)`}
              {errorTemporadas && ' (error)'}
            </p>
          </button>

          <button
            onClick={() => setSeccion('equipos')}
            className="bg-dark-card rounded-2xl p-6 border border-dark-border hover:border-accent-blue transition-all hover:scale-[1.02] text-left group"
          >
            <div className="w-14 h-14 bg-accent-blue/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <span className="text-3xl">👥</span>
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Equipos</h3>
            <p className="text-gray-400 text-sm">
              {loadingEquipos ? 'Cargando...' : `${equipos.length} equipo(s)`}
              {errorEquipos && ' (error)'}
            </p>
          </button>

          <button
            onClick={() => setSeccion('partidos')}
            className="bg-dark-card rounded-2xl p-6 border border-dark-border hover:border-accent-orange transition-all hover:scale-[1.02] text-left group"
          >
            <div className="w-14 h-14 bg-accent-orange/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <span className="text-3xl">⚽</span>
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Partidos</h3>
            <p className="text-gray-400 text-sm">Gestionar partidos</p>
          </button>

          <button
            onClick={() => setSeccion('estadisticas')}
            className="bg-dark-card rounded-2xl p-6 border border-dark-border hover:border-accent-purple transition-all hover:scale-[1.02] text-left group"
          >
            <div className="w-14 h-14 bg-accent-purple/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <span className="text-3xl">📊</span>
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Estadísticas</h3>
            <p className="text-gray-400 text-sm">Ver métricas</p>
          </button>
        </div>
      )}

      {seccion === 'temporadas' && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold text-white">Temporadas</h3>
            <button
              onClick={() => setMostrarFormTemporada(true)}
              className="bg-accent-green hover:bg-accent-green/80 text-dark-bg font-bold px-6 py-3 rounded-xl transition-all flex items-center gap-2"
            >
              <span>+</span> Nueva Temporada
            </button>
          </div>

          {mostrarFormTemporada && (
            <form
              onSubmit={handleCrearTemporada}
              className="bg-dark-card rounded-2xl p-6 border border-accent-green/50 mb-6"
            >
              <h4 className="text-lg font-semibold text-white mb-4">Crear Nueva Temporada</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Nombre *</label>
                  <input
                    name="nombre"
                    required
                    placeholder="Ej: 2024-2025"
                    className="w-full px-4 py-3 rounded-xl border"
                  />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Fecha Inicio</label>
                  <input name="fecha_inicio" type="date" className="w-full px-4 py-3 rounded-xl border" />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Fecha Fin</label>
                  <input name="fecha_fin" type="date" className="w-full px-4 py-3 rounded-xl border" />
                </div>
              </div>
              <div className="flex gap-3 mt-4">
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="bg-accent-green text-dark-bg font-bold px-6 py-3 rounded-xl disabled:opacity-50"
                >
                  {actionLoading ? 'Guardando...' : 'Guardar'}
                </button>
                <button
                  type="button"
                  onClick={() => setMostrarFormTemporada(false)}
                  className="bg-dark-border text-white px-6 py-3 rounded-xl"
                >
                  Cancelar
                </button>
              </div>
            </form>
          )}

          {loadingTemporadas && !errorTemporadas ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-accent-green border-t-transparent"></div>
              <span className="ml-3 text-gray-400">Cargando temporadas...</span>
            </div>
          ) : errorTemporadas ? (
            <div className="text-center py-8 bg-dark-card rounded-xl border border-dark-border">
              <p className="text-red-400 mb-4">{errorTemporadas}</p>
              <button
                onClick={cargarTemporadas}
                className="bg-accent-green text-dark-bg px-4 py-2 rounded-lg"
              >
                Reintentar
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {temporadas.map((temp) => (
                <div key={temp.id} className="bg-dark-card rounded-xl p-4 border border-dark-border">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-accent-green/20 rounded-lg flex items-center justify-center">
                      <span>📅</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-white">{temp.nombre}</h4>
                      <p className="text-xs text-gray-400">
                        {temp.fecha_inicio || 'Sin fecha'} - {temp.fecha_fin || 'Sin fecha'}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
              {temporadas.length === 0 && (
                <div className="col-span-full text-center py-12">
                  <p className="text-gray-400">No hay temporadas creadas</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {seccion === 'equipos' && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold text-white">Equipos</h3>
            <button
              onClick={abrirFormCrearEquipo}
              className="bg-accent-blue hover:bg-accent-blue/80 text-dark-bg font-bold px-6 py-3 rounded-xl transition-all flex items-center gap-2"
            >
              <span>+</span> Nuevo Equipo
            </button>
          </div>

          {loadingEquipos && !errorEquipos ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-accent-blue border-t-transparent"></div>
              <span className="ml-3 text-gray-400">Cargando equipos...</span>
            </div>
          ) : errorEquipos ? (
            <div className="text-center py-8 bg-dark-card rounded-xl border border-dark-border">
              <p className="text-red-400 mb-4">{errorEquipos}</p>
              <button onClick={cargarEquipos} className="bg-accent-blue text-dark-bg px-4 py-2 rounded-lg">
                Reintentar
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {equipos.map((eq) => (
                <EquipoCard
                  key={eq.id}
                  equipo={eq}
                  onEdit={abrirFormEditarEquipo}
                  onDelete={confirmarEliminarEquipo}
                  disabled={actionLoading}
                />
              ))}
              {equipos.length === 0 && (
                <div className="col-span-full text-center py-12">
                  <p className="text-gray-400">No hay equipos creados</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {seccion === 'partidos' && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold text-white">Partidos</h3>
            <button
              onClick={() => setMostrarFormPartido(true)}
              disabled={temporadas.length === 0 || equipos.length < 2}
              className="bg-accent-orange hover:bg-accent-orange/80 text-dark-bg font-bold px-6 py-3 rounded-xl transition-all flex items-center gap-2 disabled:opacity-50"
            >
              <span>+</span> Nuevo Partido
            </button>
          </div>

          {temporadas.length === 0 ? (
            <div className="bg-dark-card rounded-xl p-8 text-center border border-dark-border">
              <p className="text-gray-400 mb-2">Necesitas crear temporadas y equipos primero</p>
              <button onClick={() => setSeccion('temporadas')} className="text-accent-orange hover:underline">
                Ir a Temporadas
              </button>
            </div>
          ) : (
            <div className="mb-6">
              <label className="block text-gray-400 text-sm mb-2">Seleccionar Temporada</label>
              <select
                onChange={(e) => {
                  const temp = temporadas.find((t) => t.id === parseInt(e.target.value));
                  seleccionarTemporada(temp);
                }}
                value={temporadaSeleccionada?.id || ''}
                className="px-4 py-3 rounded-xl border w-full max-w-xs"
              >
                <option value="">Seleccionar temporada...</option>
                {temporadas.map((temp) => (
                  <option key={temp.id} value={temp.id}>
                    {temp.nombre}
                  </option>
                ))}
              </select>
            </div>
          )}

          {mostrarFormPartido && equipos.length >= 2 && (
            <form
              onSubmit={handleCrearPartido}
              className="bg-dark-card rounded-2xl p-6 border border-accent-orange/50 mb-6"
            >
              <h4 className="text-lg font-semibold text-white mb-4">Crear Nuevo Partido</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Fecha</label>
                  <input name="fecha" type="datetime-local" className="w-full px-4 py-3 rounded-xl border" />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Equipo Local *</label>
                  <select name="equipo_local" required className="w-full px-4 py-3 rounded-xl border">
                    <option value="">Seleccionar...</option>
                    {equipos.map((eq) => (
                      <option key={eq.id} value={eq.id}>
                        {eq.nombre}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Equipo Visitante *</label>
                  <select name="equipo_visitante" required className="w-full px-4 py-3 rounded-xl border">
                    <option value="">Seleccionar...</option>
                    {equipos.map((eq) => (
                      <option key={eq.id} value={eq.id}>
                        {eq.nombre}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Goles Local</label>
                  <input
                    name="goles_local"
                    type="number"
                    min="0"
                    defaultValue="0"
                    className="w-full px-4 py-3 rounded-xl border"
                  />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Goles Visitante</label>
                  <input
                    name="goles_visitante"
                    type="number"
                    min="0"
                    defaultValue="0"
                    className="w-full px-4 py-3 rounded-xl border"
                  />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Arbitro</label>
                  <input
                    name="arbitro"
                    placeholder="Nombre del arbitro"
                    className="w-full px-4 py-3 rounded-xl border"
                  />
                </div>
                <div className="lg:col-span-3">
                  <label className="block text-gray-400 text-sm mb-2">Estadio</label>
                  <input
                    name="estadio"
                    placeholder="Nombre del estadio"
                    className="w-full px-4 py-3 rounded-xl border max-w-md"
                  />
                </div>
              </div>
              <div className="flex gap-3 mt-4">
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="bg-accent-orange text-dark-bg font-bold px-6 py-3 rounded-xl disabled:opacity-50"
                >
                  {actionLoading ? 'Guardando...' : 'Guardar'}
                </button>
                <button
                  type="button"
                  onClick={() => setMostrarFormPartido(false)}
                  className="bg-dark-border text-white px-6 py-3 rounded-xl"
                >
                  Cancelar
                </button>
              </div>
            </form>
          )}

          {loadingPartidos && !errorPartidos ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-accent-orange border-t-transparent"></div>
              <span className="ml-3 text-gray-400">Cargando partidos...</span>
            </div>
          ) : errorPartidos ? (
            <div className="text-center py-8 bg-dark-card rounded-xl border border-dark-border">
              <p className="text-red-400 mb-4">{errorPartidos}</p>
              <button onClick={cargarPartidos} className="bg-accent-orange text-dark-bg px-4 py-2 rounded-lg">
                Reintentar
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {partidos.map((partido) => (
                <div key={partido.id} className="bg-dark-card rounded-xl p-4 border border-dark-border">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-gray-400">
                        {partido.fecha ? new Date(partido.fecha).toLocaleDateString() : 'Sin fecha'}
                      </span>
                      <span className="font-bold text-white">{getNombreEquipo(partido.equipo_local)}</span>
                    </div>
                    <div className="bg-dark-bg px-4 py-2 rounded-xl flex items-center gap-4">
                      <span className="text-2xl font-bold text-accent-green">{partido.goles_local}</span>
                      <span className="text-gray-400">-</span>
                      <span className="text-2xl font-bold text-accent-orange">{partido.goles_visitante}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="font-bold text-white">{getNombreEquipo(partido.equipo_visitante)}</span>
                    </div>
                  </div>
                  {partido.arbitro && (
                    <p className="text-xs text-gray-500 mt-2">
                      Arbitro: {partido.arbitro} | Estadio: {partido.estadio}
                    </p>
                  )}
                </div>
              ))}
              {partidos.length === 0 && temporadaSeleccionada && (
                <div className="text-center py-8">
                  <p className="text-gray-400">No hay partidos en esta temporada</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {seccion === 'estadisticas' && liga?.id && <Estadisticas ligaId={liga.id} />}

      <Modal
        isOpen={mostrarFormEquipo}
        onClose={() => {
          setMostrarFormEquipo(false);
          setEquipoEditando(null);
        }}
        title={equipoEditando ? 'Editar Equipo' : 'Nuevo Equipo'}
      >
        <EquipoForm
          equipo={equipoEditando}
          onSubmit={handleSubmitEquipo}
          onCancel={() => {
            setMostrarFormEquipo(false);
            setEquipoEditando(null);
          }}
          isSubmitting={actionLoading}
        />
      </Modal>

      <ConfirmDialog
        isOpen={mostrarConfirmEliminar}
        onClose={() => {
          setMostrarConfirmEliminar(false);
          setEquipoEliminando(null);
        }}
        onConfirm={handleEliminarEquipo}
        title="¿Eliminar Equipo?"
        message={`¿Estás seguro de eliminar "${equipoEliminando?.nombre}"? Esta acción no se puede deshacer.`}
        confirmText="Eliminar"
        cancelText="Cancelar"
        type="danger"
      />

      {toast && <Toast {...toast} onClose={hideToast} />}
    </div>
  );
}
