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

  const requestIdRef = useRef(0);

  useEffect(() => {
    if (!ligaId) return;

    const requestId = ++requestIdRef.current;

    const cargar = async () => {
      console.log("🚀 CARGANDO ESTADISTICAS...");

      const [stats, rank] = await Promise.all([
        obtenerEstadisticasConFiltro(ligaId),
        obtenerRanking()
      ]);

      console.log("📊 STATS:", stats);
      console.log("📊 RANK:", rank);

      setEstadisticas(stats || {});
      setRanking(Array.isArray(rank) ? rank : []);
      setLoading(false);
    };

    cargar();
  }, [ligaId]);

  // 🔥 DEBUG VISUAL
  console.log("🎯 RENDER");
  console.log("datos estadisticas:", estadisticas);

  const datosGoles = [
    {
      name: "Menos de 3",
      value: estadisticas?.partidos_menos_igual_3_goles ?? 0,
    },
    {
      name: "Más de 3",
      value: estadisticas?.partidos_mas_3_goles ?? 0,
    }
  ];

  const datosRanking = (ranking || []).map(l => ({
    nombre: l.nombre,
    promedio: l.promedio_goles
  }));

  console.log("📈 datosGoles:", datosGoles);
  console.log("📈 datosRanking:", datosRanking);

  return (
    <div style={{ padding: 20 }}>

      <h2 style={{ color: "white" }}>DEBUG GRÁFICAS</h2>

      {/* 🔥 DEBUG VISUAL */}
      <pre style={{ color: "lime", fontSize: 12 }}>
        {JSON.stringify({ datosGoles, datosRanking }, null, 2)}
      </pre>

      {/* PIE */}
      <div style={{ width: "100%", height: 300, background: "#111" }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={datosGoles} dataKey="value" fill="#8884d8">
              {datosGoles.map((entry, i) => (
                <Cell key={i} fill={i === 0 ? "#10b981" : "#f59e0b"} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* BAR */}
      <div style={{ width: "100%", height: 300, background: "#222", marginTop: 40 }}>
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
  );
}