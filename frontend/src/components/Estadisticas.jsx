import { useState, useEffect, useRef } from 'react';
import { obtenerEstadisticasConFiltro, obtenerRanking } from '../api';
import {
  PieChart, Pie, Cell, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend
} from 'recharts';

export default function Estadisticas({ ligaId }) {
  const [estadisticas, setEstadisticas] = useState(null);
  const [ranking, setRanking] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const isMountedRef = useRef(true);
  const requestIdRef = useRef(0);
  const abortControllerRef = useRef(null);

  // 🔒 Control de montaje
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      abortControllerRef.current?.abort();
    };
  }, []);

  // 🚀 Fetch principal
  useEffect(() => {
    if (!ligaId) return;

    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();

    const requestId = ++requestIdRef.current;

    setLoading(true);
    setError(null);

    const cargar = async () => {
      try {
        const [stats, rank] = await Promise.all([
          obtenerEstadisticasConFiltro(ligaId, null, `stats-${ligaId}-${requestId}`),
          obtenerRanking(`ranking-${requestId}`),
        ]);

        if (!isMountedRef.current || requestId !== requestIdRef.current) return;

        console.log("STATS:", stats); // 🔍 debug útil

        setEstadisticas(stats || {});
        setRanking(Array.isArray(rank) ? rank : []);

      } catch (err) {
        if (!isMountedRef.current || requestId !== requestIdRef.current) return;
        if (err?.name === 'AbortError') return;

        setError(err.message || 'Error al cargar estadísticas');
      } finally {
        if (isMountedRef.current && requestId === requestIdRef.current) {
          setLoading(false);
        }
      }
    };

    cargar();
  }, [ligaId]);

  // 🧠 Estado inicial
  const isInitialLoad = loading && estadisticas === null;

  if (isInitialLoad) {
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
        <button
          onClick={() => {
            setError(null);
            setLoading(true);
            setEstadisticas(null);
          }}
          className="bg-accent-blue text-dark-bg px-4 py-2 rounded-lg"
        >
          Reintentar
        </button>
      </div>
    );
  }

  // 📊 Datos seguros
  const umbral = estadisticas?.umbral_goles || 3;

  const datosGoles = [
    {
      name: `≤ ${umbral} goles`,
      value: estadisticas?.partidos_menos_igual_3_goles ?? 0,
      color: '#10b981'
    },
    {
      name: `> ${umbral} goles`,
      value: estadisticas?.partidos_mas_3_goles ?? 0,
      color: '#f59e0b'
    }
  ].filter(d => d.value > 0);

  const datosRanking = (ranking || []).map((liga) => ({
    nombre: (liga.nombre || 'Sin nombre').slice(0, 15),
    promedio: liga.promedio_goles || 0,
  }));

  return (
    <div style={{ position: 'relative', opacity: loading ? 0.6 : 1 }}>

      {/* Spinner overlay */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center z-10">
          <div className="animate-spin rounded-full h-10 w-10 border-4 border-accent-blue border-t-transparent"></div>
        </div>
      )}

      <h3 className="text-2xl font-bold text-white mb-6">Estadísticas</h3>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card title="Total Partidos" value={estadisticas?.total_partidos || 0} />
        <Card title="Promedio Goles" value={(estadisticas?.promedio_goles || 0).toFixed(2)} />
        <Card title={`Partidos >${umbral}`} value={estadisticas?.partidos_mas_3_goles || 0} />
        <Card title={`Partidos ≤${umbral}`} value={estadisticas?.partidos_menos_igual_3_goles || 0} />
      </div>

      {/* GRÁFICAS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* PIE */}
        <div className="bg-dark-card p-6 rounded-2xl">
          <h4 className="text-white mb-4">Distribución de Goles</h4>

          <div className="h-64">
            {datosGoles.length === 0 ? (
              <div className="text-gray-400 text-center py-10">
                No hay datos
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={datosGoles} dataKey="value">
                    {datosGoles.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* BAR */}
        <div className="bg-dark-card p-6 rounded-2xl">
          <h4 className="text-white mb-4">Ranking</h4>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={datosRanking}>
                <XAxis dataKey="nombre" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="promedio" fill="#38bdf8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

// 🔥 componente reutilizable
function Card({ title, value }) {
  return (
    <div className="bg-dark-card p-5 rounded-xl">
      <p className="text-gray-400 text-sm">{title}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}