import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Cargar los datos
# Usamos low_memory=False para evitar advertencias si hay tipos de datos mixtos
archivo_csv = "afluenciastc_desglosado_01_2026.csv"
print(f"Cargando datos desde {archivo_csv}...")
df_afluencia = pd.read_csv(archivo_csv, low_memory=False)

# 2. Exploración inicial de la estructura
print("\n--- Primeras 5 filas del Dataset ---")
print(df_afluencia.head())

print("\n--- Información general de las columnas y memoria ---")
# Esto es vital para tus 8GB de RAM; te dirá cuánto espacio ocupa este archivo en memoria
print(df_afluencia.info())

# 3. Limpieza básica
# Asumiendo que el diccionario indica que hay una columna 'fecha' y una 'afluencia'
# (Nota: Si las columnas se llaman distinto, cambia los nombres en las siguientes líneas)
# Convertimos la columna de fecha a formato datetime de Pandas
if "fecha" in df_afluencia.columns:
    df_afluencia["fecha"] = pd.to_datetime(df_afluencia["fecha"])

# 4. Agrupación y Visualización
# Vamos a sumar la afluencia total de toda la red por cada día
if "fecha" in df_afluencia.columns and "afluencia" in df_afluencia.columns:
    print("\nGenerando gráfica de afluencia diaria total...")

    # Agrupamos por fecha y sumamos
    afluencia_diaria = df_afluencia.groupby("fecha")["afluencia"].sum().reset_index()

    # Configuración de la gráfica
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=afluencia_diaria, x="fecha", y="afluencia", color="orange")

    plt.title("Afluencia Diaria Total en la Red del STC Metro")
    plt.xlabel("Fecha")
    plt.ylabel("Total de Pasajeros")
    plt.xticks(rotation=45)
    plt.tight_layout()  # Ajusta los márgenes

    # Muestra la gráfica en pantalla
    plt.show()
else:
    print(
        "\nRevisa los nombres de las columnas en el head(). Parece que 'fecha' o 'afluencia' tienen otro nombre en tu CSV."
    )
