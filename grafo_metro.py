import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt


def gtfs_time_to_seconds(time_str):
    """Convierte el formato HH:MM:SS de GTFS a segundos totales, soportando > 24h."""
    if pd.isna(time_str):
        return None
    h, m, s = map(int, str(time_str).split(":"))
    return h * 3600 + m * 60 + s


print("Cargando y filtrando datos GTFS del Metro...")

# 1. Filtros base (nuestra llave maestra)
df_routes = pd.read_csv("routes.txt", encoding="utf-8-sig", low_memory=False)
rutas_metro = df_routes[df_routes["agency_id"] == "METRO"]["route_id"].unique()

df_trips = pd.read_csv("trips.txt", encoding="utf-8-sig", low_memory=False)
viajes_metro = df_trips[df_trips["route_id"].isin(rutas_metro)]["trip_id"].unique()

df_stop_times = pd.read_csv("stop_times.txt", encoding="utf-8-sig", low_memory=False)
# Filtramos solo los tiempos de parada que pertenecen al Metro
df_stop_times_metro = df_stop_times[df_stop_times["trip_id"].isin(viajes_metro)].copy()

df_stops = pd.read_csv("stops.txt", encoding="utf-8-sig", low_memory=False)
estaciones_metro = df_stops[
    df_stops["stop_id"].isin(df_stop_times_metro["stop_id"].unique())
]

# 2. Construcción del Grafo (Nodos)
G_metro = nx.Graph()
posiciones = {}

for index, row in estaciones_metro.iterrows():
    nodo_id = row["stop_id"]
    G_metro.add_node(nodo_id, nombre=row["stop_name"])
    posiciones[nodo_id] = (row["stop_lon"], row["stop_lat"])

print(f"Nodos (Estaciones) creados: {G_metro.number_of_nodes()}")

# 3. Construcción de Aristas y Cálculo de Pesos (Tiempos de Viaje)
print("Calculando conexiones y tiempos de viaje estáticos...")

# Convertimos los tiempos a segundos
df_stop_times_metro["arrival_sec"] = df_stop_times_metro["arrival_time"].apply(
    gtfs_time_to_seconds
)
df_stop_times_metro["departure_sec"] = df_stop_times_metro["departure_time"].apply(
    gtfs_time_to_seconds
)

# Ordenamos estrictamente por viaje y secuencia de parada
df_stop_times_metro = df_stop_times_metro.sort_values(by=["trip_id", "stop_sequence"])

tiempos_tramos = {}

# Agrupamos por viaje y procesamos las paradas consecutivas
for trip_id, group in df_stop_times_metro.groupby("trip_id"):
    paradas = group.to_dict("records")

    for i in range(len(paradas) - 1):
        origen = paradas[i]["stop_id"]
        destino = paradas[i + 1]["stop_id"]

        # Conectamos la parada actual con la siguiente (si no existe la arista, se crea)
        if not G_metro.has_edge(origen, destino):
            G_metro.add_edge(origen, destino)

        tiempo_salida = paradas[i]["departure_sec"]
        tiempo_llegada = paradas[i + 1]["arrival_sec"]

        if tiempo_salida is not None and tiempo_llegada is not None:
            delta_segundos = tiempo_llegada - tiempo_salida

            # Filtramos deltas ilógicos (menores a 0 o mayores a 30 mins entre dos estaciones)
            if 0 < delta_segundos < 1800:
                tramo = tuple(
                    sorted((origen, destino))
                )  # Usamos sorted para grafos no dirigidos
                if tramo not in tiempos_tramos:
                    tiempos_tramos[tramo] = []
                tiempos_tramos[tramo].append(delta_segundos)

# Promediamos los tiempos y los asignamos como peso definitivo a las aristas
for (nodo1, nodo2), tiempos in tiempos_tramos.items():
    if G_metro.has_edge(nodo1, nodo2):
        tiempo_promedio_segundos = sum(tiempos) / len(tiempos)
        G_metro[nodo1][nodo2]["weight"] = round(tiempo_promedio_segundos, 2)
        G_metro[nodo1][nodo2]["tiempo_minutos"] = round(
            tiempo_promedio_segundos / 60, 2
        )

print(f"Aristas (Conexiones) creadas y pesadas: {G_metro.number_of_edges()}")

# Para verificar que funcionó, imprimimos una muestra de las aristas con sus pesos
print("\nMuestra de conexiones y tiempos base (sin congestión):")
for idx, (u, v, data) in enumerate(G_metro.edges(data=True)):
    nombre_u = G_metro.nodes[u]["nombre"]
    nombre_v = G_metro.nodes[v]["nombre"]
    minutos = data.get("tiempo_minutos", "Desconocido")
    print(f"- De {nombre_u} a {nombre_v}: {minutos} mins")
    if idx >= 4:  # Mostramos solo las primeras 5
        break
print()

# 4. Dibujar el Grafo Completo
print("Generando mapa topológico completo...")
plt.figure(figsize=(12, 12))

nx.draw_networkx_nodes(
    G_metro,
    posiciones,
    node_size=30,
    node_color="orange",
    edgecolors="black",
    alpha=0.9,
)
nx.draw_networkx_edges(G_metro, posiciones, edge_color="gray", width=1.5, alpha=0.6)

plt.title("Topología de Red del STC Metro (Nodos y Aristas con Pesos)", fontsize=16)
plt.xlabel("Longitud", fontsize=12)
plt.ylabel("Latitud", fontsize=12)
plt.grid(True, linestyle="--", alpha=0.5)
plt.axis("on")
plt.tight_layout()

plt.show()
