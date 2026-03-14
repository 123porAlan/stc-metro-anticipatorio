import pandas as pd

print("Cargando dataset de afluencia diaria...")
df_diario = pd.read_csv("afluenciastc_desglosado_01_2026.csv")


def limpiar_texto(texto):
    if isinstance(texto, str):
        try:
            # Revertimos la doble codificación que rompe los acentos
            return texto.encode("latin1").decode("utf-8")
        except:
            return texto
    return texto


# Aplicamos la limpieza a las columnas afectadas
df_diario["estacion"] = df_diario["estacion"].apply(limpiar_texto)
df_diario["linea"] = df_diario["linea"].apply(limpiar_texto)
df_total_diario = (
    df_diario.groupby(["fecha", "linea", "estacion"])["afluencia"].sum().reset_index()
)

print("Definiendo perfiles espaciotemporales de demanda...")

# 1. Definimos 3 perfiles de comportamiento (Cada columna debe sumar 1.0)
# - ORIGEN: Alta demanda matutina (Gente saliendo de la periferia a trabajar)
# - DESTINO: Alta demanda vespertina (Gente regresando a casa desde centros laborales)
# - MIXTO: Comportamiento bimodal equilibrado (Estaciones de transbordo o céntricas)

perfiles_horarios = pd.DataFrame(
    {
        "hora": range(24),
        # Pico muy marcado 6 AM - 8 AM
        "peso_origen": [
            0.002,
            0.002,
            0.002,
            0.002,
            0.002,
            0.04,
            0.15,
            0.18,
            0.12,
            0.06,
            0.04,
            0.03,
            0.03,
            0.03,
            0.04,
            0.04,
            0.05,
            0.06,
            0.05,
            0.03,
            0.02,
            0.01,
            0.005,
            0.005,
        ],
        # Pico muy marcado 5 PM - 8 PM
        "peso_destino": [
            0.002,
            0.002,
            0.002,
            0.002,
            0.002,
            0.01,
            0.02,
            0.04,
            0.05,
            0.04,
            0.04,
            0.04,
            0.05,
            0.06,
            0.06,
            0.06,
            0.08,
            0.15,
            0.14,
            0.08,
            0.04,
            0.02,
            0.01,
            0.005,
        ],
        # Dos picos moderados (Mañana y Tarde)
        "peso_mixto": [
            0.002,
            0.002,
            0.002,
            0.002,
            0.002,
            0.02,
            0.09,
            0.12,
            0.09,
            0.05,
            0.04,
            0.04,
            0.04,
            0.04,
            0.05,
            0.05,
            0.06,
            0.10,
            0.09,
            0.05,
            0.03,
            0.01,
            0.005,
            0.005,
        ],
    }
)

# 2. Diccionarios de clasificación de estaciones clave (Nombres corregidos)
estaciones_origen = [
    "Pantitlán",
    "Indios Verdes",
    "Ciudad Azteca",
    "Tláhuac",
    "La Paz",
    "El Rosario",
    "Martín Carrera",
    "Tasqueña",
    "Universidad",
    "Constitución de 1917",
]

estaciones_destino = [
    "Polanco",
    "Auditorio",
    "Insurgentes",
    "Chilpancingo",
    "Sevilla",
    "Zócalo/Tenochtitlan",
    "Bellas Artes",
    "Juárez",
    "Coyoacán",
    "Zapata",
]


def asignar_perfil(estacion):
    """Asigna el perfil adecuado dependiendo del tipo de estación."""
    if estacion in estaciones_origen:
        return "origen"
    elif estacion in estaciones_destino:
        return "destino"
    else:
        return "mixto"  # Perfil por defecto para el resto de la red


# Aplicamos la clasificación
df_total_diario["perfil"] = df_total_diario["estacion"].apply(asignar_perfil)

print("Cruzando datos y calculando afluencia exacta por hora según perfil...")

# 3. Producto Cartesiano para expandir a 24 horas
df_total_diario["key"] = 1
perfiles_horarios["key"] = 1
df_horario = pd.merge(df_total_diario, perfiles_horarios, on="key").drop("key", axis=1)

# 4. Cálculo vectorial: Multiplicamos la afluencia total por el peso específico de su perfil
# Usamos numpy select o loc para aplicar la lógica condicional de forma masiva y rápida
import numpy as np

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

df_horario["afluencia_sintetica_hora"] = np.select(
    condiciones, elecciones, default=0
).astype(int)

# 5. Limpiamos y ordenamos
columnas_borrar = ["afluencia", "peso_origen", "peso_destino", "peso_mixto"]
df_horario = df_horario.drop(columns=columnas_borrar).sort_values(
    by=["fecha", "linea", "estacion", "hora"]
)

# Filtramos las horas donde el metro está cerrado (0 a 4 AM) si no queremos que aparezcan
df_horario = df_horario[df_horario["hora"] >= 5]

archivo_salida = "afluencia_sintetica_horaria_avanzada_2026.csv"
df_horario.to_csv(archivo_salida, index=False, encoding="utf-8-sig")

print(f"\n¡Proceso finalizado! Dataset avanzado guardado como: {archivo_salida}")

# Muestra comparativa (al final del script)
print("\n--- Comparación a las 7:00 AM (Hora Pico Matutina) ---")
muestra_mañana = df_horario[df_horario["hora"] == 7]
print(
    muestra_mañana[
        (muestra_mañana["estacion"].isin(["Pantitlán", "Polanco"]))
        & (muestra_mañana["fecha"] == "2026-01-01")
    ][["estacion", "perfil", "afluencia_sintetica_hora"]]
)

print("\n--- Comparación a las 6:00 PM (Hora Pico Vespertina) ---")
muestra_tarde = df_horario[df_horario["hora"] == 18]
print(
    muestra_tarde[
        (muestra_tarde["estacion"].isin(["Pantitlán", "Polanco"]))
        & (muestra_tarde["fecha"] == "2026-01-01")
    ][["estacion", "perfil", "afluencia_sintetica_hora"]]
)
