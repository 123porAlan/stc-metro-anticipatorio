import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

print("Cargando archivo de paradas (stops.txt)...")
# Cargamos el archivo GTFS de estaciones
# Nota: Los archivos GTFS son básicamente CSVs, así que pandas los lee sin problema
df_stops = pd.read_csv("stops.txt")

print("Creando el grafo espacial...")
# Inicializamos un grafo vacío de NetworkX
G = nx.Graph()

# Diccionario para guardar las coordenadas (longitud, latitud) de cada estación
posiciones = {}

# Iteramos sobre cada fila del archivo para crear los nodos
for index, row in df_stops.iterrows():
    # Usamos stop_id como el ID único del nodo y guardamos su nombre como atributo
    nodo_id = row["stop_id"]
    G.add_node(nodo_id, nombre=row["stop_name"])

    # Guardamos la posición espacial: (X=Longitud, Y=Latitud)
    posiciones[nodo_id] = (row["stop_lon"], row["stop_lat"])

print(f"Total de nodos (estaciones) creados: {G.number_of_nodes()}")

# Dibujamos el grafo
print("Generando mapa de nodos...")
plt.figure(figsize=(10, 10))

# Por ahora solo dibujamos los nodos (puntos), ya que aún no tenemos las aristas (conexiones)
nx.draw_networkx_nodes(G, posiciones, node_size=30, node_color="purple", alpha=0.8)

plt.title("Topología del STC Metro (Nodos Base)", fontsize=16)
plt.xlabel("Longitud", fontsize=12)
plt.ylabel("Latitud", fontsize=12)
plt.grid(True, linestyle="--", alpha=0.5)

# Forzamos los ejes para que muestren las coordenadas reales
plt.axis("on")
plt.tight_layout()

plt.show()
