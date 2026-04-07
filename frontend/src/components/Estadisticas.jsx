import { useEffect } from 'react';
import {
  PieChart, Pie, Cell, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend
} from 'recharts';

export default function Estadisticas({ estadisticasExternas, rankingExterno = [] }) {

  // 🔍 DEBUG 1: ver props
  console.log("🧠 PROPS:");
  console.log("estadisticasExternas:", estadisticasExternas);
  console.log("rankingExterno:", rankingExterno);

  const stats = estadisticasExternas;

  // 🔍 DEBUG 2: mount/unmount
  useEffect(() => {
    console.log("✅ Estadisticas MONTADO");

    return () => {
      console.log("❌ Estadisticas DESMONTADO");
    };
  }, []);

  // 🔍 DEBUG 3: cambios en stats
  useEffect(() => {
    console.log("📊 stats actualizado:", stats);
  }, [stats]);

  // 🚨 DEBUG CRÍTICO
  if (!stats) {
    console.log("⚠️ NO HAY STATS");

    return (
      <div style={{ padding: 20, color: "yellow" }}>
        ⏳ Esperando estadísticas...
      </div>
    );
  }

  // 📊 Datos
  const datosGoles = [
    {
      name: "Menos de 3",
      value: stats.partidos_menos_igual_3_goles || 0,
    },
    {
      name: "Más de 3",
      value: stats.partidos_mas_3_goles || 0,
    }
  ];

  const datosRanking = (rankingExterno || []).map(l => ({
    nombre: l.nombre,
    promedio: l.partidos_jugados > 0
      ? (l.goles_favor / l.partidos_jugados).toFixed(2)
      : 0
  }));

  console.log("📈 datosGoles:", datosGoles);
  console.log("📈 datosRanking:", datosRanking);

  // 🔍 DEBUG 4: validar valores
  if (datosGoles.every(d => d.value === 0)) {
    console.log("⚠️ TODOS LOS VALORES DE GOLES SON 0");
  }

  if (datosRanking.length === 0) {
    console.log("⚠️ RANKING VACÍO");
  }

  return (
    <div style={{ padding: 20, border: "2px solid lime" }}>

      <h2 style={{ color: "lime" }}>🧪 DEBUG GRÁFICAS</h2>

      {/* DEBUG VISUAL */}
      <pre style={{ color: "white", fontSize: 11 }}>
        {JSON.stringify({ datosGoles, datosRanking }, null, 2)}
      </pre>

      {/* ================= PIE ================= */}
      <div style={{
        width: "100%",
        height: 300,
        background: "#111",
        border: "2px solid red"
      }}>
        <p style={{ color: "white" }}>📊 PIE</p>

        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={datosGoles} dataKey="value">
              {datosGoles.map((_, i) => (
                <Cell key={i} fill={i === 0 ? "#10b981" : "#f59e0b"} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* ================= BAR ================= */}
      <div style={{
        width: "100%",
        height: 300,
        background: "#222",
        marginTop: 30,
        border: "2px solid blue"
      }}>
        <p style={{ color: "white" }}>📊 BAR</p>

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