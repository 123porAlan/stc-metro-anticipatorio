# IA Anticipatoria - STC Metro CDMX

**Alumno:** Alan Bellon García
**Asesor:** M. en Fil. C. Enrique Francisco Soto Astorga

## Descripción del Proyecto
Este repositorio contiene el código, la documentación y los experimentos para el proyecto de tesis: *"Modelado y prototipado de un sistema de Inteligencia Artificial Anticipatoria para la estimación de estados de congestión en el STC Metro de la Ciudad de México"*.

El objetivo principal es desarrollar un prototipo basado en Inteligencia Artificial Anticipatoria para el modelado y la previsión de estados de saturación en la red del STC Metro. Ante la complejidad de acceder a flujos de datos masivos en tiempo real, el comportamiento del sistema se validará mediante la generación de un dataset sintético y un entorno de simulación.

## Estado Actual y Contenido del Repositorio
Actualmente, el proyecto ha avanzado desde la fase de análisis exploratorio de datos (EDA) hacia el modelado topológico de la infraestructura de la red utilizando datos en formato GTFS.

### Documentación
* **Propuesta de Tesis:** Documento que detalla los objetivos, hipótesis, justificación y el aparato teórico fundamental (sistemas anticipatorios, teoría de grafos y aprendizaje automático) que guiará la investigación.

### Análisis Exploratorio de Datos (EDA) y Modelado
Se incluyen los scripts en Python para la limpieza, visualización de datos de afluencia y la construcción inicial del modelo de la red:
* `exploracion_afluencia.py`: Script para cargar el dataset de afluencia, revisar la estructura de memoria, estandarizar formatos de fecha y visualizar la afluencia diaria total de la red.
* `comparacion_lineas.py`: Script enfocado en filtrar, limpiar errores de codificación (encoding) y generar una gráfica comparativa de series temporales entre la afluencia de la Línea 1 y la Línea 2.
* `grafo_metro.py`: Script que procesa los archivos GTFS (`routes.txt`, `trips.txt`, `stops.txt`, `stop_times.txt`) para construir la representación topológica de la red del STC Metro. Genera un grafo bidireccional donde los nodos representan las estaciones y las aristas las conexiones, visualizando el mapa de la red.

## Tecnologías Utilizadas (Hasta el momento)
* **Lenguaje:** Python
* **Manejo de Datos:** Pandas
* **Teoría de Grafos y Redes:** NetworkX
* **Visualización:** Matplotlib, Seaborn
