# IA Anticipatoria - STC Metro CDMX

**Alumno:** Alan Bellon García
**Asesor:** M. en Fil. C. Enrique Francisco Soto Astorga

## Descripción del Proyecto
Este repositorio contiene el código, la documentación y los experimentos para el proyecto de tesis: *"Modelado y prototipado de un sistema de Inteligencia Artificial Anticipatoria para la estimación de estados de congestión en el STC Metro de la Ciudad de México"*[cite: 4, 5].

El objetivo principal es desarrollar un prototipo basado en Inteligencia Artificial Anticipatoria para el modelado y la previsión de estados de saturación en la red del STC Metro[cite: 6, 7]. [cite_start]Ante la complejidad de acceder a flujos de datos masivos en tiempo real, el comportamiento del sistema se validará mediante la generación de un dataset sintético y un entorno de simulación[cite: 7, 9, 18].

## Estado Actual y Contenido del Repositorio
Actualmente, el proyecto se encuentra en la fase inicial de definición y análisis exploratorio de datos (EDA) sobre los históricos de afluencia.

### Documentación
* **Propuesta de Tesis:** Documento que detalla los objetivos, hipótesis, justificación y el aparato teórico fundamental (sistemas anticipatorios, teoría de grafos y aprendizaje automático) que guiará la investigación.

### Análisis Exploratorio de Datos (EDA)
Se incluyen los primeros scripts en Python para la limpieza y visualización de datos:
* `exploracion_afluencia.py`: Script para cargar el dataset de afluencia, revisar la estructura de memoria, estandarizar formatos de fecha y visualizar la afluencia diaria total de la red.
* `comparacion_lineas.py`: Script enfocado en filtrar, limpiar errores de codificación (encoding) y generar una gráfica comparativa de series temporales entre la afluencia de la Línea 1 y la Línea 2.

## Tecnologías Utilizadas (Hasta el momento)
* **Lenguaje:** Python
* **Manejo de Datos:** Pandas
* **Visualización:** Matplotlib, Seaborn
