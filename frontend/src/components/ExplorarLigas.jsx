import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Toast } from './Toast';
import { ConfirmDialog } from './Modal';
import SearchBar from './SearchBar';
import {
  obtenerLigasExternas,
  obtenerEquiposExternos,
  obtenerPartidosExternos,
  obtenerEstadoCache,
  importarLiga,
  actualizarLigaEx,
} from '../api';

export default function ExplorarLigas() {
  const [ligas, setLigas] = useState([]);
  const [equipos, setEquipos] = useState([]);
  const [partidos, setPartidos] = useState([]);
  const [ligaSeleccionada, setLigaSeleccionada] = useState(null);
  const [temporada, setTemporada] = useState(2024);

  const [loadingLigas, setLoadingLigas] = useState(true);
  const [loadingEquipos, setLoadingEquipos] = useState(false);
  const [loadingPartidos, setLoadingPartidos] = useState(false);
  const [errorLigas, setErrorLigas] = useState(null);
  const [errorEquipos, setErrorEquipos] = useState(null);
  const [errorPartidos, setErrorPartidos] = useState(null);

  const [importing, setImporting] = useState(false);
  const [cacheStatus, setCacheStatus] = useState(null);
  const [mostrarConfirmImportar, setMostrarConfirmImportar] = useState(false);
  const [ligaAImportar, setLigaAImportar] = useState(null);
  const [ligaActualizando, setLigaActualizando] = useState(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCountry, setSelectedCountry] = useState(null);

  const [toast, setToast] = useState(null);
  const isMountedRef = useRef(true);
  const requestIdRef = useRef(0);

  // Component-scoped abort controllers — one per operation type
  // This prevents cancelling requests from sibling components
  const ligasAbortRef = useRef(null);
  const equiposAbortRef = useRef(null);
  const partidosAbortRef = useRef(null);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      // Only abort this component's own requests on unmount
      ligasAbortRef.current?.abort();
      equiposAbortRef.current?.abort();
      partidosAbortRef.current?.abort();
    };
  }, []);

  const countries = useMemo(() => {
    const countrySet = new Set();
    (ligas || []).forEach((liga) => {
      if (liga.country) countrySet.add(liga.country);
    });
    return Array.from(countrySet).sort();
  }, [ligas]);

  const ligasFiltradas = useMemo(() => {
    let filtered = ligas || [];
    if (selectedCountry) {
      filtered = filtered.filter((liga) => liga.country === selectedCountry);
    }
    if (searchTerm) {
      const term = searchTerm.toLowerCase().trim();
      filtered = filtered.filter((liga) => {
        const nameMatch = (liga.name || '').toLowerCase().includes(term);
        const countryMatch = (liga.country || '').toLowerCase().includes(term);
        return nameMatch || countryMatch;
      });
    }
    return filtered;
  }, [ligas, searchTerm, selectedCountry]);

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

  const cargarCacheStatus = useCallback(async () => {
    try {
      const status = await obtenerEstadoCache();
      if (isMountedRef.current) {
        setCacheStatus(status);
      }
    } catch (error) {
      console.error('Error cargando estado de cache:', error);
    }
  }, []);

  const cargarLigas = useCallback(async (forceRefresh = false) => {
    if (!isMountedRef.current) return;

    // Abort any previous ligas request from this component
    ligasAbortRef.current?.abort();
    ligasAbortRef.current = new AbortController();

    const requestId = ++requestIdRef.current;
    console.log(`[ExplorarLigas] Iniciando cargarLigas, requestId: ${requestId}`);

    setLoadingLigas(true);
    setErrorLigas(null);

    try {
      const data = await obtenerLigasExternas(forceRefresh, `ligas-${requestId}`);

      if (!isMountedRef.current || requestId !== requestIdRef.current) {
        console.log(`[ExplorarLigas] cargarLigas abortado, requestId: ${requestId}`);
        return;
      }

      setLigas(Array.isArray(data) ? data : []);
      console.log(`[ExplorarLigas] ligas cargadas: ${Array.isArray(data) ? data.length : 0}`);
    } catch (error) {
      if (!isMountedRef.current || requestId !== requestIdRef.current) return;
      if (error?.name === 'AbortError') return;
      console.error(`[ExplorarLigas] Error cargando ligas:`, error);
      setErrorLigas(error.message || 'Error al cargar ligas');
    } finally {
      if (isMountedRef.current && requestId === requestIdRef.current) {
        setLoadingLigas(false);
      }
    }
  }, []);

  const refrescarLigas = useCallback(async () => {
    if (!isMountedRef.current) return;

    ligasAbortRef.current?.abort();
    ligasAbortRef.current = new AbortController();

    const requestId = ++requestIdRef.current;

    setLoadingLigas(true);
    setErrorLigas(null);

    try {
      const data = await obtenerLigasExternas(true, `ligas-refresh-${requestId}`);

      if (!isMountedRef.current || requestId !== requestIdRef.current) return;

      setLigas(Array.isArray(data) ? data : []);
      showToast('Ligas actualizadas desde API', 'success');
    } catch (error) {
      if (!isMountedRef.current || requestId !== requestIdRef.current) return;
      if (error?.name === 'AbortError') return;
      setErrorLigas(error.message || 'Error al actualizar ligas');
      showToast('Error al actualizar ligas', 'error');
    } finally {
      if (isMountedRef.current && requestId === requestIdRef.current) {
        setLoadingLigas(false);
      }
    }
  }, [showToast]);

  const seleccionarLiga = useCallback(async (liga) => {
    if (!isMountedRef.current || !liga?.id) return;

    equiposAbortRef.current?.abort();
    equiposAbortRef.current = new AbortController();

    const requestId = ++requestIdRef.current;

    setLigaSeleccionada(liga);
    setEquipos([]);
    setPartidos([]);
    setErrorEquipos(null);
    setErrorPartidos(null);
    setLoadingEquipos(true);

    try {
      const data = await obtenerEquiposExternos(liga.id, false, `equipos-${liga.id}-${requestId}`);

      if (!isMountedRef.current || requestId !== requestIdRef.current) return;

      setEquipos(Array.isArray(data) ? data : []);
    } catch (error) {
      if (!isMountedRef.current || requestId !== requestIdRef.current) return;
      if (error?.name === 'AbortError') return;
      setErrorEquipos(error.message || 'Error al cargar equipos');
    } finally {
      if (isMountedRef.current && requestId === requestIdRef.current) {
        setLoadingEquipos(false);
      }
    }
  }, []);

  const cargarPartidos = useCallback(async () => {
    if (!isMountedRef.current || !ligaSeleccionada?.id) return;

    partidosAbortRef.current?.abort();
    partidosAbortRef.current = new AbortController();

    const requestId = ++requestIdRef.current;

    setLoadingPartidos(true);
    setErrorPartidos(null);

    try {
      const data = await obtenerPartidosExternos(
        ligaSeleccionada.id,
        temporada,
        false,
        `partidos-${ligaSeleccionada.id}-${temporada}-${requestId}`
      );

      if (!isMountedRef.current || requestId !== requestIdRef.current) return;

      setPartidos(Array.isArray(data) ? data : []);
    } catch (error) {
      if (!isMountedRef.current || requestId !== requestIdRef.current) return;
      if (error?.name === 'AbortError') return;
      setErrorPartidos(error.message || 'Error al cargar partidos');
    } finally {
      if (isMountedRef.current && requestId === requestIdRef.current) {
        setLoadingPartidos(false);
      }
    }
  }, [ligaSeleccionada, temporada]);

  // Initial load — stable empty deps array, cargarLigas is stable (no deps)
  useEffect(() => {
    cargarLigas(false);
    cargarCacheStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load partidos whenever liga or temporada changes
  useEffect(() => {
    if (ligaSeleccionada) {
      cargarPartidos();
    } else {
      setPartidos([]);
      setLoadingPartidos(false);
    }
  }, [ligaSeleccionada, temporada, cargarPartidos]);

  const confirmarImportar = useCallback((liga) => {
    setLigaAImportar(liga);
    setMostrarConfirmImportar(true);
  }, []);

  const handleImportar = useCallback(async () => {
    if (!ligaAImportar?.id || !isMountedRef.current) return;

    setImporting(true);

    try {
      const result = await importarLiga(ligaAImportar.id);
      if (!isMountedRef.current) return;

      showToast(
        `Liga "${ligaAImportar.name}" importada (${result?.equipos_guardados || 0} equipos, ${result?.partidos_guardados || 0} partidos)`,
        'success'
      );
      setMostrarConfirmImportar(false);
      setLigaAImportar(null);
      cargarCacheStatus();
    } catch (error) {
      if (!isMountedRef.current) return;
      showToast('Error al importar liga', 'error');
    } finally {
      if (isMountedRef.current) {
        setImporting(false);
      }
    }
  }, [ligaAImportar, showToast, cargarCacheStatus]);

  const handleActualizar = useCallback(
    async (liga) => {
      if (!liga?.id || !isMountedRef.current) return;

      setLigaActualizando(liga.id);

      try {
        await actualizarLigaEx(liga.id, temporada);
        if (!isMountedRef.current) return;

        showToast('Datos actualizados desde API', 'success');
        await seleccionarLiga(liga);
        cargarCacheStatus();
      } catch (error) {
        if (!isMountedRef.current) return;
        showToast('Error al actualizar datos', 'error');
      } finally {
        if (isMountedRef.current) {
          setLigaActualizando(null);
        }
      }
    },
    [temporada, showToast, seleccionarLiga, cargarCacheStatus]
  );

  const getNombreEquipo = useCallback(
    (id) => {
      const eq = equipos.find((e) => e.id === id);
      return eq ? eq.name : `Equipo ${id}`;
    },
    [equipos]
  );

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white mb-1">Explorar Ligas</h2>
            <p className="text-gray-400 text-sm">Datos guardados localmente para optimizar consumo de API</p>
          </div>
          <button
            onClick={refrescarLigas}
            disabled={loadingLigas}
            className="bg-accent-purple hover:bg-accent-purple/80 text-white px-4 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50"
          >
            <svg
              className={`w-4 h-4 ${loadingLigas ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Actualizar
          </button>
        </div>

        {cacheStatus && (
          <div className="mt-4 bg-dark-card rounded-xl p-4 border border-dark-border">
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${cacheStatus.ligas_count > 0 ? 'bg-accent-green' : 'bg-gray-500'}`}></div>
                <span className="text-gray-400">Ligas: <span className="text-white">{cacheStatus.ligas_count}</span></span>
              </div>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${cacheStatus.equipos_count > 0 ? 'bg-accent-green' : 'bg-gray-500'}`}></div>
                <span className="text-gray-400">Equipos: <span className="text-white">{cacheStatus.equipos_count}</span></span>
              </div>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${cacheStatus.partidos_count > 0 ? 'bg-accent-green' : 'bg-gray-500'}`}></div>
                <span className="text-gray-400">Partidos: <span className="text-white">{cacheStatus.partidos_count}</span></span>
              </div>
              <div className="ml-auto text-gray-500 text-xs">
                TTL: Ligas {cacheStatus.ttl_config?.ligas} | Equipos {cacheStatus.ttl_config?.equipos} | Partidos {cacheStatus.ttl_config?.partidos}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-dark-card rounded-2xl p-6 border border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-4">Ligas Disponibles</h3>

          <SearchBar
            value={searchTerm}
            onChange={setSearchTerm}
            placeholder="Buscar liga o país..."
            countries={countries}
            selectedCountry={selectedCountry}
            onCountryChange={setSelectedCountry}
            resultCount={ligasFiltradas.length}
            totalCount={ligas.length}
          />

          {loadingLigas && !errorLigas ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-accent-blue border-t-transparent"></div>
              <span className="ml-3 text-gray-400">Cargando...</span>
            </div>
          ) : errorLigas ? (
            <div className="text-center py-8">
              <p className="text-red-400 mb-4">{errorLigas}</p>
              <button
                onClick={() => cargarLigas(false)}
                className="bg-accent-blue hover:bg-accent-blue/80 text-dark-bg px-4 py-2 rounded-lg"
              >
                Reintentar
              </button>
            </div>
          ) : (
            <div className="space-y-3 max-h-[450px] overflow-y-auto mt-4">
              {ligasFiltradas.map((liga) => (
                <div
                  key={liga.id}
                  onClick={() => seleccionarLiga(liga)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    ligaSeleccionada?.id === liga.id
                      ? 'border-accent-blue bg-accent-blue/10'
                      : 'border-dark-border hover:border-accent-blue/50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {liga.logo && (
                      <img src={liga.logo} alt={liga.name} className="w-10 h-10 rounded-lg object-contain bg-white/10" />
                    )}
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-white truncate">{liga.name}</h4>
                      <p className="text-sm text-gray-400">{liga.country}</p>
                    </div>
                    <div className="flex gap-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          confirmarImportar(liga);
                        }}
                        disabled={importing}
                        className="p-2 rounded-lg bg-accent-green/20 text-accent-green hover:bg-accent-green hover:text-white transition-all disabled:opacity-50"
                        title="Importar"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
              {ligasFiltradas.length === 0 && (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-dark-border rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <p className="text-gray-400 mb-2">No se encontraron ligas</p>
                  <button
                    onClick={() => { setSearchTerm(''); setSelectedCountry(null); }}
                    className="text-accent-blue hover:text-accent-blue/80 text-sm transition-colors"
                  >
                    Limpiar filtros
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="space-y-6">
          {ligaSeleccionada ? (
            <>
              <div className="bg-dark-card rounded-2xl p-6 border border-dark-border">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    {ligaSeleccionada.logo && (
                      <img src={ligaSeleccionada.logo} alt={ligaSeleccionada.name} className="w-12 h-12 rounded-xl object-contain bg-white/10" />
                    )}
                    <div>
                      <h3 className="text-xl font-bold text-white">{ligaSeleccionada.name}</h3>
                      <p className="text-gray-400">{ligaSeleccionada.country}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleActualizar(ligaSeleccionada)}
                    disabled={ligaActualizando === ligaSeleccionada.id}
                    className="bg-accent-blue hover:bg-accent-blue/80 text-dark-bg px-4 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50"
                  >
                    <svg className={`w-4 h-4 ${ligaActualizando === ligaSeleccionada.id ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Actualizar
                  </button>
                </div>

                <div className="flex items-center gap-4 text-sm">
                  <select
                    value={temporada}
                    onChange={(e) => setTemporada(parseInt(e.target.value))}
                    className="bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-white"
                  >
                    {[2024, 2023, 2022, 2021].map((y) => (
                      <option key={y} value={y}>{y}</option>
                    ))}
                  </select>
                  <span className="text-gray-400">
                    {loadingPartidos ? 'Cargando partidos...' : `${partidos.length} partidos${errorPartidos ? ' (error)' : ''}`}
                  </span>
                </div>
              </div>

              <div className="bg-dark-card rounded-2xl p-6 border border-dark-border">
                <h4 className="text-lg font-semibold text-white mb-4">
                  Equipos{' '}
                  {loadingEquipos && <span className="text-gray-400 text-sm">(Cargando...)</span>}
                  {errorEquipos && <span className="text-red-400 text-sm ml-2">(Error)</span>}
                </h4>

                {loadingEquipos ? (
                  <div className="animate-spin rounded-full h-8 w-8 border-4 border-accent-green border-t-transparent mx-auto"></div>
                ) : errorEquipos ? (
                  <div className="text-center py-4">
                    <p className="text-red-400 mb-2">{errorEquipos}</p>
                    <button onClick={() => seleccionarLiga(ligaSeleccionada)} className="text-accent-blue hover:underline text-sm">Reintentar</button>
                  </div>
                ) : (
                  <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
                    {(equipos || []).map((eq) => (
                      <div key={eq.id} className="bg-dark-bg rounded-lg p-3 text-center">
                        {eq.logo && <img src={eq.logo} alt={eq.name} className="w-10 h-10 mx-auto rounded-lg object-contain" />}
                        <p className="text-xs text-white mt-2 truncate">{eq.name}</p>
                      </div>
                    ))}
                    {(!equipos || equipos.length === 0) && (
                      <p className="col-span-full text-center text-gray-400 py-4">No hay equipos</p>
                    )}
                  </div>
                )}
              </div>

              <div className="bg-dark-card rounded-2xl p-6 border border-dark-border">
                <h4 className="text-lg font-semibold text-white mb-4">
                  Partidos Recientes{' '}
                  {errorPartidos && <span className="text-red-400 text-sm ml-2">(Error al cargar)</span>}
                </h4>

                {loadingPartidos ? (
                  <div className="animate-spin rounded-full h-8 w-8 border-4 border-accent-orange border-t-transparent mx-auto"></div>
                ) : errorPartidos ? (
                  <div className="text-center py-4">
                    <p className="text-red-400 mb-2">{errorPartidos}</p>
                    <button onClick={cargarPartidos} className="text-accent-blue hover:underline text-sm">Reintentar</button>
                  </div>
                ) : (
                  <div className="space-y-2 max-h-[300px] overflow-y-auto">
                    {(partidos || []).slice(0, 20).map((partido) => (
                      <div key={partido.id} className="bg-dark-bg rounded-lg p-3 flex items-center justify-between">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <span className="text-xs text-gray-500 w-8">{partido.jornada}</span>
                          <span className="text-sm text-white truncate">{getNombreEquipo(partido.equipo_local_id)}</span>
                        </div>
                        <div className="bg-dark-card px-3 py-1 rounded-lg flex items-center gap-2 mx-2">
                          <span className="font-bold text-accent-green">{partido.goles_local}</span>
                          <span className="text-gray-400">-</span>
                          <span className="font-bold text-accent-orange">{partido.goles_visitante}</span>
                        </div>
                        <div className="flex items-center gap-2 flex-1 min-w-0 text-right">
                          <span className="text-sm text-white truncate">{getNombreEquipo(partido.equipo_visitante_id)}</span>
                          <span className="text-xs text-gray-500">{partido.estado}</span>
                        </div>
                      </div>
                    ))}
                    {(!partidos || partidos.length === 0) && (
                      <p className="text-center text-gray-400 py-4">No hay partidos</p>
                    )}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="bg-dark-card rounded-2xl p-12 border border-dark-border text-center">
              <div className="w-20 h-20 bg-dark-border rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-4xl">🌐</span>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Selecciona una Liga</h3>
              <p className="text-gray-400">Haz clic en una liga para ver sus equipos y partidos</p>
            </div>
          )}
        </div>
      </div>

      <ConfirmDialog
        isOpen={mostrarConfirmImportar}
        onClose={() => { setMostrarConfirmImportar(false); setLigaAImportar(null); }}
        onConfirm={handleImportar}
        title="¿Importar Liga?"
        message={`¿Quieres importar "${ligaAImportar?.name}"? Los datos se guardarán localmente.`}
        confirmText="Importar"
        cancelText="Cancelar"
        type="success"
      />

      {toast && <Toast {...toast} onClose={hideToast} />}
    </div>
  );
}