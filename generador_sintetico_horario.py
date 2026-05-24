import pandas as pd
import numpy as np

print("Cargando dataset de afluencia diaria...")
# Asegúrate de tener tu archivo original en la misma ruta
df_diario = pd.read_csv("afluenciastc_desglosado_01_2026.csv")

def limpiar_texto(texto):
    if isinstance(texto, str):
        try:
            return texto.encode("latin1").decode("utf-8")
        except:
            return texto
    return texto

df_diario["estacion"] = df_diario["estacion"].apply(limpiar_texto)
df_diario["linea"] = df_diario["linea"].apply(limpiar_texto)
df_total_diario = (
    df_diario.groupby(["fecha", "linea", "estacion"])["afluencia"].sum().reset_index()
)

print("Definiendo perfiles espaciotemporales de demanda...")

# 1. Definimos 3 perfiles de comportamiento
perfiles_horarios = pd.DataFrame(
    {
        "hora": range(24),
        "peso_origen": [0.002, 0.002, 0.002, 0.002, 0.002, 0.04, 0.15, 0.18, 0.12, 0.06, 0.04, 0.03, 0.03, 0.03, 0.04, 0.04, 0.05, 0.06, 0.05, 0.03, 0.02, 0.01, 0.005, 0.005],
        "peso_destino": [0.002, 0.002, 0.002, 0.002, 0.002, 0.01, 0.02, 0.04, 0.05, 0.04, 0.04, 0.04, 0.05, 0.06, 0.06, 0.06, 0.08, 0.15, 0.14, 0.08, 0.04, 0.02, 0.01, 0.005],
        "peso_mixto": [0.002, 0.002, 0.002, 0.002, 0.002, 0.02, 0.09, 0.12, 0.09, 0.05, 0.04, 0.04, 0.04, 0.04, 0.05, 0.05, 0.06, 0.10, 0.09, 0.05, 0.03, 0.01, 0.005, 0.005],
    }
)

estaciones_origen = ["Pantitlán", "Indios Verdes", "Ciudad Azteca", "Tláhuac", "La Paz", "El Rosario", "Martín Carrera", "Tasqueña", "Universidad", "Constitución de 1917"]
estaciones_destino = ["Polanco", "Auditorio", "Insurgentes", "Chilpancingo", "Sevilla", "Zócalo/Tenochtitlan", "Bellas Artes", "Juárez", "Coyoacán", "Zapata"]

def asignar_perfil(estacion):
    if estacion in estaciones_origen: return "origen"
    elif estacion in estaciones_destino: return "destino"
    else: return "mixto"

df_total_diario["perfil"] = df_total_diario["estacion"].apply(asignar_perfil)

print("Cruzando datos y calculando afluencia de ENTRADA por hora...")

df_total_diario["key"] = 1
perfiles_horarios["key"] = 1
df_horario = pd.merge(df_total_diario, perfiles_horarios, on="key").drop("key", axis=1)

condiciones = [
    df_horario["perfil"] == "origen",
    df_horario["perfil"] == "destino",
    df_horario["perfil"] == "mixto",
]
elecciones = [
    df_horario["afluencia"] * df_horario["peso_origen"],
    df_horario["afluencia"] * df_horario["peso_destino"],
    df_horario["afluencia"] * df_horario["peso_mixto"],
]

df_horario["afluencia_sintetica_hora"] = np.select(condiciones, elecciones, default=0).astype(int)
df_horario = df_horario.drop(columns=["afluencia", "peso_origen", "peso_destino", "peso_mixto"]).sort_values(by=["fecha", "linea", "estacion", "hora"])
df_horario = df_horario[df_horario["hora"] >= 5]

# Guardamos el archivo base (entradas)
df_horario.to_csv("datos_procesados/entradas_sinteticas_horarias.csv", index=False, encoding="utf-8-sig")

# ====================================================================================
# NUEVA SECCIÓN: PUNTO 1 DE LA TESIS - CONSTRUCCIÓN DEL AMBIENTE (MATRIZ ORIGEN-DESTINO)
# ====================================================================================
print("\n--- Iniciando Generación de Matriz Origen-Destino (Modelo Gravitacional) ---")

def calcular_atractividad_destino(hora, perfil):
    """
    Asigna un peso de probabilidad para que una estación sea elegida como destino.
    """
    if 5 <= hora <= 11:
        # En la mañana, las zonas laborales ('destino') atraen a la mayoría.
        if perfil == 'destino': return 0.65
        elif perfil == 'mixto': return 0.25
        else: return 0.10
    elif 16 <= hora <= 21:
        # En la tarde, la gente regresa a casa ('origen').
        if perfil == 'origen': return 0.65
        elif perfil == 'mixto': return 0.25
        else: return 0.10
    else:
        # En horas valle, el flujo es más equilibrado.
        if perfil == 'mixto': return 0.50
        else: return 0.25

# Filtramos un día de prueba para construir la red (El mismo usado en tu simulador)
dia_simulacion = "2026-01-13"
df_dia = df_horario[df_horario['fecha'] == dia_simulacion].copy()

# Calculamos la atractividad de cada estación para cada hora
df_dia['peso_atractividad'] = df_dia.apply(lambda row: calcular_atractividad_destino(row['hora'], row['perfil']), axis=1)

# Preparamos DataFrames para el producto cartesiano
df_origen = df_dia[['hora', 'estacion', 'perfil', 'afluencia_sintetica_hora']].rename(
    columns={'estacion': 'origen', 'perfil': 'perfil_origen', 'afluencia_sintetica_hora': 'entradas'}
)
df_destino = df_dia[['hora', 'estacion', 'perfil', 'peso_atractividad']].rename(
    columns={'estacion': 'destino', 'perfil': 'perfil_destino', 'peso_atractividad': 'atractividad_destino'}
)

print(f"Cruzando posibles viajes para el día {dia_simulacion}...")
# Hacemos merge por hora: cruzamos todas las estaciones de origen con todas las de destino
df_od = pd.merge(df_origen, df_destino, on='hora')

# La gente no viaja a la misma estación en la que entró
df_od = df_od[df_od['origen'] != df_od['destino']]

# Sumamos la atractividad total disponible por cada hora y estación de origen para normalizar
suma_atractividad = df_od.groupby(['hora', 'origen'])['atractividad_destino'].sum().reset_index()
suma_atractividad.rename(columns={'atractividad_destino': 'atractividad_total'}, inplace=True)
df_od = pd.merge(df_od, suma_atractividad, on=['hora', 'origen'])

# Calculamos la proporción (probabilidad) y la aplicamos a las entradas reales
df_od['probabilidad'] = df_od['atractividad_destino'] / df_od['atractividad_total']
df_od['pasajeros_viaje'] = (df_od['entradas'] * df_od['probabilidad']).round().astype(int)

# Limpieza final de la Matriz O-D
df_od_final = df_od[['hora', 'origen', 'destino', 'perfil_origen', 'perfil_destino', 'pasajeros_viaje']]
# Eliminamos viajes con 0 pasajeros para optimizar
df_od_final = df_od_final[df_od_final['pasajeros_viaje'] > 0]

archivo_od = f"datos_procesados/matriz_od_sintetica_{dia_simulacion}.csv"
df_od_final.to_csv(archivo_od, index=False, encoding="utf-8-sig")

print(f"\n¡Dataset de ambiente creado exitosamente! Guardado en: {archivo_od}")

print("\n--- Muestra del comportamiento simulado ---")
viajes_manana = df_od_final[(df_od_final['hora'] == 7) & (df_od_final['origen'] == 'Pantitlán')].sort_values(by='pasajeros_viaje', ascending=False)
print("Top 3 destinos desde Pantitlán a las 7:00 AM:")
print(viajes_manana.head(3)[['destino', 'perfil_destino', 'pasajeros_viaje']])

viajes_tarde = df_od_final[(df_od_final['hora'] == 18) & (df_od_final['origen'] == 'Polanco')].sort_values(by='pasajeros_viaje', ascending=False)
print("\nTop 3 destinos desde Polanco a las 6:00 PM:")
print(viajes_tarde.head(3)[['destino', 'perfil_destino', 'pasajeros_viaje']])