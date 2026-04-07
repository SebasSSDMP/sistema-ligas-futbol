import {
  PieChart, Pie, Cell, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend
} from 'recharts';

export default function Estadisticas({ estadisticasExternas, rankingExterno = [] }) {

  // 🔥 Fuente única de datos (sin estados internos)
  const stats = estadisticasExternas;

  // 🚫 Evitar render vacío
  if (!stats) {
    return (
      <div style={{ padding: 20 }}>
        <p style={{ color: "white" }}>Cargando gráficas...</p>
      </div>
    );
  }

  // 📊 Datos para gráfica de goles
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

  // 📊 Datos para gráfica de ranking
  const datosRanking = (rankingExterno || []).map(l => ({
    nombre: l.nombre,
    promedio: Number(l.promedio_goles || 0)
  }));

  // 🎨 Colores
  const COLORS = ["#10b981", "#f59e0b"];

  return (
    <div style={{ padding: 20 }}>

      {/* ===================== */}
      {/* 📊 GRÁFICA PIE */}
      {/* ===================== */}
      <div style={{
        width: "100%",
        height: 300,
        background: "#111",
        borderRadius: 12,
        padding: 10
      }}>
        <h3 style={{ color: "white", marginBottom: 10 }}>
          Distribución de Goles
        </h3>

        <ResponsiveContainer width="100%" height="85%">
          <PieChart>
            <Pie
              data={datosGoles}
              dataKey="value"
              nameKey="name"
              outerRadius={100}
              label
            >
              {datosGoles.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* ===================== */}
      {/* 📊 GRÁFICA BAR */}
      {/* ===================== */}
      <div style={{
        width: "100%",
        height: 320,
        background: "#222",
        marginTop: 40,
        borderRadius: 12,
        padding: 10
      }}>
        <h3 style={{ color: "white", marginBottom: 10 }}>
          Promedio de Goles por Liga
        </h3>

        <ResponsiveContainer width="100%" height="85%">
          <BarChart data={datosRanking}>
            <XAxis dataKey="nombre" stroke="#ccc" />
            <YAxis stroke="#ccc" />
            <Tooltip />
            <Legend />
            <Bar dataKey="promedio" fill="#38bdf8" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

    </div>
  );
}