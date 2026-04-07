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
  actualizarPartido,
  obtenerEstadisticasConFiltro,
  obtenerRankingLiga,
  obtenerEquiposTemporada,
  asociarEquipoTemporada,
  desasociarEquipoTemporada,
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

  // REQ 1: edición de partidos
  const [editandoPartidoId, setEditandoPartidoId] = useState(null);
  const [partidoEditado, setPartidoEditado] = useState({ goles_local: 0, goles_visitante: 0, fecha: null });
  const [savingPartido, setSavingPartido] = useState(false);

  const [actionLoading, setActionLoading] = useState(false);

  const [mostrarFormEquipo, setMostrarFormEquipo] = useState(false);
  const [equipoEditando, setEquipoEditando] = useState(null);
  const [equipoEliminando, setEquipoEliminando] = useState(null);
  const [mostrarConfirmEliminar, setMostrarConfirmEliminar] = useState(false);

  const [mostrarFormPartido, setMostrarFormPartido] = useState(false);
  const [mostrarFormTemporada, setMostrarFormTemporada] = useState(false);

  // REQ 2/4: estadísticas con filtro temporada
  const [estadisticas, setEstadisticas] = useState(null);
  const [loadingEstadisticas, setLoadingEstadisticas] = useState(false);
  const [temporadaEstadisticas, setTemporadaEstadisticas] = useState('');

  // REQ 3: ranking de equipos de la liga
  const [rankingEquipos, setRankingEquipos] = useState([]);
  const [loadingRanking, setLoadingRanking] = useState(false);
  const [seccionEstadisticas, setSeccionEstadisticas] = useState('estadisticas'); // 'estadisticas' | 'tabla'

  // REQ 5: equipos de temporada
  const [equiposTemporada, setEquiposTemporada] = useState([]);
  const [loadingEquiposTemp, setLoadingEquiposTemp] = useState(false);
  const [equipoParaAgregar, setEquipoParaAgregar] = useState('');
  const [mostrarGestionEquiposTemp, setMostrarGestionEquiposTemp] = useState(false);

  const [toast, setToast] = useState(null);
  const isMountedRef = useRef(true);
  const tempRequestIdRef = useRef(0);
  const equiposRequestIdRef = useRef(0);
  const partidosRequestIdRef = useRef(0);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      cancelAllRequests();
    };
  }, []);

  const showToast = useCallback((message, type = 'success') => {
    if (isMountedRef.current) setToast({ message, type });
  }, []);

  const hideToast = useCallback(() => {
    if (isMountedRef.current) setToast(null);
  }, []);

  const cargarTemporadas = useCallback(async () => {
    if (!liga?.id || !isMountedRef.current) return;
    const requestId = ++tempRequestIdRef.current;
    setLoadingTemporadas(true);
    setErrorTemporadas(null);
    try {
      const data = await obtenerTemporadas(liga.id, `temp-${liga.id}-${requestId}`);
      if (!isMountedRef.current || requestId !== tempRequestIdRef.current) return;
      setTemporadas(Array.isArray(data) ? data : []);
    } catch (error) {
      if (!isMountedRef.current || requestId !== tempRequestIdRef.current) return;
      setErrorTemporadas(error.message || 'Error al cargar temporadas');
    } finally {
      if (isMountedRef.current && requestId === tempRequestIdRef.current) setLoadingTemporadas(false);
    }
  }, [liga?.id]);

  const cargarEquipos = useCallback(async () => {
    if (!liga?.id || !isMountedRef.current) return;
    const requestId = ++equiposRequestIdRef.current;
    setLoadingEquipos(true);
    setErrorEquipos(null);
    try {
      const data = await obtenerEquipos(liga.id, `equipos-${liga.id}-${requestId}`);
      if (!isMountedRef.current || requestId !== equiposRequestIdRef.current) return;
      setEquipos(Array.isArray(data) ? data : []);
    } catch (error) {
      if (!isMountedRef.current || requestId !== equiposRequestIdRef.current) return;
      setErrorEquipos(error.message || 'Error al cargar equipos');
    } finally {
      if (isMountedRef.current && requestId === equiposRequestIdRef.current) setLoadingEquipos(false);
    }
  }, [liga?.id]);

  const cargarPartidos = useCallback(async () => {
    if (!temporadaSeleccionada?.id || !isMountedRef.current) return;
    const requestId = ++partidosRequestIdRef.current;
    setLoadingPartidos(true);
    setErrorPartidos(null);
    try {
      const data = await obtenerPartidos(temporadaSeleccionada.id, `partidos-${temporadaSeleccionada.id}-${requestId}`);
      if (!isMountedRef.current || requestId !== partidosRequestIdRef.current) return;
      setPartidos(Array.isArray(data) ? data : []);
    } catch (error) {
      if (!isMountedRef.current || requestId !== partidosRequestIdRef.current) return;
      setErrorPartidos(error.message || 'Error al cargar partidos');
    } finally {
      if (isMountedRef.current && requestId === partidosRequestIdRef.current) setLoadingPartidos(false);
    }
  }, [temporadaSeleccionada]);

  // REQ 2/4: cargar estadísticas con filtro
  const cargarEstadisticas = useCallback(async (temporadaId = null) => {
    if (!liga?.id || !isMountedRef.current) return;
    setLoadingEstadisticas(true);
    try {
      const data = await obtenerEstadisticasConFiltro(liga.id, temporadaId || null);
      if (!isMountedRef.current) return;
      setEstadisticas(data || {});
    } catch (error) {
      if (!isMountedRef.current) return;
      showToast('Error al cargar estadísticas', 'error');
    } finally {
      if (isMountedRef.current) setLoadingEstadisticas(false);
    }
  }, [liga?.id, showToast]);

  // REQ 3: cargar ranking de equipos
  const cargarRankingEquipos = useCallback(async () => {
    if (!liga?.id || !isMountedRef.current) return;
    setLoadingRanking(true);
    try {
      const data = await obtenerRankingLiga(liga.id);
      if (!isMountedRef.current) return;
      if (Array.isArray(data) && data.length > 0) {
        setRankingEquipos(data);
      }
    } catch (error) {
      if (!isMountedRef.current) return;
      showToast('Error al cargar ranking', 'error');
    } finally {
      if (isMountedRef.current) setLoadingRanking(false);
    }
  }, [liga?.id, showToast]);

  // REQ 5: cargar equipos de temporada seleccionada
  const cargarEquiposTemporada = useCallback(async () => {
    if (!temporadaSeleccionada?.id) return;
    setLoadingEquiposTemp(true);
    try {
      const data = await obtenerEquiposTemporada(temporadaSeleccionada.id);
      if (!isMountedRef.current) return;
      setEquiposTemporada(Array.isArray(data) ? data : []);
    } catch {
      setEquiposTemporada([]);
    } finally {
      if (isMountedRef.current) setLoadingEquiposTemp(false);
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
      cargarEquiposTemporada();
    } else {
      setPartidos([]);
      setEquiposTemporada([]);
      setLoadingPartidos(false);
    }
  }, [temporadaSeleccionada, cargarPartidos, cargarEquiposTemporada]);

  const yaCargadoRef = useRef(false);

  useEffect(() => {
    if (seccion === 'estadisticas' && liga?.id && !yaCargadoRef.current) {
      yaCargadoRef.current = true;
      cargarEstadisticas(temporadaEstadisticas || null);
      cargarRankingEquipos();
    }
  }, [seccion, liga?.id]);

  const seleccionarTemporada = useCallback((temp) => {
    if (!temp?.id || !isMountedRef.current) return;
    setTemporadaSeleccionada(temp);
  }, []);

  const abrirFormCrearEquipo = () => { setEquipoEditando(null); setMostrarFormEquipo(true); };
  const abrirFormEditarEquipo = (equipo) => { setEquipoEditando(equipo); setMostrarFormEquipo(true); };

  const handleSubmitEquipo = useCallback(async (data) => {
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
  }, [liga?.id, equipoEditando, showToast, cargarEquipos]);

  const confirmarEliminarEquipo = (equipo) => { setEquipoEliminando(equipo); setMostrarConfirmEliminar(true); };

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

  const handleCrearTemporada = useCallback(async (e) => {
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
  }, [liga?.id, showToast, cargarTemporadas]);

  // REQ 6: crear partido sin árbitro ni estadio
  const handleCrearPartido = useCallback(async (e) => {
    e.preventDefault();
    if (!temporadaSeleccionada) { showToast('Selecciona una temporada', 'warning'); return; }
    const form = e.target;
    if (form.equipo_local.value === form.equipo_visitante.value) {
      showToast('Los equipos no pueden ser iguales', 'warning');
      return;
    }
    setActionLoading(true);
    try {
      await crearPartido({
        fecha: form.fecha.value ? form.fecha.value.split('T')[0] : null,
        equipo_local: parseInt(form.equipo_local.value),
        equipo_visitante: parseInt(form.equipo_visitante.value),
        goles_local: parseInt(form.goles_local.value) || 0,
        goles_visitante: parseInt(form.goles_visitante.value) || 0,
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
  }, [temporadaSeleccionada, showToast, cargarPartidos]);

  // REQ 1: guardar partido editado
  const handleGuardarPartido = useCallback(async (partidoId) => {
    setSavingPartido(true);
    try {
      await actualizarPartido(partidoId, {
        goles_local: partidoEditado.goles_local,
        goles_visitante: partidoEditado.goles_visitante,
        fecha: partidoEditado.fecha || null,
      });
      showToast('Partido actualizado', 'success');
      setEditandoPartidoId(null);
      setPartidoEditado({ goles_local: 0, goles_visitante: 0, fecha: null });
      cargarPartidos();
    } catch (error) {
      showToast(error.message || 'Error al actualizar partido', 'error');
    } finally {
      setSavingPartido(false);
    }
  }, [partidoEditado, showToast, cargarPartidos]);

  // REQ 5: asociar/desasociar equipos a temporada
  const handleAsociarEquipo = useCallback(async () => {
    if (!equipoParaAgregar || !temporadaSeleccionada) return;
    try {
      await asociarEquipoTemporada(temporadaSeleccionada.id, parseInt(equipoParaAgregar));
      showToast('Equipo agregado a la temporada', 'success');
      setEquipoParaAgregar('');
      cargarEquiposTemporada();
    } catch (error) {
      showToast(error.message || 'Error al agregar equipo', 'error');
    }
  }, [equipoParaAgregar, temporadaSeleccionada, showToast, cargarEquiposTemporada]);

  const handleDesasociarEquipo = useCallback(async (equipoId) => {
    if (!temporadaSeleccionada) return;
    try {
      await desasociarEquipoTemporada(temporadaSeleccionada.id, equipoId);
      showToast('Equipo removido de la temporada', 'success');
      cargarEquiposTemporada();
    } catch (error) {
      showToast(error.message || 'Error al remover equipo', 'error');
    }
  }, [temporadaSeleccionada, showToast, cargarEquiposTemporada]);

  const getNombreEquipo = useCallback((id) => {
    const eq = equipos.find((e) => e.id === id);
    return eq ? eq.nombre : 'N/A';
  }, [equipos]);

  // Equipos no asociados aún a la temporada (para el dropdown de agregar)
  const equiposNoAsociados = equipos.filter(
    (eq) => !equiposTemporada.find((et) => et.id === eq.id)
  );

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">{liga?.nombre || 'Liga'}</h2>
        <p className="text-gray-400">{liga?.pais || 'Sin país'} - Panel de Gestión</p>
      </div>

      {seccion === 'menu' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <button onClick={() => setSeccion('temporadas')} className="bg-dark-card rounded-2xl p-6 border border-dark-border hover:border-accent-green transition-all hover:scale-[1.02] text-left group">
            <div className="w-14 h-14 bg-accent-green/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform"><span className="text-3xl">📅</span></div>
            <h3 className="text-lg font-bold text-white mb-1">Temporadas</h3>
            <p className="text-gray-400 text-sm">{loadingTemporadas ? 'Cargando...' : `${temporadas.length} temporada(s)`}{errorTemporadas && ' (error)'}</p>
          </button>

          <button onClick={() => setSeccion('equipos')} className="bg-dark-card rounded-2xl p-6 border border-dark-border hover:border-accent-blue transition-all hover:scale-[1.02] text-left group">
            <div className="w-14 h-14 bg-accent-blue/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform"><span className="text-3xl">👥</span></div>
            <h3 className="text-lg font-bold text-white mb-1">Equipos</h3>
            <p className="text-gray-400 text-sm">{loadingEquipos ? 'Cargando...' : `${equipos.length} equipo(s)`}{errorEquipos && ' (error)'}</p>
          </button>

          <button onClick={() => setSeccion('partidos')} className="bg-dark-card rounded-2xl p-6 border border-dark-border hover:border-accent-orange transition-all hover:scale-[1.02] text-left group">
            <div className="w-14 h-14 bg-accent-orange/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform"><span className="text-3xl">⚽</span></div>
            <h3 className="text-lg font-bold text-white mb-1">Partidos</h3>
            <p className="text-gray-400 text-sm">Gestionar partidos</p>
          </button>

          <button onClick={() => setSeccion('estadisticas')} className="bg-dark-card rounded-2xl p-6 border border-dark-border hover:border-accent-purple transition-all hover:scale-[1.02] text-left group">
            <div className="w-14 h-14 bg-accent-purple/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform"><span className="text-3xl">📊</span></div>
            <h3 className="text-lg font-bold text-white mb-1">Estadísticas</h3>
            <p className="text-gray-400 text-sm">Ver métricas y tabla</p>
          </button>
        </div>
      )}

      {/* TEMPORADAS */}
      {seccion === 'temporadas' && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold text-white">Temporadas</h3>
            <button onClick={() => setMostrarFormTemporada(true)} className="bg-accent-green hover:bg-accent-green/80 text-dark-bg font-bold px-6 py-3 rounded-xl transition-all flex items-center gap-2">
              <span>+</span> Nueva Temporada
            </button>
          </div>

          {mostrarFormTemporada && (
            <form onSubmit={handleCrearTemporada} className="bg-dark-card rounded-2xl p-6 border border-accent-green/50 mb-6">
              <h4 className="text-lg font-semibold text-white mb-4">Crear Nueva Temporada</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Nombre *</label>
                  <input name="nombre" required placeholder="Ej: 2024-2025" className="w-full px-4 py-3 rounded-xl border bg-dark-bg text-white border-dark-border" />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Fecha Inicio</label>
                  <input name="fecha_inicio" type="date" className="w-full px-4 py-3 rounded-xl border bg-dark-bg text-white border-dark-border" />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Fecha Fin</label>
                  <input name="fecha_fin" type="date" className="w-full px-4 py-3 rounded-xl border bg-dark-bg text-white border-dark-border" />
                </div>
              </div>
              <div className="flex gap-3 mt-4">
                <button type="submit" disabled={actionLoading} className="bg-accent-green text-dark-bg font-bold px-6 py-3 rounded-xl disabled:opacity-50">
                  {actionLoading ? 'Guardando...' : 'Guardar'}
                </button>
                <button type="button" onClick={() => setMostrarFormTemporada(false)} className="bg-dark-border text-white px-6 py-3 rounded-xl">Cancelar</button>
              </div>
            </form>
          )}

          {loadingTemporadas ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-accent-green border-t-transparent"></div>
              <span className="ml-3 text-gray-400">Cargando temporadas...</span>
            </div>
          ) : errorTemporadas ? (
            <div className="text-center py-8 bg-dark-card rounded-xl border border-dark-border">
              <p className="text-red-400 mb-4">{errorTemporadas}</p>
              <button onClick={cargarTemporadas} className="bg-accent-green text-dark-bg px-4 py-2 rounded-lg">Reintentar</button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {temporadas.map((temp) => (
                <div key={temp.id} className="bg-dark-card rounded-xl p-4 border border-dark-border">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-accent-green/20 rounded-lg flex items-center justify-center"><span>📅</span></div>
                    <div>
                      <h4 className="font-semibold text-white">{temp.nombre}</h4>
                      <p className="text-xs text-gray-400">{temp.fecha_inicio || 'Sin fecha'} — {temp.fecha_fin || 'Sin fecha'}</p>
                    </div>
                  </div>
                </div>
              ))}
              {temporadas.length === 0 && (
                <div className="col-span-full text-center py-12"><p className="text-gray-400">No hay temporadas creadas</p></div>
              )}
            </div>
          )}
        </div>
      )}

      {/* EQUIPOS */}
      {seccion === 'equipos' && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold text-white">Equipos</h3>
            <button onClick={abrirFormCrearEquipo} className="bg-accent-blue hover:bg-accent-blue/80 text-dark-bg font-bold px-6 py-3 rounded-xl transition-all flex items-center gap-2">
              <span>+</span> Nuevo Equipo
            </button>
          </div>

          {loadingEquipos ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-accent-blue border-t-transparent"></div>
              <span className="ml-3 text-gray-400">Cargando equipos...</span>
            </div>
          ) : errorEquipos ? (
            <div className="text-center py-8 bg-dark-card rounded-xl border border-dark-border">
              <p className="text-red-400 mb-4">{errorEquipos}</p>
              <button onClick={cargarEquipos} className="bg-accent-blue text-dark-bg px-4 py-2 rounded-lg">Reintentar</button>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {equipos.map((eq) => (
                <EquipoCard key={eq.id} equipo={eq} onEdit={abrirFormEditarEquipo} onDelete={confirmarEliminarEquipo} disabled={actionLoading} />
              ))}
              {equipos.length === 0 && (
                <div className="col-span-full text-center py-12"><p className="text-gray-400">No hay equipos creados</p></div>
              )}
            </div>
          )}
        </div>
      )}

      {/* PARTIDOS */}
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
              <button onClick={() => setSeccion('temporadas')} className="text-accent-orange hover:underline">Ir a Temporadas</button>
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
                className="px-4 py-3 rounded-xl border bg-dark-bg text-white border-dark-border w-full max-w-xs"
              >
                <option value="">Seleccionar temporada...</option>
                {temporadas.map((temp) => (
                  <option key={temp.id} value={temp.id}>{temp.nombre}</option>
                ))}
              </select>
            </div>
          )}

          {/* REQ 5: Equipos asociados a temporada */}
          {temporadaSeleccionada && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-gray-300">Equipos en esta temporada ({equiposTemporada.length})</h4>
                <button
                  onClick={() => setMostrarGestionEquiposTemp(!mostrarGestionEquiposTemp)}
                  className="text-xs text-accent-blue hover:underline"
                >
                  {mostrarGestionEquiposTemp ? 'Ocultar gestión' : 'Gestionar equipos'}
                </button>
              </div>

              {mostrarGestionEquiposTemp && (
                <div className="bg-dark-card rounded-xl p-4 border border-dark-border mb-3">
                  <div className="flex gap-3 mb-4">
                    <select
                      value={equipoParaAgregar}
                      onChange={(e) => setEquipoParaAgregar(e.target.value)}
                      className="flex-1 px-3 py-2 rounded-lg border bg-dark-bg text-white border-dark-border text-sm"
                    >
                      <option value="">Seleccionar equipo para agregar...</option>
                      {equiposNoAsociados.map((eq) => (
                        <option key={eq.id} value={eq.id}>{eq.nombre}</option>
                      ))}
                    </select>
                    <button
                      onClick={handleAsociarEquipo}
                      disabled={!equipoParaAgregar}
                      className="bg-accent-green text-dark-bg px-4 py-2 rounded-lg text-sm font-bold disabled:opacity-50"
                    >
                      Agregar
                    </button>
                  </div>
                  {loadingEquiposTemp ? (
                    <p className="text-gray-400 text-sm">Cargando...</p>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {equiposTemporada.map((eq) => (
                        <div key={eq.id} className="flex items-center gap-2 bg-dark-bg px-3 py-1 rounded-full border border-dark-border">
                          <span className="text-sm text-white">{eq.nombre}</span>
                          <button
                            onClick={() => handleDesasociarEquipo(eq.id)}
                            className="text-red-400 hover:text-red-300 text-xs font-bold"
                          >✕</button>
                        </div>
                      ))}
                      {equiposTemporada.length === 0 && (
                        <p className="text-gray-500 text-sm">No hay equipos asociados aún</p>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* REQ 6: form sin árbitro/estadio */}
          {mostrarFormPartido && equipos.length >= 2 && (
            <form onSubmit={handleCrearPartido} className="bg-dark-card rounded-2xl p-6 border border-accent-orange/50 mb-6">
              <h4 className="text-lg font-semibold text-white mb-4">Crear Nuevo Partido</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Fecha</label>
                  <input name="fecha" type="datetime-local" className="w-full px-4 py-3 rounded-xl border bg-dark-bg text-white border-dark-border" />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Equipo Local *</label>
                  <select name="equipo_local" required className="w-full px-4 py-3 rounded-xl border bg-dark-bg text-white border-dark-border">
                    <option value="">Seleccionar...</option>
                    {equipos.map((eq) => <option key={eq.id} value={eq.id}>{eq.nombre}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Equipo Visitante *</label>
                  <select name="equipo_visitante" required className="w-full px-4 py-3 rounded-xl border bg-dark-bg text-white border-dark-border">
                    <option value="">Seleccionar...</option>
                    {equipos.map((eq) => <option key={eq.id} value={eq.id}>{eq.nombre}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Goles Local</label>
                  <input name="goles_local" type="number" min="0" defaultValue="0" className="w-full px-4 py-3 rounded-xl border bg-dark-bg text-white border-dark-border" />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Goles Visitante</label>
                  <input name="goles_visitante" type="number" min="0" defaultValue="0" className="w-full px-4 py-3 rounded-xl border bg-dark-bg text-white border-dark-border" />
                </div>
              </div>
              <div className="flex gap-3 mt-4">
                <button type="submit" disabled={actionLoading} className="bg-accent-orange text-dark-bg font-bold px-6 py-3 rounded-xl disabled:opacity-50">
                  {actionLoading ? 'Guardando...' : 'Guardar'}
                </button>
                <button type="button" onClick={() => setMostrarFormPartido(false)} className="bg-dark-border text-white px-6 py-3 rounded-xl">Cancelar</button>
              </div>
            </form>
          )}

          {loadingPartidos ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-accent-orange border-t-transparent"></div>
              <span className="ml-3 text-gray-400">Cargando partidos...</span>
            </div>
          ) : errorPartidos ? (
            <div className="text-center py-8 bg-dark-card rounded-xl border border-dark-border">
              <p className="text-red-400 mb-4">{errorPartidos}</p>
              <button onClick={cargarPartidos} className="bg-accent-orange text-dark-bg px-4 py-2 rounded-lg">Reintentar</button>
            </div>
          ) : (
            <div className="space-y-3">
              {partidos.map((partido) => (
                <div key={partido.id} className="bg-dark-card rounded-xl p-4 border border-dark-border">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-gray-400">{partido.fecha ? new Date(partido.fecha).toLocaleDateString() : 'Sin fecha'}</span>
                      <span className="font-bold text-white">{getNombreEquipo(partido.equipo_local)}</span>
                    </div>
                    <div className="bg-dark-bg px-4 py-2 rounded-xl flex items-center gap-4">
                      <span className="text-2xl font-bold text-accent-green">{partido.goles_local}</span>
                      <span className="text-gray-400">-</span>
                      <span className="text-2xl font-bold text-accent-orange">{partido.goles_visitante}</span>
                    </div>
                    <span className="font-bold text-white">{getNombreEquipo(partido.equipo_visitante)}</span>
                  </div>

                  {/* REQ 1: formulario inline de edición */}
                  {editandoPartidoId === partido.id ? (
                    <div className="mt-4 pt-4 border-t border-dark-border">
                      <div className="grid grid-cols-3 gap-3 mb-3">
                        <div>
                          <label className="block text-xs text-gray-400 mb-1">Goles Local</label>
                          <input
                            type="number" min="0"
                            value={partidoEditado.goles_local}
                            onChange={(e) => setPartidoEditado({ ...partidoEditado, goles_local: parseInt(e.target.value) || 0 })}
                            className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white text-sm"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-400 mb-1">Goles Visitante</label>
                          <input
                            type="number" min="0"
                            value={partidoEditado.goles_visitante}
                            onChange={(e) => setPartidoEditado({ ...partidoEditado, goles_visitante: parseInt(e.target.value) || 0 })}
                            className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white text-sm"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-400 mb-1">Fecha</label>
                          <input
                            type="date"
                            value={partidoEditado.fecha ? new Date(partidoEditado.fecha).toISOString().split('T')[0] : ''}
                            onChange={(e) => setPartidoEditado({ ...partidoEditado, fecha: e.target.value || null })}
                            className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white text-sm"
                          />
                        </div>
                      </div>
                      <div className="flex gap-2 justify-end">
                        <button
                          onClick={() => { setEditandoPartidoId(null); setPartidoEditado({ goles_local: 0, goles_visitante: 0, fecha: null }); }}
                          className="px-4 py-2 bg-dark-border text-white rounded-lg text-sm"
                        >Cancelar</button>
                        <button
                          onClick={() => handleGuardarPartido(partido.id)}
                          disabled={savingPartido}
                          className="px-4 py-2 bg-accent-green text-dark-bg rounded-lg text-sm font-bold disabled:opacity-50"
                        >{savingPartido ? 'Guardando...' : 'Guardar'}</button>
                      </div>
                    </div>
                  ) : (
                    <div className="mt-2 flex justify-end">
                      <button
                        onClick={() => {
                          setEditandoPartidoId(partido.id);
                          setPartidoEditado({ goles_local: partido.goles_local, goles_visitante: partido.goles_visitante, fecha: partido.fecha });
                        }}
                        className="text-xs text-accent-blue hover:text-accent-blue/80 px-2 py-1 rounded hover:bg-dark-border"
                      >✏️ Editar</button>
                    </div>
                  )}
                </div>
              ))}
              {partidos.length === 0 && temporadaSeleccionada && (
                <div className="text-center py-8"><p className="text-gray-400">No hay partidos en esta temporada</p></div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ESTADÍSTICAS + RANKING */}
      {seccion === 'estadisticas' && (
        <div>
          {/* Tabs */}
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setSeccionEstadisticas('estadisticas')}
              className={`px-5 py-2 rounded-xl font-semibold text-sm transition-all ${seccionEstadisticas === 'estadisticas' ? 'bg-accent-purple text-white' : 'bg-dark-card text-gray-400 hover:text-white border border-dark-border'}`}
            >📊 Estadísticas</button>
            <button
              onClick={() => { setSeccionEstadisticas('tabla'); cargarRankingEquipos(); }}
              className={`px-5 py-2 rounded-xl font-semibold text-sm transition-all ${seccionEstadisticas === 'tabla' ? 'bg-accent-blue text-white' : 'bg-dark-card text-gray-400 hover:text-white border border-dark-border'}`}
            >🏆 Tabla de Posiciones</button>
          </div>

          {/* REQ 2/4: estadísticas con filtro por temporada */}
          {seccionEstadisticas === 'estadisticas' && (
            <div>
              <div className="flex items-center gap-4 mb-6">
                <h3 className="text-2xl font-bold text-white">Estadísticas</h3>
                <select
                  value={temporadaEstadisticas}
                  onChange={(e) => {
                    setTemporadaEstadisticas(e.target.value);
                    cargarEstadisticas(e.target.value || null);
                  }}
                  className="px-3 py-2 rounded-lg border bg-dark-bg text-white border-dark-border text-sm"
                >
                  <option value="">Todas las temporadas</option>
                  {temporadas.map((t) => <option key={t.id} value={t.id}>{t.nombre}</option>)}
                </select>
                {loadingEstadisticas && <span className="text-gray-400 text-sm">Cargando...</span>}
              </div>

              <>
                {/* KPIs */}
                {estadisticas && (
                  <>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="bg-dark-card rounded-xl p-5 border border-dark-border">
                        <p className="text-gray-400 text-sm mb-1">Total Partidos</p>
                        <p className="text-3xl font-bold text-accent-blue">
                          {estadisticas.total_partidos || 0}
                        </p>
                      </div>

                      <div className="bg-dark-card rounded-xl p-5 border border-dark-border">
                        <p className="text-gray-400 text-sm mb-1">Promedio Goles</p>
                        <p className="text-3xl font-bold text-accent-green">
                          {(estadisticas.promedio_goles || 0).toFixed(2)}
                        </p>
                      </div>

                      <div className="bg-dark-card rounded-xl p-5 border border-dark-border">
                        <p className="text-gray-400 text-sm mb-1">
                          Partidos &gt;{estadisticas.umbral_goles || 3} goles
                        </p>
                        <p className="text-3xl font-bold text-accent-orange">
                          {estadisticas.partidos_mas_3_goles || 0}
                        </p>
                      </div>

                      <div className="bg-dark-card rounded-xl p-5 border border-dark-border">
                        <p className="text-gray-400 text-sm mb-1">
                          Partidos ≤{estadisticas.umbral_goles || 3} goles
                        </p>
                        <p className="text-3xl font-bold text-accent-purple">
                          {estadisticas.partidos_menos_igual_3_goles || 0}
                        </p>
                      </div>
                    </div>

                    <div className="bg-dark-card rounded-xl p-4 border border-dark-border text-sm text-gray-400">
                      ✅ Verificación:{" "}
                      {(estadisticas.partidos_mas_3_goles || 0) +
                        (estadisticas.partidos_menos_igual_3_goles || 0)}{" "}
                      = {estadisticas.total_partidos || 0} partidos totales
                      {((estadisticas.partidos_mas_3_goles || 0) +
                        (estadisticas.partidos_menos_igual_3_goles || 0)) ===
                        (estadisticas.total_partidos || 0)
                        ? " ✓ Consistente"
                        : " ⚠️ Inconsistente"}
                      {estadisticas.temporada_id && (
                        <span className="ml-4 text-accent-green">
                          Filtrado por temporada
                        </span>
                      )}
                    </div>
                  </>
                )}

                {/* 🔥 GRÁFICAS SIEMPRE MONTADAS */}
                <div style={{ minHeight: 400 }}>
                  <Estadisticas
                    estadisticasExternas={estadisticas}
                    rankingExterno={rankingEquipos}
                  />
                </div>
              </>
            </div>
          )}

          {/* REQ 3: tabla de posiciones */}
          {seccionEstadisticas === 'tabla' && (
            <div>
              <h3 className="text-2xl font-bold text-white mb-6">Tabla de Posiciones</h3>
              {loadingRanking ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-10 w-10 border-4 border-accent-blue border-t-transparent"></div>
                </div>
              ) : rankingEquipos.length === 0 ? (
                <div className="text-center py-12 bg-dark-card rounded-xl border border-dark-border">
                  <p className="text-gray-400">No hay datos suficientes para calcular la tabla de posiciones</p>
                </div>
              ) : (
                <div className="bg-dark-card rounded-2xl border border-dark-border overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-gray-400 border-b border-dark-border bg-dark-bg/50">
                          <th className="text-left py-3 px-4">#</th>
                          <th className="text-left py-3 px-4">Equipo</th>
                          <th className="text-center py-3 px-3">PJ</th>
                          <th className="text-center py-3 px-3">G</th>
                          <th className="text-center py-3 px-3">E</th>
                          <th className="text-center py-3 px-3">D</th>
                          <th className="text-center py-3 px-3">GF</th>
                          <th className="text-center py-3 px-3">GC</th>
                          <th className="text-center py-3 px-3">DG</th>
                          <th className="text-center py-3 px-3 font-bold text-white">PTS</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rankingEquipos.map((eq, idx) => (
                          <tr key={eq.equipo_id} className="border-b border-dark-border hover:bg-dark-bg/30 transition-colors">
                            <td className="py-3 px-4">
                              <span className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs ${idx === 0 ? 'bg-yellow-500 text-dark-bg' : idx === 1 ? 'bg-gray-400 text-dark-bg' : idx === 2 ? 'bg-amber-700 text-white' : 'bg-dark-border text-gray-400'}`}>
                                {idx + 1}
                              </span>
                            </td>
                            <td className="py-3 px-4 font-semibold text-white">{eq.nombre}</td>
                            <td className="py-3 px-3 text-center text-gray-300">{eq.partidos_jugados}</td>
                            <td className="py-3 px-3 text-center text-accent-green">{eq.victorias}</td>
                            <td className="py-3 px-3 text-center text-gray-300">{eq.empates}</td>
                            <td className="py-3 px-3 text-center text-red-400">{eq.derrotas}</td>
                            <td className="py-3 px-3 text-center text-gray-300">{eq.goles_favor}</td>
                            <td className="py-3 px-3 text-center text-gray-300">{eq.goles_contra}</td>
                            <td className={`py-3 px-3 text-center font-medium ${eq.diferencia_goles > 0 ? 'text-accent-green' : eq.diferencia_goles < 0 ? 'text-red-400' : 'text-gray-400'}`}>
                              {eq.diferencia_goles > 0 ? '+' : ''}{eq.diferencia_goles}
                            </td>
                            <td className="py-3 px-3 text-center font-bold text-white text-base">{eq.puntos}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* MODALS */}
      <Modal isOpen={mostrarFormEquipo} onClose={() => { setMostrarFormEquipo(false); setEquipoEditando(null); }} title={equipoEditando ? 'Editar Equipo' : 'Nuevo Equipo'}>
        <EquipoForm equipo={equipoEditando} onSubmit={handleSubmitEquipo} onCancel={() => { setMostrarFormEquipo(false); setEquipoEditando(null); }} isSubmitting={actionLoading} />
      </Modal>

      <ConfirmDialog
        isOpen={mostrarConfirmEliminar}
        onClose={() => { setMostrarConfirmEliminar(false); setEquipoEliminando(null); }}
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