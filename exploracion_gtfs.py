import pandas as pd

# 1. Explorar las agencias disponibles
print("--- Leyendo agency.txt ---")
try:
    df_agency = pd.read_csv("agency.txt", encoding="utf-8-sig")
    print(df_agency[["agency_id", "agency_name"]])
except Exception as e:
    print(f"Error al leer agency.txt: {e}")

# 2. Explorar las primeras rutas
print("\n--- Leyendo routes.txt ---")
try:
    df_routes = pd.read_csv("routes.txt", encoding="utf-8-sig")
    print("Muestra de las rutas en el sistema:")
    print(df_routes[["route_id", "agency_id", "route_short_name"]].head(15))
except Exception as e:
    print(f"Error al leer routes.txt: {e}")
