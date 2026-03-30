from database import (
    get_db,
    LigaRepository,
    TemporadaRepository,
    EquipoRepository,
    PartidoRepository,
    calcular_promedio_goles_por_liga,
    contar_partidos_mas_3_goles,
    contar_partidos_menor_igual_3_goles,
    ranking_ligas_por_promedio_goles,
    obtener_estadisticas_liga,
)


def crear_datos_prueba():
    db = get_db()

    liga_repo = LigaRepository(db)
    temporada_repo = TemporadaRepository(db)
    equipo_repo = EquipoRepository(db)
    partido_repo = PartidoRepository(db)

    cursor = db.get_connection().cursor()
    cursor.execute("DELETE FROM partidos")
    cursor.execute("DELETE FROM equipos")
    cursor.execute("DELETE FROM temporadas")
    cursor.execute("DELETE FROM ligas")
    db.get_connection().commit()

    liga_id = liga_repo.crear("La Liga", "Espana")
    temp_id = temporada_repo.crear("2024-2025", "2024-08-15", "2025-05-30", liga_id)

    equipos = []
    for nombre in ["Real Madrid", "Barcelona", "Atletico Madrid", "Sevilla"]:
        equipos.append(equipo_repo.crear(nombre, liga_id))

    partidos = [
        (equipos[0], equipos[1], 3, 2),
        (equipos[1], equipos[2], 1, 1),
        (equipos[0], equipos[3], 4, 1),
        (equipos[2], equipos[3], 0, 0),
        (equipos[1], equipos[0], 2, 2),
    ]

    for local, visitante, gl, gv in partidos:
        partido_repo.crear(
            fecha="2024-09-01 20:00",
            equipo_local=local,
            equipo_visitante=visitante,
            goles_local=gl,
            goles_visitante=gv,
            arbitro="Arbitro X",
            estadio="Estadio Y",
            temporada_id=temp_id,
        )

    return liga_id


def main():
    print("=== Creando datos de prueba ===")
    liga_id = crear_datos_prueba()

    print(f"\n=== Estadisticas de Liga (ID: {liga_id}) ===")

    promedio = calcular_promedio_goles_por_liga(liga_id)
    print(f"Promedio de goles: {promedio:.2f}")

    mas_3 = contar_partidos_mas_3_goles(liga_id)
    print(f"Partidos con mas de 3 goles: {mas_3}")

    menos_3 = contar_partidos_menor_igual_3_goles(liga_id)
    print(f"Partidos con 3 o menos goles: {menos_3}")

    print("\n=== Ranking de ligas por promedio ===")
    ranking = ranking_ligas_por_promedio_goles()
    for i, liga in enumerate(ranking, 1):
        print(f"{i}. {liga['nombre']} ({liga['pais']}) - Promedio: {liga['promedio_goles']:.2f}")

    print("\n=== Estadisticas completas ===")
    stats = obtener_estadisticas_liga(liga_id)
    print(stats)


if __name__ == "__main__":
    main()
