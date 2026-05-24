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
CAPACIDAD_PROMEDIO_HORA = 25000

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


        # --- SIMULACIÓN DE DISRUPCIÓN PARA LA TESIS ---
        # Si es de 7 a 9 AM, simulamos que la Línea 9 (Puebla, Velódromo, etc.) sufre una falla de trenes
        if 7 <= hora <= 9 and "B_0200L9" in u:
            pasajeros_origen += 40000 # Inyectamos un colapso masivo solo en esta línea

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


# --- Lo siguiente es mi data pipeline ---

print("\nExtrayendo características tabulares para Machine Learning...")

datos_ml = []
horas_disponibles = sorted(list(grafos_temporales.keys()))

# Recorremos cada hora simulada
for i, hora_actual in enumerate(horas_disponibles):
    
    # Para predecir (target), necesitamos la hora siguiente. 
    # Si no hay hora siguiente (ej. a las 23:00), no podemos crear target, así que la saltamos.
    if i + 1 >= len(horas_disponibles):
        continue
        
    # Para tener 'lags' (memoria pasada), necesitamos al menos 1 hora anterior.
    # Si es la primera hora del día (5:00), la saltamos porque no tenemos datos de las 4:00.
    if i < 1:
        continue
        
    hora_siguiente = horas_disponibles[i + 1]
    hora_pasada = horas_disponibles[i - 1]
    
    G_actual = grafos_temporales[hora_actual]
    G_pasado = grafos_temporales[hora_pasada]
    G_siguiente = grafos_temporales[hora_siguiente]
    
    # Recorremos cada tramo (arista) de la red
    for u, v, data in G_actual.edges(data=True):
        nombre_origen = G_actual.nodes[u].get('nombre', str(u))
        nombre_destino = G_actual.nodes[v].get('nombre', str(v))
        tramo_id = f"{nombre_origen}-{nombre_destino}"
        
        tiempo_ideal = data.get('tiempo_minutos', 0)
        
        # Extraemos el retraso (congestibilidad) en t (presente)
        congest_actual = data.get('congestibilidad', 0)
        
        # Extraemos el retraso en t-1 (pasado)
        congest_pasada = G_pasado[u][v].get('congestibilidad', 0) if G_pasado.has_edge(u, v) else 0
        
        # Extraemos el retraso en t+1 (FUTURO / TARGET)
        congest_futura = G_siguiente[u][v].get('congestibilidad', 0) if G_siguiente.has_edge(u, v) else 0
        
        # Guardamos la fila tabular
        datos_ml.append({
            'fecha': fecha_simulacion,
            'hora': hora_actual,
            'nodo_origen': u,
            'nodo_destino': v,
            'tramo': tramo_id,
            'origen': nombre_origen,
            'tiempo_ideal': tiempo_ideal,
            'congestibilidad_t_minus_1': congest_pasada,
            'congestibilidad_t': congest_actual,
            'target_congestibilidad_t_plus_1': congest_futura
        })

# Convertimos a DataFrame
df_ml = pd.DataFrame(datos_ml)

# Guardamos el CSV tabular
archivo_dataset = "datos_procesados/dataset_features_entrenamiento.csv"
df_ml.to_csv(archivo_dataset, index=False, encoding='utf-8-sig')

print(f"Dataset tabular generado exitosamente con {len(df_ml)} registros de entrenamiento.")
print(f"Guardado en: {archivo_dataset}")