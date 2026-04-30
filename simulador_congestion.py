import pandas as pd
import networkx as nx
import numpy as np
from datetime import time

print("Cargando infraestructura (Grafo Base)...")
# Cargamos el grafo que construiste en grafo_metro.py
# (Asegúrate de haberlo exportado. Aquí usamos gexf como ejemplo estándar)
G_base = nx.read_gexf("grafo_base_metro.gexf") 

print("Cargando dinámica de pasajeros (Dataset Sintético)...")
df_afluencia = pd.read_csv("datos_procesados/afluencia_sintetica_horaria_avanzada_2026.csv")

def funcion_penalizacion_bpr(tiempo_base_min, afluencia, capacidad_estacion, alpha=0.15, beta=4):
    """
    Calcula el nuevo tiempo de viaje usando la función BPR adaptada para transporte público.
    Simula el tiempo extra de espera, fricción en andenes y cierre de puertas.
    """
    if pd.isna(afluencia) or afluencia == 0:
        return tiempo_base_min
    
    # Relación Volumen/Capacidad (V/C)
    saturacion = afluencia / capacidad_estacion
    
    # Aplicamos la fórmula BPR
    tiempo_congestivo = tiempo_base_min * (1 + alpha * (saturacion ** beta))
    
    # Límite físico: Un tren no puede tardar más del cuádruple del tiempo ideal entre dos estaciones
    tiempo_maximo = tiempo_base_min * 4 
    
    return min(tiempo_congestivo, tiempo_maximo)

print("Iniciando motor de simulación horaria...")

# Supongamos una capacidad base teórica por hora para las estaciones. 
# En tu tesis puedes refinar esto dependiendo de la línea.
CAPACIDAD_PROMEDIO_HORA = 1000

# Diccionario para almacenar los estados de la red en cada hora
grafos_temporales = {}

# Filtramos un día específico para la simulación (Ej. 2026-01-01)
fecha_simulacion = "2026-01-13"
df_dia = df_afluencia[df_afluencia['fecha'] == fecha_simulacion]

# Simulamos desde las 5:00 AM hasta las 11:00 PM (23:00)
horas_operacion = range(5, 24)

for hora in horas_operacion:
    # Creamos una copia del grafo base para esta hora específica
    G_hora = G_base.copy()
    
    # Filtramos la afluencia para esta hora
    df_hora = df_dia[df_dia['hora'] == hora]
    
    # Convertimos a diccionario para búsqueda rápida en O(1)
    afluencia_dict = dict(zip(df_hora['estacion'], df_hora['afluencia_sintetica_hora']))
    
    # Recorremos todas las conexiones (aristas) del grafo
    for u, v, data in G_hora.edges(data=True):
        nombre_origen = G_hora.nodes[u].get('nombre', u)
        
        # Obtenemos la afluencia de la estación de origen en esta hora
        # Si no hay datos, asumimos 0 (sin congestión)
        pasajeros_origen = afluencia_dict.get(nombre_origen, 0)

        # Pon esto temporalmente dentro del loop de aristas:
        if nombre_origen == "Pantitlán" and hora == 7:
            print(f"DEBUG - Pantitlán a las 7 AM: {pasajeros_origen} pasajeros detectados.")
        
        tiempo_ideal = data.get('tiempo_minutos', 2.0) # Tiempo ideal base
        
        # Calculamos el impacto matemático de la congestión
        nuevo_tiempo = funcion_penalizacion_bpr(tiempo_ideal, pasajeros_origen, CAPACIDAD_PROMEDIO_HORA)
        
        # Actualizamos el peso en el grafo dinámico
        G_hora[u][v]['weight'] = round(nuevo_tiempo, 2)
        G_hora[u][v]['congestibilidad'] = round(nuevo_tiempo - tiempo_ideal, 2) # Minutos de retraso
        
    grafos_temporales[hora] = G_hora

print("Simulación completada.")

# --- PRUEBA DEL SIMULADOR ---
# Vamos a comprobar la diferencia entre una hora valle (11 AM) y hora pico (7 AM)
origen_prueba = "Pantitlán"
# Necesitas el ID real del nodo para buscar las aristas. Supongamos que lo encontramos:
nodo_pantitlan = [n for n, d in G_base.nodes(data=True) if d.get('nombre') == origen_prueba][0]

print(f"\nVariación dinámica en {origen_prueba} hacia sus conexiones directas:")

for vecino in G_base.neighbors(nodo_pantitlan):
    nombre_vecino = G_base.nodes[vecino].get('nombre', vecino)
    
    tiempo_base = G_base[nodo_pantitlan][vecino].get('tiempo_minutos')
    tiempo_11am = grafos_temporales[11][nodo_pantitlan][vecino]['weight']
    tiempo_7am = grafos_temporales[7][nodo_pantitlan][vecino]['weight']
    
    print(f"Hacia {nombre_vecino}:")
    print(f"  - Base Ideal:   {tiempo_base} mins")
    print(f"  - Valle (11AM): {tiempo_11am} mins")
    print(f"  - Pico (7AM):   {tiempo_7am} mins")