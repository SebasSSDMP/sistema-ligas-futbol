import { startGlobalLoading, stopGlobalLoading, setGlobalError, clearGlobalError } from './utils/apiState';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003';
const MAX_RETRIES = 1;
const RETRY_DELAY = 1000;
const REQUEST_TIMEOUT = 10000;


class RequestManager {
  constructor() {
    this.controllers = new Map();
    this.pendingRequests = new Set();
    // Cache for deduplication: {url: {promise, timestamp}}
    this.requestCache = new Map();
    this.CACHE_DURATION_MS = 5000; // 5 seconds cache for identical requests
  }

  generateRequestId(endpoint) {
    return `${endpoint}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  cancelRequest(requestId) {
    const controller = this.controllers.get(requestId);
    if (controller) {
      controller.abort();
      this.controllers.delete(requestId);
      this.pendingRequests.delete(requestId);
    }
  }

  cancelAllRequests() {
    this.controllers.forEach((controller) => controller.abort());
    this.controllers.clear();
    this.pendingRequests.clear();
  }

    async request(url, options = {}, requestId = null) {
        // Check cache for duplicate requests (same URL and method)
        const cacheKey = `${url}:${options.method || 'GET'}`;
        const cached = this.requestCache.get(cacheKey);
        if (cached && (Date.now() - cached.timestamp < this.CACHE_DURATION_MS)) {
            console.log(`[API] Returning cached response for ${url}`);
            return cached.promise;
        }

        const controller = new AbortController();
        const id = requestId || this.generateRequestId(url);
        this.controllers.set(id, controller);
        this.pendingRequests.add(id);

        // Set up timeout
        const timeoutId = setTimeout(() => {
            controller.abort();
        }, REQUEST_TIMEOUT);

        let lastError = null;

        try {
            // Start global loading indicator
            startGlobalLoading();
            clearGlobalError();

            for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
                if (attempt > 0) {
                    await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY));
                    console.log(`[API] Retry attempt ${attempt} for ${url}`);
                }

                try {
                    console.log(`[API] Request ${attempt === 0 ? 'started' : 'retry'}: ${url}`);

                    const response = await fetch(url, {
                        ...options,
                        signal: controller.signal,
                        headers: {
                            'Content-Type': 'application/json',
                            ...options.headers,
                        },
                    });

                    if (!response.ok) {
                        let errorDetail = `HTTP ${response.status}`;
                        try {
                            const errorData = await response.json();
                            errorDetail = errorData.detail || errorDetail;
                        } catch {
                            // ignore JSON parse errors
                        }
                        throw new Error(errorDetail);
                    }

                    const text = await response.text();
                    const data = text ? JSON.parse(text) : null;

                    console.log(`[API] Success: ${url}`, data ? `(${Array.isArray(data) ? data.length + ' items' : 'object'})` : '(empty)');

                    // Cache successful response
                    const cachePromise = Promise.resolve(data);
                    this.requestCache.set(cacheKey, {
                        promise: cachePromise,
                        timestamp: Date.now()
                    });

                    // Clean old cache entries
                    this._cleanCache();

                    this.controllers.delete(id);
                    this.pendingRequests.delete(id);
                    clearTimeout(timeoutId);
                    stopGlobalLoading();

                    return data;
                } catch (error) {
                    lastError = error;

                    if (error.name === 'AbortError') {
                        console.log(`[API] Aborted: ${url}`);
                        return null;
                    }

                    console.error(`[API] Error${attempt < MAX_RETRIES ? ' (will retry)' : ''}: ${url}`, error.message);

                    if (attempt === MAX_RETRIES) {
                        break;
                    }
                }
            }
        } finally {
            this.controllers.delete(id);
            this.pendingRequests.delete(id);
            clearTimeout(timeoutId);
            stopGlobalLoading();
        }

        // Set global error if we have one
        if (lastError) {
            setGlobalError(lastError.message);
        }

        throw lastError;
    }

    _cleanCache() {
        const now = Date.now();
        for (const [key, value] of this.requestCache.entries()) {
            if (now - value.timestamp > this.CACHE_DURATION_MS * 2) {
                this.requestCache.delete(key);
            }
        }
    }
}

const requestManager = new RequestManager();

// LIGAS
export async function obtenerLigas(requestId = null) {
  const id = requestId || `ligas-${Date.now()}`;
  requestManager.cancelRequest(id);
  return requestManager.request(`${API_URL}/ligas`, {}, id);
}

export async function crearLiga(data) {
  console.log('[API] Creating liga:', data);
  return requestManager.request(`${API_URL}/ligas`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function actualizarLiga(id, data) {
  console.log('[API] Updating liga:', id, data);
  return requestManager.request(`${API_URL}/ligas/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function eliminarLiga(id) {
  console.log('[API] Deleting liga:', id);
  return requestManager.request(`${API_URL}/ligas/${id}`, {
    method: 'DELETE',
  });
}

// TEMPORADAS
export async function obtenerTemporadas(ligaId, requestId = null) {
  if (!ligaId) {
    console.log('[API] Skipping obtenerTemporadas: no ligaId');
    return [];
  }
  const id = requestId || `temp-${ligaId}-${Date.now()}`;
  requestManager.cancelRequest(id);
  console.log('[API] Fetching temporadas for liga:', ligaId);
  return requestManager.request(`${API_URL}/ligas/${ligaId}/temporadas`, {}, id);
}

export async function crearTemporada(data) {
  console.log('[API] Creating temporada:', data);
  return requestManager.request(`${API_URL}/temporadas`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// EQUIPOS
export async function obtenerEquipos(ligaId, requestId = null) {
  if (!ligaId) {
    console.log('[API] Skipping obtenerEquipos: no ligaId');
    return [];
  }
  const id = requestId || `equipos-${ligaId}-${Date.now()}`;
  requestManager.cancelRequest(id);
  console.log('[API] Fetching equipos for liga:', ligaId);
  return requestManager.request(`${API_URL}/ligas/${ligaId}/equipos`, {}, id);
}

export async function crearEquipo(data) {
  console.log('[API] Creating equipo:', data);
  return requestManager.request(`${API_URL}/equipos`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function actualizarEquipo(id, data) {
  console.log('[API] Updating equipo:', id, data);
  return requestManager.request(`${API_URL}/equipos/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function eliminarEquipo(id) {
  console.log('[API] Deleting equipo:', id);
  return requestManager.request(`${API_URL}/equipos/${id}`, {
    method: 'DELETE',
  });
}

// PARTIDOS
export async function obtenerPartidos(temporadaId, requestId = null) {
  if (!temporadaId) {
    console.log('[API] Skipping obtenerPartidos: no temporadaId');
    return [];
  }
  const id = requestId || `partidos-${temporadaId}-${Date.now()}`;
  requestManager.cancelRequest(id);
  console.log('[API] Fetching partidos for temporada:', temporadaId);
  return requestManager.request(`${API_URL}/temporadas/${temporadaId}/partidos`, {}, id);
}

export async function crearPartido(data) {
  console.log('[API] Creating partido:', data);
  return requestManager.request(`${API_URL}/partidos`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function actualizarPartido(id, data) {
  console.log('[API] Updating partido:', id, data);
  return requestManager.request(`${API_URL}/partidos/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

// ESTADISTICAS
export async function obtenerEstadisticas(ligaId, requestId = null) {
  if (!ligaId) {
    console.log('[API] Skipping obtenerEstadisticas: no ligaId');
    return {};
  }
  const id = requestId || `stats-${ligaId}-${Date.now()}`;
  requestManager.cancelRequest(id);
  console.log('[API] Fetching estadisticas for liga:', ligaId);
  const result = await requestManager.request(`${API_URL}/ligas/${ligaId}/estadisticas`, {}, id);
  return result || {};
}

export async function obtenerRanking(requestId = null) {
  const id = requestId || `ranking-${Date.now()}`;
  requestManager.cancelRequest(id);
  console.log('[API] Fetching ranking');
  const result = await requestManager.request(`${API_URL}/ranking`, {}, id);
  return Array.isArray(result) ? result : [];
}

// RESET
export async function resetDatabase() {
  console.log('[API] Resetting database');
  return requestManager.request(`${API_URL}/reset-db`, {
    method: 'POST',
  });
}

// EXTERNAL API (API-Football with caching)
export async function obtenerLigasExternas(forceRefresh = false, requestId = null) {
  const id = requestId || `external-ligas-${Date.now()}`;
  requestManager.cancelRequest(id);
  console.log('[API] Fetching external ligas, forceRefresh:', forceRefresh);
  const result = await requestManager.request(
    `${API_URL}/external/ligas?force_refresh=${forceRefresh}`,
    {},
    id
  );
  return Array.isArray(result) ? result : [];
}

export async function obtenerEquiposExternos(ligaId, forceRefresh = false, requestId = null) {
  if (!ligaId) {
    console.log('[API] Skipping obtenerEquiposExternos: no ligaId');
    return [];
  }
  const id = requestId || `external-equipos-${ligaId}-${Date.now()}`;
  requestManager.cancelRequest(id);
  console.log('[API] Fetching external equipos for liga:', ligaId);
  const result = await requestManager.request(
    `${API_URL}/external/equipos/${ligaId}?force_refresh=${forceRefresh}`,
    {},
    id
  );
  return Array.isArray(result) ? result : [];
}

export async function obtenerPartidosExternos(ligaId, temporada = 2024, forceRefresh = false, requestId = null) {
  if (!ligaId) {
    console.log('[API] Skipping obtenerPartidosExternos: no ligaId');
    return [];
  }
  const id = requestId || `external-partidos-${ligaId}-${temporada}-${Date.now()}`;
  requestManager.cancelRequest(id);
  console.log('[API] Fetching external partidos for liga:', ligaId, 'temporada:', temporada);
  const result = await requestManager.request(
    `${API_URL}/external/partidos/${ligaId}?temporada=${temporada}&force_refresh=${forceRefresh}`,
    {},
    id
  );
  return Array.isArray(result) ? result : [];
}

export async function obtenerEstadoCache(requestId = null) {
  const id = requestId || `cache-status-${Date.now()}`;
  requestManager.cancelRequest(id);
  console.log('[API] Fetching cache status');
  const result = await requestManager.request(`${API_URL}/external/cache-status`, {}, id);
  return result || {};
}

export async function limpiarCache(tipo = null, requestId = null) {
  const id = requestId || `cache-clear-${Date.now()}`;
  requestManager.cancelRequest(id);
  const url = tipo
    ? `${API_URL}/external/cache/clear?tipo=${tipo}`
    : `${API_URL}/external/cache/clear`;
  console.log('[API] Clearing cache, tipo:', tipo);
  return requestManager.request(url, { method: 'POST' }, id);
}

export async function importarLiga(ligaId, requestId = null) {
  if (!ligaId) {
    console.log('[API] Skipping importarLiga: no ligaId');
    return null;
  }
  const id = requestId || `import-${ligaId}-${Date.now()}`;
  requestManager.cancelRequest(id);
  console.log('[API] Importing liga:', ligaId);
  const result = await requestManager.request(`${API_URL}/importar-liga/${ligaId}`, { method: 'POST' }, id);
  return result;
}

export async function actualizarLigaEx(ligaId, temporada = 2024, requestId = null) {
  if (!ligaId) {
    console.log('[API] Skipping actualizarLigaEx: no ligaId');
    return null;
  }
  const id = requestId || `update-${ligaId}-${Date.now()}`;
  requestManager.cancelRequest(id);
  console.log('[API] Updating liga external:', ligaId);
  const result = await requestManager.request(
    `${API_URL}/actualizar-liga/${ligaId}?temporada=${temporada}`,
    { method: 'POST' },
    id
  );
  return result;
}

export function cancelAllRequests() {
  requestManager.cancelAllRequests();
}

// REQ 3: Ranking por liga
export async function obtenerRankingLiga(ligaId, requestId = null) {
  if (!ligaId) return [];
  const id = requestId || `ranking-liga-${ligaId}-${Date.now()}`;
  requestManager.cancelRequest(id);
  const result = await requestManager.request(`${API_URL}/ligas/${ligaId}/ranking`, {}, id);
  return Array.isArray(result) ? result : [];
}

// REQ 4: Estadísticas filtradas por temporada
export async function obtenerEstadisticasConFiltro(ligaId, temporadaId = null, requestId = null) {
  if (!ligaId) return {};
  const id = requestId || `stats-filtro-${ligaId}-${temporadaId}-${Date.now()}`;
  requestManager.cancelRequest(id);
  const url = temporadaId
    ? `${API_URL}/ligas/${ligaId}/estadisticas?temporada_id=${temporadaId}`
    : `${API_URL}/ligas/${ligaId}/estadisticas`;
  const result = await requestManager.request(url, {}, id);
  return result || {};
}

// REQ 5: Equipos por temporada
export async function obtenerEquiposTemporada(temporadaId, requestId = null) {
  if (!temporadaId) return [];
  const id = requestId || `equipos-temp-${temporadaId}-${Date.now()}`;
  requestManager.cancelRequest(id);
  const result = await requestManager.request(`${API_URL}/temporadas/${temporadaId}/equipos`, {}, id);
  return Array.isArray(result) ? result : [];
}

export async function asociarEquipoTemporada(temporadaId, equipoId) {
  return requestManager.request(`${API_URL}/temporadas/${temporadaId}/equipos/${equipoId}`, {
    method: 'POST',
  });
}

export async function desasociarEquipoTemporada(temporadaId, equipoId) {
  return requestManager.request(`${API_URL}/temporadas/${temporadaId}/equipos/${equipoId}`, {
    method: 'DELETE',
  });
}