import { useState, useEffect, useCallback, useRef } from 'react';
import { obtenerEstadisticas, obtenerRanking, cancelAllRequests } from '../api';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';

export default function Estadisticas({ ligaId }) {
  const [estadisticas, setEstadisticas] = useState(null);
  const [ranking, setRanking] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const isMountedRef = useRef(true);
  const requestIdRef = useRef(0);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      cancelAllRequests();
    };
  }, []);

  const cargarDatos = useCallback(async () => {
    if (!ligaId || !isMountedRef.current) return;

    const requestId = ++requestIdRef.current;
    console.log(`[Estadisticas] Cargando datos, requestId: ${requestId}`);

    setLoading(true);
    setError(null);

    try {
      const [stats, rank] = await Promise.all([
        obtenerEstadisticas(ligaId, `stats-${ligaId}-${requestId}`),
        obtenerRanking(`ranking-${requestId}`),
      ]);

      if (!isMountedRef.current || requestId !== requestIdRef.current) return;

      setEstadisticas(stats || {});
      setRanking(Array.isArray(rank) ? rank : []);
      console.log(`[Estadisticas] Datos cargados`);
    } catch (err) {
      if (!isMountedRef.current || requestId !== requestIdRef.current) return;
      console.error(`[Estadisticas] Error:`, err);
      setError(err.message || 'Error al cargar estadísticas');
    } finally {
      if (isMountedRef.current && requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }, [ligaId]);

  useEffect(() => {
    cargarDatos();
  }, [ligaId]);

  if (loading && !error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-accent-blue border-t-transparent"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-400 mb-4">{error}</p>
        <button onClick={cargarDatos} className="bg-accent-blue text-dark-bg px-4 py-2 rounded-lg">
          Reintentar
        </button>
      </div>
    );
  }

  const datosGoles = estadisticas
    ? [
        { name: '≤ 3 goles', value: estadisticas.partidos_menos_igual_3_goles || 0, color: '#10b981' },
        { name: '> 3 goles', value: estadisticas.partidos_mas_3_goles || 0, color: '#f59e0b' },
      ]
    : [];

  const datosRanking = (ranking || []).map((liga) => ({
    nombre: (liga.nombre || 'Sin nombre').length > 15
      ? (liga.nombre || 'Sin nombre').substring(0, 15) + '...'
      : (liga.nombre || 'Sin nombre'),
    promedio: liga.promedio_goles || 0,
    partidos: liga.total_partidos || 0,
    highlight: liga.id === ligaId,
  }));

  return (
    <div>
      <h3 className="text-2xl font-bold text-white mb-6">Estadísticas</h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-dark-card rounded-xl p-5 border border-dark-border">
          <p className="text-gray-400 text-sm mb-1">Total Partidos</p>
          <p className="text-3xl font-bold text-accent-blue">{estadisticas?.total_partidos || 0}</p>
        </div>
        <div className="bg-dark-card rounded-xl p-5 border border-dark-border">
          <p className="text-gray-400 text-sm mb-1">Promedio Goles</p>
          <p className="text-3xl font-bold text-accent-green">
            {(estadisticas?.promedio_goles || 0).toFixed(2)}
          </p>
        </div>
        <div className="bg-dark-card rounded-xl p-5 border border-dark-border">
          <p className="text-gray-400 text-sm mb-1">Partidos &gt;3 goles</p>
          <p className="text-3xl font-bold text-accent-orange">{estadisticas?.partidos_mas_3_goles || 0}</p>
        </div>
        <div className="bg-dark-card rounded-xl p-5 border border-dark-border">
          <p className="text-gray-400 text-sm mb-1">Partidos ≤3 goles</p>
          <p className="text-3xl font-bold text-accent-purple">
            {estadisticas?.partidos_menos_igual_3_goles || 0}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-dark-card rounded-2xl p-6 border border-dark-border">
          <h4 className="text-lg font-semibold text-white mb-4">Distribución de Goles</h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={datosGoles}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {datosGoles.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-dark-card rounded-2xl p-6 border border-dark-border">
          <h4 className="text-lg font-semibold text-white mb-4">Ranking por Promedio de Goles</h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={datosRanking} layout="vertical">
                <XAxis type="number" stroke="#64748b" />
                <YAxis
                  type="category"
                  dataKey="nombre"
                  stroke="#64748b"
                  width={100}
                  tick={{ fill: '#fff', fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Bar dataKey="promedio" fill="#38bdf8" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="mt-6 bg-dark-card rounded-2xl p-6 border border-dark-border">
        <h4 className="text-lg font-semibold text-white mb-4">Resumen de Ranking</h4>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-gray-400 text-sm border-b border-dark-border">
                <th className="text-left py-3 px-4">#</th>
                <th className="text-left py-3 px-4">Liga</th>
                <th className="text-left py-3 px-4">País</th>
                <th className="text-right py-3 px-4">Partidos</th>
                <th className="text-right py-3 px-4">Promedio</th>
              </tr>
            </thead>
            <tbody>
              {(ranking || []).map((liga, index) => (
                <tr
                  key={liga.id || index}
                  className={`border-b border-dark-border ${liga.id === ligaId ? 'bg-accent-blue/10' : ''}`}
                >
                  <td className="py-3 px-4">
                    <span
                      className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                        index === 0
                          ? 'bg-yellow-500 text-dark-bg'
                          : index === 1
                          ? 'bg-gray-400 text-dark-bg'
                          : index === 2
                          ? 'bg-amber-700 text-white'
                          : 'bg-dark-border text-gray-400'
                      }`}
                    >
                      {index + 1}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-semibold text-white">{liga.nombre || 'Sin nombre'}</td>
                  <td className="py-3 px-4 text-gray-400">{liga.pais || 'N/A'}</td>
                  <td className="py-3 px-4 text-right text-gray-400">{liga.total_partidos || 0}</td>
                  <td className="py-3 px-4 text-right">
                    <span className={`font-bold ${liga.id === ligaId ? 'text-accent-blue' : 'text-gray-300'}`}>
                      {liga.promedio_goles ? liga.promedio_goles.toFixed(2) : '0.00'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
