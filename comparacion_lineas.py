import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Cargar los datos intentando forzar la codificación correcta
archivo_csv = "afluenciastc_desglosado_01_2026.csv"
print(f"Cargando datos desde {archivo_csv}...")

# Usamos encoding='utf-8'. Si el portal del gobierno usó otro formato, esto ayuda a interpretarlo mejor.
df_afluencia = pd.read_csv(archivo_csv, encoding="utf-8", low_memory=False)

# Limpieza de seguridad: Forzamos el reemplazo del texto corrupto si sigue existiendo
df_afluencia["linea"] = (
    df_afluencia["linea"].astype(str).str.replace("LÃ­nea", "Línea", regex=False)
)

# 2. Preparar la columna de fecha
df_afluencia["fecha"] = pd.to_datetime(df_afluencia["fecha"])

# 3. Filtrar y Agrupar
print("Filtrando datos para la Línea 1 y Línea 2...")
lineas_a_comparar = ["Línea 1", "Línea 2"]
df_filtrado = df_afluencia[df_afluencia["linea"].isin(lineas_a_comparar)]

# Agrupamos por fecha Y por línea, sumando la afluencia
afluencia_por_linea = (
    df_filtrado.groupby(["fecha", "linea"])["afluencia"].sum().reset_index()
)

# 4. Generar la gráfica comparativa
print("Generando gráfica comparativa...")
plt.figure(figsize=(14, 7))

# El parámetro 'hue' le dice a Seaborn que dibuje una línea distinta para cada categoría en la columna 'linea'
sns.lineplot(
    data=afluencia_por_linea,
    x="fecha",
    y="afluencia",
    hue="linea",
    palette="Set1",
    linewidth=1.5,
)

plt.title("Comparativa de Afluencia Diaria: Línea 1 vs Línea 2", fontsize=16)
plt.xlabel("Fecha", fontsize=12)
plt.ylabel("Total de Pasajeros", fontsize=12)
plt.xticks(rotation=45)
plt.legend(title="Línea")
plt.grid(
    True, linestyle="--", alpha=0.6
)  # Una cuadrícula suave ayuda a comparar mejor los niveles
plt.tight_layout()

# Muestra la gráfica en pantalla
plt.show()
