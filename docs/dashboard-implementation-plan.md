# ECOS: Plan de Implementación de Dashboard Analítico Profesional

Este documento define la estrategia de visualización, análisis estadístico y diseño de experiencia de usuario (UX) para el sistema de monitoreo epidemiológico ECOS. El objetivo es transformar el modelo estrella curado en una herramienta de soporte a decisiones para salud pública.

---

## 1. Arquitectura de Navegación

El dashboard se organiza en tres niveles de profundidad para permitir desde una visión gerencial hasta un análisis de causa raíz:

### A. Vista de Control Ejecutivo (Nacional)
*   **Propósito**: Monitoreo en tiempo real de la situación del país.
*   **KPIs Principales**:
    *   **Casos Totales**: Con indicador de tendencia frente a la semana epidemiológica anterior.
    *   **Tasa de Incidencia Acumulada**: Casos por cada 100,000 habitantes.
    *   **Índice de Alerta**: Porcentaje de municipios en estado de "Brote".
    *   **Cobertura de Vacunación**: Promedio nacional vs meta (95%).

### B. Vista de Factores de Riesgo (Correlación)
*   **Propósito**: Entender el "por qué" de los brotes.
*   **Análisis Climático**: Relación entre anomalías de temperatura/precipitación y picos de casos.
*   **Análisis de Protección**: Identificación de zonas con baja cobertura de vacunación y alta incidencia.

### C. Vista Territorial (Detalle Local)
*   **Propósito**: Herramienta para secretarías de salud locales.
*   **Detalle**: Fichas técnicas por municipio con historial de los últimos 2 años.

---

## 2. Catálogo de Visualizaciones Sugeridas

| Sección | Tipo de Gráfico | Descripción y Uso |
| :--- | :--- | :--- |
| **Distribución** | Mapa de Coropletas | Mapa de Colombia con degradado de calor basado en la Tasa de Incidencia. Permite identificar clústeres geográficos de contagio. |
| **Tendencia** | Gráfico de Áreas Apiladas | Evolución semanal de casos agrupados por enfermedad (Dengue, Chikungunya, Zika, Malaria). |
| **Clima** | Gráfico Combo (Línea + Columnas) | Columnas para precipitación mensual y líneas para casos semanales. Crucial para observar el "Lag" o desfase entre lluvias y brotes. |
| **Vacunación** | Gráfico de Dispersión (Scatter) | Eje X: Cobertura de Vacunación, Eje Y: Casos. Las burbujas (municipios) en el cuadrante superior izquierdo representan el mayor riesgo. |
| **Estacionalidad** | Heatmap (Calendario) | Meses en el eje X, Años en el eje Y. La intensidad del color muestra los meses históricamente más críticos. |

---

## 3. Lógica Estadística y Medidas DAX Recomendadas

Para implementar este dashboard en herramientas como Power BI o Tableau, se sugieren las siguientes medidas calculadas:

1.  **Tasa de Incidencia**: 
    `Incidencia = (SUM(fact_core_weekly[cases_total]) / SUM(dim_municipios[poblacion])) * 100000`
2.  **Canal Endémico (Línea Base)**:
    Cálculo del promedio móvil de los últimos 5 años para la misma semana epidemiológica. Si la semana actual supera el percentil 75, se dispara una alerta visual.
3.  **Promedio Móvil (4 semanas)**:
    Suaviza la curva de casos para eliminar el ruido de reportes tardíos y visualizar la tendencia real de la epidemia.

---

## 4. Estética y Diseño (Look & Feel)

*   **Paleta de Colores**: 
    *   Fondo: Gris oscuro o azul medianoche (#121212) para reducir la fatiga visual.
    *   Métricas Positivas: Esmeralda/Verde Neón.
    *   Alertas de Brote: Rojo Coral o Naranja Intenso.
*   **Tipografía**: Sans-serif moderna (Inter, Roboto o Montserrat) para máxima legibilidad de números.
*   **Interactividad**: 
    *   Uso de "Slicers" (segmentadores) sincronizados entre todas las páginas.
    *   "Tooltips" visuales: Al pasar el cursor sobre un municipio en el mapa, se debe desplegar un mini-gráfico de su tendencia de casos.

---

## 5. Roadmap de Implementación

1.  **Fase 1 (Datos)**: Carga de archivos Parquet/CSV corregidos a la base de datos Supabase.
2.  **Fase 2 (Modelo)**: Creación de relaciones entre `fact_core_weekly` y las dimensiones `dim_departamentos`, `dim_municipios`.
3.  **Fase 3 (Visual)**: Construcción de las 3 páginas principales y validación de filtros.
4.  **Fase 4 (Publicación)**: Configuración de actualización automática y accesos de usuario.
