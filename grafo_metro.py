import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

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

# 3. Construcción de las Aristas (Conexiones)
print("Calculando conexiones entre estaciones...")
# Ordenamos por viaje y por secuencia de parada para asegurar el orden cronológico
df_stop_times_metro = df_stop_times_metro.sort_values(by=["trip_id", "stop_sequence"])

# Agrupamos por viaje y conectamos las estaciones consecutivas
for trip_id, group in df_stop_times_metro.groupby("trip_id"):
    secuencia_paradas = group["stop_id"].tolist()
    # Conectamos la parada actual con la siguiente
    for i in range(len(secuencia_paradas) - 1):
        origen = secuencia_paradas[i]
        destino = secuencia_paradas[i + 1]
        G_metro.add_edge(origen, destino)

print(f"Aristas (Conexiones) creadas: {G_metro.number_of_edges()}")

# 4. Dibujar el Grafo Completo
print("Generando mapa topológico completo...")
plt.figure(figsize=(12, 12))

# Dibujamos nodos
nx.draw_networkx_nodes(
    G_metro,
    posiciones,
    node_size=30,
    node_color="orange",
    edgecolors="black",
    alpha=0.9,
)
# Dibujamos aristas
nx.draw_networkx_edges(G_metro, posiciones, edge_color="gray", width=1.5, alpha=0.6)

plt.title("Topología de Red del STC Metro (Nodos y Aristas)", fontsize=16)
plt.xlabel("Longitud", fontsize=12)
plt.ylabel("Latitud", fontsize=12)
plt.grid(True, linestyle="--", alpha=0.5)
plt.axis("on")
plt.tight_layout()

plt.show()
