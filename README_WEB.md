# Sistema de Gestión de Ligas de Fútbol - Web

Aplicación web profesional con FastAPI (backend) y React + TailwindCSS (frontend).

## Estructura del Proyecto

```
statsbr/
├── backend/               # API FastAPI
│   ├── main.py           # Endpoints REST
│   ├── models.py         # Modelos Pydantic
│   └── requirements.txt  # Dependencias Python
├── frontend/             # Aplicación React
│   ├── src/
│   │   ├── api.js       # Llamadas a la API
│   │   ├── App.jsx      # Componente principal
│   │   └── components/  # Componentes React
│   ├── index.html
│   └── package.json
├── data/                 # Base de datos SQLite
└── README.md
```

## Requisitos Previos

- Python 3.9+
- Node.js 18+
- npm o yarn

## Instalación y Ejecución

### 1. Backend (FastAPI)

```bash
cd backend

# Crear entorno virtual (opcional pero recomendado)
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python main.py
```

El backend estará disponible en: http://localhost:8000
- Documentación API: http://localhost:8000/docs

### 2. Frontend (React)

```bash
cd frontend

# Instalar dependencias
npm install

# Ejecutar aplicación
npm run dev
```

El frontend estará disponible en: http://localhost:3000

### 3. Base de Datos

La base de datos SQLite ya existe en `data/futbol.db`. 
Se creará automáticamente si no existe.

## Endpoints de la API

### Ligas
- `GET /ligas` - Listar todas las ligas
- `POST /ligas` - Crear nueva liga
- `DELETE /ligas/{id}` - Eliminar liga

### Temporadas
- `GET /ligas/{liga_id}/temporadas` - Listar temporadas de una liga
- `POST /temporadas` - Crear temporada

### Equipos
- `GET /ligas/{liga_id}/equipos` - Listar equipos de una liga
- `POST /equipos` - Crear equipo

### Partidos
- `GET /temporadas/{temporada_id}/partidos` - Listar partidos
- `POST /partidos` - Crear partido

### Estadísticas
- `GET /ligas/{liga_id}/estadisticas` - Estadísticas de una liga
- `GET /ranking` - Ranking de ligas por promedio de goles

## Tecnologías

### Backend
- FastAPI - Framework web moderno
- Pydantic - Validación de datos
- SQLite - Base de datos

### Frontend
- React 18 - Biblioteca de UI
- Vite - Build tool
- TailwindCSS - Framework de estilos
- Recharts - Gráficos y visualizaciones

## Diseño

- Tema oscuro con colores:
  - Fondo: `#0f172a`
  - Tarjetas: `#1e293b`
  - Verde (acciones positivas): `#10b981`
  - Naranja (acciones importantes): `#f59e0b`
  - Azul claro (estadísticas): `#38bdf8`
  - Púrpura (acentos): `#a855f7`

## Scripts Disponibles

### Backend
```bash
python main.py  # Iniciar servidor
```

### Frontend
```bash
npm run dev     # Desarrollo (http://localhost:3000)
npm run build   # Build de producción
npm run preview # Vista previa del build
```
