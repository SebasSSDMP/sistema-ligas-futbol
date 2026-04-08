# Sistema de Gestion de Ligas de Futbol

Aplicacion de escritorio para la gestion de ligas de futbol, equipos, temporadas, partidos y estadisticas.

## Requisitos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)

## Instalacion

1. Clonar o descargar el proyecto

2. Instalar las dependencias:
```bash
pip install -r backend/requirements.txt
pip install customtkinter
```

3. Ejecutar la aplicacion:

**Windows:**
```bash
python main.py
```
O simplemente haz doble clic en `run.bat`

**Linux/Mac:**
```bash
python main.py
```
O ejecuta `./run.sh` (primero dale permisos: `chmod +x run.sh`)

## Caracteristicas

- Gestion de ligas de futbol
- Gestion de equipos y temporadas
- Registro de partidos con resultados
- Estadisticas y rankings
- Importacion de datos desde football-data.org (opcional)

## Datos

La aplicacion utiliza SQLite y guarda todos los datos en el archivo `data/futbol.db`.
No requiere ninguna configuracion adicional ni servicios externos.

## Notas

- La base de datos se crea automaticamente al iniciar la aplicacion
- Todos los datos se guardan localmente en el archivo `data/futbol.db`
- No se requiere conexion a internet para el funcionamiento basico
- Para importar datos de football-data.org, se necesita una API key gratuita en https://www.football-data.org/
