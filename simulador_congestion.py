import pandas as pd
import networkx as nx
import numpy as np

print("Cargando infraestructura (Grafo Base)...")
G_base = nx.read_gexf("grafo_base_metro.gexf") 

print("Cargando dinámica de pasajeros (Matriz O-D del Ambiente)...")
# Aquí leemos el archivo que creamos en el Punto 1
dia_simulacion = "2026-01-13"
df_od = pd.read_csv(f"datos_procesados/matriz_od_sintetica_{dia_simulacion}.csv")

def funcion_penalizacion_bpr(tiempo_base_min, afluencia_tramo, capacidad_tramo, alpha=0.15, beta=4):
    """
    Calcula el nuevo tiempo de viaje usando la función BPR adaptada para transporte público.
    """
    if pd.isna(afluencia_tramo) or afluencia_tramo == 0:
        return tiempo_base_min
    
    # Relación Volumen/Capacidad (V/C) en EL TRAMO ESPECÍFICO
    saturacion = afluencia_tramo / capacidad_tramo
    tiempo_congestivo = tiempo_base_min * (1 + alpha * (saturacion ** beta))
    tiempo_maximo = tiempo_base_min * 4 
    
    return min(tiempo_congestivo, tiempo_maximo)

print("Iniciando motor de simulación y captura de snapshots...")

# Capacidad base teórica de un tramo de línea por hora
CAPACIDAD_PROMEDIO_TRAMO_HORA = 35000

grafos_temporales = {}
horas_operacion = range(5, 24) # El snapshot se toma cada 1 unidad de tiempo (1 hora)

# Diccionario para mapear nombres de estaciones a sus IDs en el grafo para el ruteo
nombre_a_nodos = {}
for n, data in G_base.nodes(data=True):
    nombre = data.get('nombre')
    if nombre:
        if nombre not in nombre_a_nodos:
            nombre_a_nodos[nombre] = []
        nombre_a_nodos[nombre].append(n)

for hora in horas_operacion:
    G_hora = G_base.copy()
    
    # 1. Inicializamos la carga de pasajeros de toda la red en 0 para este snapshot
    nx.set_edge_attributes(G_hora, 0, 'carga_pasajeros')
    
    # Filtramos la matriz OD para la hora actual (el snapshot del EXTERIOR)
    df_hora = df_od[df_od['hora'] == hora]
    
    # 2. ENRUTAMIENTO: Hacemos que la gente viaje por la red
    for _, row in df_hora.iterrows():
        origen_nombre = row['origen']
        destino_nombre = row['destino']
        pasajeros = row['pasajeros_viaje']
        
        # Intentamos obtener un nodo válido para origen y destino
        if origen_nombre in nombre_a_nodos and destino_nombre in nombre_a_nodos:
            # Tomamos el primer andén asociado al nombre como punto de entrada/salida
            nodo_origen = nombre_a_nodos[origen_nombre][0]
            nodo_destino = nombre_a_nodos[destino_nombre][0]
            
            try:
                # Buscamos la ruta lógica que tomarían los usuarios basada en el tiempo
                ruta = nx.shortest_path(G_hora, source=nodo_origen, target=nodo_destino, weight='tiempo_minutos')
                
                # Sumamos la cantidad de pasajeros a CADA TRAMO por el que pasa el tren
                for i in range(len(ruta) - 1):
                    u = ruta[i]
                    v = ruta[i+1]
                    G_hora[u][v]['carga_pasajeros'] += pasajeros
            except nx.NetworkXNoPath:
                # Si algún nodo quedó desconectado en el diseño del grafo, lo ignoramos
                pass

    # 3. CÁLCULO DE CONGESTIÓN: Actualizamos el estado INTERNO de la red
    for u, v, data in G_hora.edges(data=True):
        carga_tramo = data['carga_pasajeros']
        tiempo_ideal = data.get('tiempo_minutos', 2.0) 
        
        # --- SIMULACIÓN DE DISRUPCIÓN PARA LA TESIS ---
        # Si es de 7 a 9 AM, simulamos que la Línea 9 sufre una falla inyectando carga fantasma
        if 7 <= hora <= 9 and "B_0200L9" in u:
            carga_tramo += 40000 
            
        nuevo_tiempo = funcion_penalizacion_bpr(tiempo_ideal, carga_tramo, CAPACIDAD_PROMEDIO_TRAMO_HORA)
        
        G_hora[u][v]['weight'] = round(nuevo_tiempo, 2)
        G_hora[u][v]['congestibilidad'] = round(nuevo_tiempo - tiempo_ideal, 2)
        
    # Guardamos el snapshot completo de esta hora
    grafos_temporales[hora] = G_hora

print("Simulación completada. Procesando dataset para la IA...")

# --- DATA PIPELINE: Extracción de snapshots para Machine Learning ---
datos_ml = []
horas_disponibles = sorted(list(grafos_temporales.keys()))

for i, hora_actual in enumerate(horas_disponibles):
    if i + 1 >= len(horas_disponibles) or i < 1:
        continue
        
    hora_siguiente = horas_disponibles[i + 1]
    hora_pasada = horas_disponibles[i - 1]
    
    G_actual = grafos_temporales[hora_actual]
    G_pasado = grafos_temporales[hora_pasada]
    G_siguiente = grafos_temporales[hora_siguiente]
    
    for u, v, data in G_actual.edges(data=True):
        nombre_origen = G_actual.nodes[u].get('nombre', str(u))
        nombre_destino = G_actual.nodes[v].get('nombre', str(v))
        tramo_id = f"{nombre_origen}-{nombre_destino}"
        
        tiempo_ideal = data.get('tiempo_minutos', 0)
        carga_actual = data.get('carga_pasajeros', 0)
        congest_actual = data.get('congestibilidad', 0)
        congest_pasada = G_pasado[u][v].get('congestibilidad', 0) if G_pasado.has_edge(u, v) else 0
        congest_futura = G_siguiente[u][v].get('congestibilidad', 0) if G_siguiente.has_edge(u, v) else 0
        
        datos_ml.append({
            'fecha': dia_simulacion,
            'hora': hora_actual,
            'nodo_origen': u,
            'nodo_destino': v,
            'tramo': tramo_id,
            'origen': nombre_origen,
            'tiempo_ideal': tiempo_ideal,
            'carga_pasajeros_red': carga_actual,
            'congestibilidad_t_minus_1': congest_pasada,
            'congestibilidad_t': congest_actual,
            'target_congestibilidad_t_plus_1': congest_futura
        })

df_ml = pd.DataFrame(datos_ml)
archivo_dataset = "datos_procesados/dataset_features_entrenamiento.csv"
df_ml.to_csv(archivo_dataset, index=False, encoding='utf-8-sig')

print(f"¡Dataset tabular (Snapshots) generado exitosamente con {len(df_ml)} registros de la red!")
print(f"Guardado en: {archivo_dataset}")