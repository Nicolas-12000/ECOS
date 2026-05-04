# ECOS — Early Control and Observation System
## Plataforma Nacional de Alerta Temprana para Enfermedades de Alto Impacto en Colombia

**Concurso:** Datos al Ecosistema 2026: IA para Colombia  
**Categoría:** Innovación Social / Inteligencia Artificial Aplicada a Datos Abiertos  
**Reto principal:** Reto 1 — Salud y Bienestar  
**Cobertura:** Nacional (todos los departamentos y municipios de Colombia)

---

## 1. Resumen Ejecutivo

ECOS (Early Control and Observation System) es una plataforma web nacional de alerta temprana que combina modelos de inteligencia artificial predictiva, un asistente conversacional basado en recuperación de información aumentada (RAG) y un dashboard interactivo para detectar brotes de dengue, chikungunya, zika y malaria entre 2 y 4 semanas antes de que sean reportados oficialmente por el Sistema Nacional de Vigilancia en Salud Pública (SIVIGILA).

La plataforma integra seis conjuntos de datos abiertos provenientes de datos.gov.co, complementados con señales tempranas obtenidas mediante scraping automatizado de Google Trends y medios de comunicación nacionales y regionales. El procesamiento de datos se realiza con Apache Spark, los modelos predictivos se construyen sobre XGBoost y Prophet, y la explicabilidad de las predicciones se garantiza mediante SHAP (SHapley Additive exPlanations).

ECOS está diseñado para ser usado directamente por el Ministerio de Salud y Protección Social, secretarías departamentales de salud, el Instituto Nacional de Salud (INS) y equipos de respuesta territorial. La solución es escalable, de código abierto, desplegable con Docker y alineada con los estándares CRISP-ML exigidos por el concurso.

**Impacto esperado:** reducción del rezago en alertas epidemiológicas, optimización de recursos sanitarios y prevención de miles de casos anuales a nivel nacional.

---

## 2. Problema Identificado

### 2.1 Contexto epidemiológico en Colombia

Colombia enfrenta de forma endémica brotes recurrentes de enfermedades transmitidas por vectores, especialmente dengue, chikungunya, zika y malaria. Estas enfermedades afectan de manera desproporcionada a las regiones Caribe, Pacífico, Amazonía, Orinoquía y zonas de alta humedad como Nariño, Huila, Tolima y Valle del Cauca.

En periodos recientes, el país ha registrado más de 498.000 casos de dengue en un solo ciclo epidémico, con tasas de mortalidad que podrían reducirse significativamente con detección oportuna.

### 2.2 Falla del sistema actual

El sistema SIVIGILA, aunque robusto como instrumento de vigilancia pasiva, presenta un rezago estructural de entre 2 y 4 semanas entre la ocurrencia del caso, su notificación por parte del prestador de salud, la consolidación a nivel municipal y departamental, y la alerta nacional. Este rezago implica que cuando las autoridades sanitarias identifican un brote, este ya está en fase de expansión comunitaria.

Adicionalmente, las secretarías de salud departamentales y municipales carecen de herramientas de análisis predictivo que integren variables ambientales, sociales y epidemiológicas en tiempo real, lo que limita su capacidad de anticipación y respuesta temprana.

### 2.3 Oportunidad de datos abiertos

Colombia cuenta con uno de los portales de datos abiertos más completos de América Latina (datos.gov.co), con registros históricos de vigilancia epidemiológica desde 2007, datos de calidad del aire, coberturas de vacunación y acceso a servicios de salud. Esta riqueza de información no está siendo aprovechada para construir sistemas predictivos integrados de uso gubernamental.

---

## 3. Objetivo General

Realizar un análisis predictivo integral de los datos abiertos de vigilancia epidemiológica (SIVIGILA y complementarios) para generar un sistema de alerta temprana que identifique, con 2-4 semanas de anticipación, el riesgo de brotes de dengue, chikungunya, zika y malaria a nivel nacional y municipal, integrando de forma lógica variables históricas, ambientales, de movilidad y señales en tiempo real, con el fin de apoyar la toma de decisiones basadas en evidencia por parte de las autoridades sanitarias colombianas. 

### 3.1 Objetivos Específicos

- Integrar y procesar seis fuentes de datos abiertos de datos.gov.co relacionadas con vigilancia epidemiológica, medio ambiente, vacunación y acceso a salud.
- Construir un módulo de scraping ético y automatizado que capture señales tempranas de Google Trends y medios de comunicación nacionales y regionales.
- Desarrollar modelos predictivos (XGBoost + Prophet) que estimen la probabilidad de brote por municipio y departamento con horizonte de 2 a 4 semanas.
- Implementar un asistente conversacional (RAG con LangChain y Groq) capaz de responder preguntas en lenguaje natural sobre riesgo epidemiológico.
- Desplegar un dashboard interactivo (Plotly Dash) con mapas de calor nacionales, filtros por región y simulaciones de escenarios.
- Publicar todo el proyecto como código abierto en GitHub bajo estándares CRISP-ML.

---

## 4. Alcance de la Solución

### 4.1 Enfermedades cubiertas

| Enfermedad | Justificación |
|---|---|
| Dengue | Principal arbovirosis en Colombia; ciclos epidémicos bianuales. |
| Chikungunya | Presencia sostenida desde 2014; comparte vector con dengue. |
| Zika | Relevancia por impacto en gestantes y síndrome de Guillain-Barré. |
| Malaria | Endémica en regiones Pacífico, Amazonía y Orinoquía. |

Estas cuatro enfermedades comparten el vector *Aedes aegypti* o *Anopheles* y presentan patrones de estacionalidad ligados a variables climáticas, lo que las hace especialmente susceptibles a modelado predictivo integrado.

### 4.2 Cobertura geográfica

ECOS opera a nivel nacional con capacidad de drill-down por departamento y municipio. La cobertura incluye los 32 departamentos y el Distrito Capital, con énfasis especial en las regiones de mayor carga epidémica:

- **Región Caribe:** Bolívar, Córdoba, Sucre, Atlántico, Cesar, La Guajira, Magdalena.
- **Región Pacífico:** Valle del Cauca, Cauca, Nariño, Chocó.
- **Región Amazónica:** Amazonas, Putumayo, Caquetá, Vaupés.
- **Región Orinoquía:** Meta, Casanare, Vichada, Guainía.
- **Región Andina:** Huila, Tolima, Antioquia, Cundinamarca, Santanderes.
- **Insular:** San Andrés y Providencia.

Esta cobertura responde directamente a la recomendación del concurso de priorizar regiones con menor participación digital y mayor vulnerabilidad epidemiológica.

### 4.3 Horizonte de predicción

El sistema genera predicciones a corto plazo (1 a 2 semanas) y mediano plazo (3 a 4 semanas), permitiendo tanto respuestas operativas inmediatas como planificación preventiva de recursos.

---

## 5. Fuentes de Datos

### 5.1 Datos abiertos de datos.gov.co (fuentes primarias)

#### Dataset 1 — Datos de Vigilancia en Salud Pública de Colombia (SIVIGILA 2007–2022)

- **Enlace:** https://www.datos.gov.co/Salud-y-Protecci-n-Social/Datos-de-Vigilancia-en-Salud-P-blica-de-Colombia/4hyg-wa9d
- **Entidad productora:** Instituto Nacional de Salud (INS)
- **Descripción:** Registro histórico semanal de casos notificados al sistema de vigilancia epidemiológica, desagregado por municipio, semana epidemiológica, grupo de edad, sexo y evento de interés en salud pública.
- **Volumen:** Millones de registros (supera los 10.000 filas — nivel de complejidad avanzado).
- **Variables clave utilizadas:** código DANE del municipio, semana epidemiológica, año, código del evento (dengue, chikungunya, zika, malaria), número de casos confirmados, casos probables y muertes.
- **Por qué lo usamos:** Es la fuente de verdad epidemiológica en Colombia. Sin este dataset no es posible entrenar modelos predictivos con validez histórica ni establecer líneas base de incidencia por territorio.

#### Dataset 2 — Chikungunya: Eventos específicos recientes

- **Enlace:** https://www.datos.gov.co/en/en/dataset/Chikungunya/nu5z-zutz
- **Entidad productora:** Instituto Nacional de Salud (INS)
- **Descripción:** Datos específicos sobre el evento de chikungunya con mayor resolución temporal y variables clínicas adicionales.
- **Variables clave utilizadas:** fecha de inicio de síntomas, clasificación del caso, semana epidemiológica, municipio de procedencia.
- **Por qué lo usamos:** Complementa el SIVIGILA histórico con mayor granularidad para uno de los eventos de interés. Permite calibrar el modelo para este evento específico con variables clínicas que no están disponibles en el registro histórico agregado.

#### Dataset 3 — Normales Climatologicas de Colombia (IDEAM)

- **Enlace:** https://www.datos.gov.co/d/nsz2-kzcq
- **Entidad productora:** IDEAM (Instituto de Hidrologia, Meteorologia y Estudios Ambientales)
- **Descripcion:** Normales climatologicas 1961-2020 por estacion y municipio, con promedios mensuales y anuales de temperatura, humedad relativa y precipitacion.
- **Variables clave utilizadas:** temperatura media/max/min, humedad relativa promedio, precipitacion promedio, municipio, departamento.
- **Por que lo usamos:** Aporta cobertura nacional de variables climaticas como baseline. Se pueden mapear normales mensuales a semanas para enriquecer el modelo; si en el futuro se consigue un dataset meteorologico semanal o diario nacional, se reemplaza por ese.

#### Dataset 4 — Coberturas Administrativas de Vacunación por Departamento

- **Enlace:** https://www.datos.gov.co/Salud-y-Protecci-n-Social/Coberturas-administrativas-de-vacunaci-n-por-depar/6i25-2hdt
- **Entidad productora:** Ministerio de Salud y Protección Social
- **Descripción:** Coberturas de vacunación por departamento, biológico y grupo de edad, con series anuales.
- **Variables clave utilizadas:** departamento, año, tipo de biológico, cobertura porcentual.
- **Por qué lo usamos:** La cobertura de vacunación es un indicador indirecto de la capacidad del sistema de salud y de la protección inmunológica de la población. Departamentos con coberturas bajas tienen mayor susceptibilidad a brotes. Esta variable actúa como factor de riesgo en el modelo predictivo a nivel departamental.

#### Dataset 5 — Registros de Prestación de Servicios de Salud (RIPS)

- **Enlace:** https://www.datos.gov.co/d/4k9h-8qiu (oficial) y https://www.datos.gov.co/d/5e6c-5p2c (vista agregada)
- **Entidad productora:** Ministerio de Salud y Protección Social
- **Descripción:** Registros de atenciones en salud (consultas, urgencias y hospitalizaciones), con clasificación por diagnóstico (CIE-10); usamos la vista agregada para conteos por municipio y mes.
- **Variables clave utilizadas:** código de diagnóstico CIE-10 relacionado con arbovirosis y malaria, número de atenciones, municipio, mes.
- **Por qué lo usamos:** Los RIPS capturan casos que son atendidos en el sistema de salud pero que pueden no haber sido notificados aún a SIVIGILA, funcionando como señal de alerta paralela. La divergencia entre RIPS y SIVIGILA en un municipio puede ser un indicador temprano de subnotificación o de inicio de brote.

#### Dataset 6 — Datos de Movilidad Urbana y Transporte

- **Enlaces (KISS + cobertura nacional):**
  - Nacional (intermunicipal, flujos entre municipios): https://www.datos.gov.co/d/eh75-8ah6
  - Medellin (terminal transporte): https://www.datos.gov.co/d/pfsr-mdyi
  - Opcional: Encuesta de movilidad Bogota (SIMUR) https://www.simur.gov.co/encuestas-de-movilidad
- **Entidad productora:** Ministerio de Transporte / Entidades territoriales.
- **Descripcion:** Flujos de pasajeros intermunicipales (cobertura nacional) y proxy urbano en hubs (terminal Medellin). En Bogota, el dataset CGT disponible es inventario de sensores sin conteos; no se usa hasta encontrar un endpoint con mediciones de aforo.
- **Variables clave utilizadas:** origen-destino intermunicipal, volumen de pasajeros, conteo vehicular por punto/sensor, fecha/hora, rutas de transporte.
- **Por que lo usamos:** No es redundante. El dataset nacional mide movilidad entre municipios (difusion regional), mientras que los urbanos capturan dinamica intra-urbana en hubs donde se concentran casos. Medellin se usa como granularidad y validacion para Antioquia; si queremos KISS estricto, se puede dejar solo el nacional (o nacional + Bogota) sin perder cobertura nacional.
- **Control de sesgos:** El modelo nacional usa solo movilidad intermunicipal. Los datasets urbanos se usan para analisis local y validacion (casos de estudio), no se extrapolan al resto del pais.

### 5.2 Fuentes externas obtenidas mediante scraping (señales tempranas)

Las fuentes externas se obtienen de forma automatizada mediante un módulo de scraping desarrollado en Python. Este componente es uno de los diferenciales técnicos más importantes de ECOS, porque captura señales que preceden entre 1 y 3 semanas a los reportes oficiales.

#### Fuente A — Google Trends (via `pytrends`)

- **Herramienta:** Librería `pytrends` (Python), interfaz no oficial de la API de Google Trends.
- **Palabras clave monitoreadas:** "dengue síntomas", "fiebre dengue", "mosquito dengue", "chikungunya Colombia", "malaria Colombia", "zika síntomas", "fiebre alta mosquito", "dolor articulaciones fiebre".
- **Granularidad:** Por departamento colombiano, frecuencia semanal.
- **Por qué lo usamos:** Múltiples estudios epidemiológicos internacionales (incluyendo trabajos del CDC y de la OPS) han demostrado que el volumen de búsquedas en Google sobre síntomas de una enfermedad precede a los reportes oficiales en 1 a 3 semanas. Cuando la población comienza a buscar "síntomas de dengue" de forma masiva en un departamento, es un indicador de que hay casos en curso que aún no han llegado al sistema de salud. Esta señal funciona como proxy de demanda sintomática no atendida.
- **Consideraciones éticas:** `pytrends` no recolecta datos personales; accede únicamente a tendencias agregadas y anonimizadas publicadas por Google de forma pública.

#### Fuente B — RSS de medios nacionales y regionales (via `feedparser`)

- **Herramienta:** Librería `feedparser` (Python) para consumo de feeds RSS; `BeautifulSoup` para extracción de texto de artículos.
- **Medios monitoreados:**
  - El Tiempo (eltiempo.com/rss): cobertura nacional.
  - El Colombiano (elcolombiano.com): Antioquia y región.
  - El Heraldo (elheraldo.co): Costa Caribe.
  - La Opinión (laopinion.com.co): Nariño y frontera con Ecuador.
  - El Diario del Huila (diariodelhuila.com): Huila y sur del país.
  - Noticias RCN (noticiasrcn.com/rss): cobertura nacional.
  - Caracol Radio (caracol.com.co/rss): cobertura nacional.
  - Boletines epidemiológicos del INS (ins.gov.co): fuente oficial.
- **Términos de búsqueda:** "dengue", "brote", "alerta sanitaria", "chikungunya", "malaria", "zika", "epidemia", "casos", "vector", "mosquito".
- **Por qué lo usamos:** Los medios regionales frecuentemente reportan alertas locales, declaraciones de alcaldes o secretarías de salud y testimonios comunitarios antes de que la información llegue a los sistemas formales de notificación. Un artículo en un periódico regional sobre "aumento de casos de dengue en el municipio X" es una señal temprana verificable y citeable.
- **Procesamiento:** Los artículos relevantes se procesan con un modelo de clasificación de texto ligero (TF-IDF + regresión logística en primera fase; posiblemente BERT distilado en fase avanzada) que determina si el contenido está relacionado con un evento epidemiológico activo, en qué municipio o departamento ocurre y qué enfermedad menciona.
- **Consideraciones éticas:** Solo se consumen feeds RSS públicos y páginas indexadas. No se realiza scraping de redes sociales ni de datos protegidos. Se respetan los archivos `robots.txt` de cada medio. Los datos recolectados no contienen información personal.

#### Fuente C — Boletines epidemiológicos del INS (PDF automatizado)

- **Herramienta:** `requests` + `pdfplumber` (Python).
- **Fuente:** https://www.ins.gov.co/buscador-eventos (boletines semanales públicos del INS).
- **Por qué lo usamos:** Los boletines del INS son publicados cada semana y contienen alertas departamentales, umbrales de alerta y comparativos históricos. Automatizar su lectura permite incorporar esta información al modelo sin procesamiento manual.

### 5.3 API de clima actual (sin costo)

Para datos climáticos actuales (diarios/semanales) usamos una API gratuita y sin llave, que permite construir el historial operativo y actualizar el modelo con condiciones reales de la semana.

#### Fuente D — Open-Meteo (API gratuita)

- **Enlace:** https://open-meteo.com/
- **Cobertura:** global (incluye Colombia), sin costo y sin autenticación.
- **Variables usadas:** temperatura media/max/min, humedad relativa, precipitacion.
- **Flujo:** consulta diaria → agregación semanal → unión por municipio (a partir de coordenadas) → persistencia en data/raw y data/processed.
- **Por qué lo usamos:** provee clima actual para el modelo sin depender de scraping ni pagos. Se complementa con IDEAM normales para baseline historico.

---

## 6. Arquitectura Técnica

### 6.1 Visión general

ECOS está compuesto por tres capas principales que se comunican entre sí a través de una API REST:

```
┌──────────────────────────────────────────────┐
│              CAPA DE PRESENTACIÓN             │
│  Dashboard Plotly Dash + Chat RAG (Next.js)   │
└─────────────────────┬────────────────────────┘
                      │ HTTP / WebSocket
┌─────────────────────▼────────────────────────┐
│               CAPA DE SERVICIOS               │
│         FastAPI (Python 3.11+)                │
│  /predict  /chat  /dashboard-data  /alerts    │
└──────────┬──────────────┬────────────────────┘
           │              │
┌──────────▼───┐   ┌──────▼──────────────────┐
│  MODELOS ML  │   │   MÓDULO DE SCRAPING     │
│  XGBoost     │   │   pytrends               │
│  Prophet     │   │   feedparser             │
│  SHAP        │   │   pdfplumber             │
└──────────┬───┘   └──────┬──────────────────┘
           │              │
┌──────────▼──────────────▼──────────────────┐
│           CAPA DE DATOS                     │
│  PySpark — procesamiento de datasets        │
│  6 fuentes datos.gov.co + scraped signals   │
│  PostgreSQL local / Parquet para persistencia│
└─────────────────────────────────────────────┘
```

### 6.2 Stack tecnológico detallado

| Componente | Tecnología | Justificación |
|---|---|---|
| API principal | FastAPI (Python 3.11+) | Alto rendimiento, documentación automática Swagger, fácil integración con librerías ML. |
| Procesamiento de datos | Apache Spark (PySpark) | Necesario para el volumen del histórico SIVIGILA (millones de registros). Escala a data lakes institucionales. |
| Modelo predictivo series temporales | Prophet (Meta) | Diseñado para series con estacionalidad múltiple y datos faltantes, ideal para semanas epidemiológicas. |
| Modelo clasificación y regresión | XGBoost | Alta precisión en datos tabulares, manejo nativo de valores nulos, velocidad de entrenamiento. |
| Explicabilidad | SHAP | Permite comunicar al jurado y a tomadores de decisión qué variables influyen más en cada predicción. |
| RAG y chat IA | LangChain + Groq (LLaMA 3) | Groq es gratuito y ultrarápido; LangChain facilita la construcción del pipeline RAG sobre los datasets abiertos. |
| Dashboard | Plotly Dash | 100% Python, código abierto, embebible, permite mapas interactivos, filtros y gráficos de series temporales sin dependencias externas de licencia. |
| Frontend (opcional) | Next.js 15 + Tailwind | Para versión web completa con autenticación y notificaciones. |
| Scraping | pytrends + feedparser + pdfplumber | Herramientas especializadas, ligeras y sin dependencias pesadas. |
| Infraestructura | Docker + Docker Compose | Garantiza reproducibilidad local y demo sin servicios pagos. |
| CI/CD | GitHub Actions | Automatización de pruebas y despliegue en menos de 3 minutos. |
| Persistencia | PostgreSQL local + archivos Parquet | PostgreSQL para datos operacionales; Parquet para almacenamiento eficiente de series históricas grandes. |

### 6.3 Flujo de datos

1. **Ingesta:** PySpark lee los datasets de datos.gov.co en formato CSV/JSON y los archivos descargados localmente.
2. **Preprocesamiento:** Limpieza, normalización de códigos DANE, imputación de valores faltantes, agregación semanal por municipio.
3. **Enriquecimiento:** El módulo de scraping añade la señal de Google Trends y el conteo de menciones en medios por departamento y semana.
4. **Modelado:** Prophet genera la predicción de series temporales base; XGBoost añade las variables exógenas (clima, vacunación, movilidad, señales de scraping) para corregir la predicción.
5. **Explicabilidad:** SHAP calcula la contribución de cada variable a la predicción, generando gráficos de barras por municipio.
6. **Exposición:** FastAPI expone los resultados vía endpoints REST; Plotly Dash los visualiza; el chat RAG permite consultas en lenguaje natural.

---

## 7. Componentes Funcionales de ECOS

### 7.1 Dashboard ejecutivo nacional

El tablero principal muestra:

- **Mapa de calor nacional:** Probabilidad de brote por departamento para las próximas 2 y 4 semanas, con escala de colores (verde → amarillo → rojo).
- **Mapa de municipios:** Drill-down por departamento con nivel de riesgo municipal.
- **Gráficos de tendencia:** Evolución histórica de casos vs. predicción del modelo para cada enfermedad y departamento.
- **Panel de señales tempranas:** Gráfico que muestra el índice de búsqueda en Google Trends y el volumen de menciones en medios, comparado con la incidencia histórica.
- **SHAP plots:** Visualización de las variables que más están contribuyendo al riesgo en cada región (ej: "La alta humedad relativa en Nariño esta semana es el principal factor de riesgo predicho").
- **Simulador what-if:** Permite a los tomadores de decisión ajustar variables (ej: "¿Qué pasaría si la cobertura de vacunación en el Chocó aumenta un 15%?") y ver el impacto en la predicción.

### 7.2 Asistente conversacional (RAG)

El chat integrado permite preguntas como:

- "¿Cuál es la probabilidad de brote de dengue en Nariño en las próximas tres semanas?"
- "¿Qué municipios de la Costa Caribe tienen mayor riesgo de malaria este mes?"
- "¿Cuántos casos de chikungunya se reportaron en el Valle del Cauca en 2019?"
- "¿Qué señales tempranas están activas hoy en la región Amazónica?"

El asistente responde con el porcentaje de riesgo calculado, las fuentes de datos que respaldan la respuesta, las variables más influyentes según SHAP y una recomendación de acción (ej: activación de brigadas de fumigación, refuerzo de puestos de salud, emisión de alerta a la comunidad).

### 7.3 Sistema de alertas automáticas

ECOS genera alertas automáticas cuando la probabilidad de brote supera umbrales predefinidos. Las alertas se envían vía:

- **Email:** A los correos registrados de secretarías de salud departamentales.
- **Reporte PDF automático:** Generado con `reportlab`, incluye mapas, gráficas, SHAP summary y recomendaciones. Listo para ser enviado a un despacho ministerial.

### 7.4 Módulo de publicación y transparencia

- Todos los resultados se publican en el repositorio GitHub público.
- El enlace al proyecto se registra en https://herramientas.datos.gov.co/usos.
- Los datasets procesados se publican como archivos Parquet descargables para reutilización por otras instituciones.

---

## 8. Metodología CRISP-ML

El proyecto sigue la metodología CRISP-ML (Cross-Industry Standard Process for Machine Learning), requerida por los términos del concurso. La estructura del repositorio refleja cada fase:

```
ecos/
├── crisp-ml/
│   ├── 01-business-understanding.md
│   ├── 02-data-understanding.md
│   ├── 03-data-preparation.ipynb
│   ├── 04-modeling.ipynb
│   ├── 05-evaluation.ipynb
│   └── 06-deployment.md
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
├── src/
│   ├── api/           (FastAPI)
│   ├── models/        (XGBoost + Prophet)
│   ├── scraping/      (pytrends + feedparser)
│   ├── dashboard/     (Plotly Dash)
│   └── rag/           (LangChain + Groq)
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

### 8.1 Fase 1 — Comprensión del negocio

Identificación del problema de rezago en SIVIGILA, definición del usuario final (MinSalud, secretarías departamentales), establecimiento del horizonte de predicción de 2 a 4 semanas y alineación con la Hoja de Ruta Sectorial de Salud 2025-2026.

### 8.2 Fase 2 — Comprensión de los datos

Análisis exploratorio de los 6 datasets de datos.gov.co: distribución temporal de casos, cobertura geográfica, calidad de datos, identificación de valores atípicos y periodos con datos faltantes (especialmente durante el periodo COVID-19 2020-2021, que requiere tratamiento especial).

### 8.3 Fase 3 — Preparación de los datos

Proceso con PySpark: normalización de códigos DANE a nivel municipal, agregación semanal de casos, unión de datasets por municipio y semana, imputación de valores faltantes, normalización de variables climáticas, codificación de variables categóricas y construcción del dataset de entrenamiento final.

### 8.4 Fase 4 — Modelado

- **Modelo base:** Prophet con estacionalidad anual, semanal y efectos de días festivos colombianos. Variables exógenas: temperatura, humedad, precipitación, señal Google Trends.
- **Modelo de enriquecimiento:** XGBoost sobre ventanas temporales de 4 semanas, con variables de movilidad, cobertura de vacunación y conteo de menciones en medios.
- **Estrategia de validación:** Validación cruzada temporal (walk-forward validation), respetando la naturaleza secuencial de los datos epidemiológicos. No se usa validación cruzada aleatoria para evitar data leakage temporal.

### 8.5 Fase 5 — Evaluación

Métricas principales:

- **MAE** (Mean Absolute Error) sobre número de casos predichos vs. reportados.
- **RMSE** (Root Mean Squared Error) para penalizar más los errores grandes en semanas de brote.
- **AUC-ROC** para la tarea de clasificación binaria (brote / no brote) con umbral definido epidemiológicamente.
- **Sensibilidad (recall):** Métrica prioritaria desde la perspectiva de salud pública — es más costoso no detectar un brote que generar una falsa alarma.
- **Anticipación promedio (semanas):** Cuántas semanas antes logra detectar el modelo un brote que efectivamente ocurrió.

### 8.6 Fase 6 — Despliegue

Demo local con Docker Compose, PostgreSQL local y ejecucion en laptop. No requiere nube para la hackaton. Documentacion completa de arquitectura, APIs y manual de usuario para secretarias de salud.

## 9. Guía Epidemiológica de Enfermedades Priorizadas

Para que el asistente conversacional (RAG) de ECOS responda con precisión, se ha consolidado la siguiente base de conocimientos técnica sobre las enfermedades monitoreadas.

### 9.1 Dengue (Virus del Dengue - DENV)
*   **Causas:** Virus de la familia *Flaviviridae*. Existen 4 serotipos (DENV-1, DENV-2, DENV-3, DENV-4). La infección por un serotipo no protege contra los otros.
*   **Medio de Contagio:** Picadura del mosquito hembra *Aedes aegypti* o *Aedes albopictus* infectado. No se transmite de persona a persona.
*   **Síntomas Clásicos:** Fiebre alta (40°C/104°F), dolor de cabeza severo, dolor detrás de los ojos, dolores musculares y articulares, náuseas, vómitos, agrandamiento de ganglios linfáticos y sarpullido.
*   **Signos de Alarma (Dengue Grave):** Dolor abdominal intenso, vómitos persistentes, respiración acelerada, sangrado de encías o nariz, fatiga, agitación, presencia de sangre en el vómito o heces.
*   **Periodo de Incubación:** 4 a 10 días después de la picadura.

### 9.2 Chikungunya (Virus Chikungunya - CHIKV)
*   **Causas:** Virus de la familia *Togaviridae*.
*   **Medio de Contagio:** Picadura de mosquitos *Aedes aegypti* y *Aedes albopictus*.
*   **Síntomas:** Aparición súbita de fiebre alta y **dolor articular intenso**, a menudo debilitante (la palabra "chikungunya" significa "doblarse" en lengua makonde). También incluye dolor muscular, dolor de cabeza, náuseas, fatiga y erupciones cutáneas.
*   **Diferenciador:** A diferencia del dengue, el dolor articular es mucho más pronunciado y puede persistir por meses o años (fase crónica).

### 9.3 Zika (Virus Zika - ZIKV)
*   **Causas:** Virus de la familia *Flaviviridae*.
*   **Medio de Contagio:** Principalmente picadura de mosquitos *Aedes*. También se transmite por **vía sexual**, de madre a hijo durante el embarazo (transmisión vertical) y por transfusiones sanguíneas.
*   **Síntomas:** Fiebre leve, sarpullido, conjuntivitis (ojos rojos sin secreción), dolor muscular y articular, malestar general y dolor de cabeza. Muchos casos son asintomáticos.
*   **Complicaciones Graves:** Vinculado al síndrome de Guillain-Barré y, en mujeres embarazadas, causante de microcefalia y otras malformaciones congénitas en el feto.

### 9.4 Malaria (Paludismo)
*   **Causas:** Parásitos del género *Plasmodium*. En Colombia predominan *P. vivax* y *P. falciparum* (este último es el más peligroso).
*   **Medio de Contagio:** Picadura de la hembra del mosquito *Anopheles* infectada. El mosquito pica principalmente entre el anochecer y el amanecer.
*   **Síntomas:** Ciclos de fiebre, escalofríos, sudoración, dolor de cabeza, náuseas, vómitos y dolor muscular.
*   **Complicaciones:** Anemia grave, dificultad respiratoria, falla orgánica y malaria cerebral (especialmente por *P. falciparum*). Es una emergencia médica.

---

## 10. Protocolos de Prevención y Planes de Acción

### 10.1 Medidas de Prevención (Control de Vectores)
1.  **Eliminación de Criaderos:** Lavar y cepillar tanques y albercas cada 8 días. Tapar recipientes que almacenen agua. Eliminar objetos inservibles que acumulen agua lluvia (llantas, botellas, latas).
2.  **Protección Personal:** Uso de repelentes (DEET o IR3535), ropa de manga larga y pantalones, uso de toldillos (mosquiteros) tratados con insecticida al dormir.
3.  **Barreras Físicas:** Instalación de mallas/animes en puertas y ventanas.

### 10.2 Plan de Acción Frente al Contagio (Nivel Individual)
*   **Búsqueda de Atención:** Acudir inmediatamente al centro de salud más cercano ante síntomas febriles en zonas de riesgo.
*   **No Automedicación:** **¡IMPORTANTE!** No tomar aspirina, ibuprofeno ni otros antiinflamatorios no esteroideos (AINEs) si se sospecha de dengue, ya que aumentan el riesgo de hemorragia. Solo se recomienda acetaminofén/paracetamol bajo guía médica.
*   **Hidratación:** Aumentar la ingesta de líquidos (suero oral, jugos, agua).
*   **Aislamiento del Vector:** El paciente enfermo debe dormir bajo toldillo para evitar que mosquitos sanos lo piquen, se infecten y propaguen el virus a su familia o vecinos.

### 10.3 Plan de Acción Frente a un Brote Inminente (Nivel Institucional/Comunitario)
1.  **Activación de Alerta Temprana:** ECOS notifica a la Secretaría de Salud departamental y municipal.
2.  **Intensificación de Vigilancia:** Realizar búsqueda activa de casos casa por casa y en centros de salud.
3.  **Control Químico:** Programar jornadas de fumigación espacial y motomochila en las zonas de mayor riesgo predicho por ECOS.
4.  **Movilización Social:** Realizar jornadas de "limpiatón" comunitaria para eliminar criaderos masivamente.
5.  **Refuerzo Hospitalario:** Garantizar disponibilidad de camas, insumos de hidratación (líquidos IV) y personal capacitado en el protocolo de manejo clínico de arbovirosis.
6.  **Comunicación de Riesgo:** Emisión de boletines radiales y prensa local instando a la comunidad a usar toldillos y eliminar aguas estancadas.

---

## 11. Criterios de Evaluación y Puntuación Estimada

| Criterio | Puntos máximos | Estimado ECOS | Justificación |
|---|---|---|---|
| Innovación y creatividad | 15 | 13-15 | Scraping de Google Trends + RAG conversacional + señales de medios. Diferencial claro frente a proyectos de análisis descriptivo puro. |
| Uso de datos abiertos | 20 | 18-20 | 6 datasets de datos.gov.co, incluyendo el histórico SIVIGILA de 15 años. Alineado con Hoja de Ruta Sectorial de Salud 2025-2026. |
| Análisis y rigor técnico | 15 | 13-15 | PySpark + CRISP-ML + validación temporal walk-forward + SHAP. Documentación completa de metodología. |
| Uso de tecnologías emergentes — IA | 20 | 18-20 | Predictivo (XGBoost + Prophet) + generativo (RAG con LLaMA 3) + explicabilidad (SHAP). Cubre múltiples técnicas de frontera. |
| Impacto y escalabilidad | 20 | 17-20 | Impacto directo en toma de decisiones de MinSalud. Diseñado para integración con data lakes institucionales. Replicable a otras enfermedades y países. |
| Diseño, comunicación y usabilidad | 10 | 8-10 | Dashboard interactivo, chat en lenguaje natural, mapas de calor, reportes PDF automáticos. |
| **Total estimado** | **100** | **87–100** | |

---

## 12. Impacto Esperado

### 12.1 Impacto en salud pública

- Reducción del rezago en alertas epidemiológicas de 2 a 4 semanas a cero en los departamentos priorizados.
- Optimización de la distribución de recursos de respuesta (fumigación, brigadas de salud, insumos hospitalarios) con semanas de anticipación.
- Estimación conservadora: una reducción del 10% en la tasa de incidencia de dengue representa aproximadamente 50.000 casos anuales menos en Colombia.
- Prevención de muertes evitables en poblaciones vulnerables, especialmente niños menores de 5 años y adultos mayores.

### 12.2 Impacto institucional

- Herramienta directamente utilizable por el INS, el Ministerio de Salud y las 32 secretarías departamentales sin desarrollo adicional.
- Reducción de carga de trabajo en equipos de epidemiología que hoy procesan datos manualmente.
- Fortalecimiento de la cultura de uso de datos abiertos en el sector salud.

### 12.3 Impacto económico

- Ahorro en costos de hospitalización al prevenir casos graves mediante detección temprana.
- Optimización del presupuesto de control vectorial al focalizar las intervenciones en zonas de mayor riesgo predicho.
- Reducción de ausentismo laboral y escolar en regiones afectadas por brotes.

### 12.4 Escalabilidad

- **Horizontal:** El modelo puede extenderse a otros eventos de SIVIGILA: leptospirosis, leishmaniasis, hepatitis A, COVID-19.
- **Vertical:** La arquitectura en Spark y Docker permite escalar al volumen completo del data lake del INS con mínimos cambios.
- **Regional:** El modelo puede replicarse en otros países de América Latina con sistemas similares de vigilancia epidemiológica (Peru, Ecuador, Brasil).
- **Institucional:** Diseñado para ser transferido al INS o MinSalud como herramienta de uso continuo más allá del concurso.

---

## 13. Alineación con la Convocatoria

| Requisito de la convocatoria | Cumplimiento ECOS |
|---|---|
| Uso de datos de datos.gov.co | ✅ 6 datasets, incluyendo SIVIGILA histórico. |
| Componente de IA | ✅ Modelos predictivos + RAG + clasificación de texto. |
| Estándares CRISP-ML | ✅ Estructura de repositorio y documentación completa. |
| Código abierto en repositorio público | ✅ GitHub público, licencia MIT. |
| Dashboard / aplicación web accesible | ✅ Plotly Dash + API REST documentada. |
| Equipo multidisciplinario con al menos una mujer | ✅ 4 integrantes, perfil diverso. |
| Publicación en herramientas.datos.gov.co/usos | ✅ Programado antes de la fase de evaluación. |
| Reto de la convocatoria | ✅ Reto 1 — Salud y Bienestar. |
| Hoja de Ruta Nacional 2025-2026 | ✅ Alineado con Hoja de Ruta Sectorial de Salud. |
| Cobertura territorial amplia | ✅ Nacional con énfasis en regiones vulnerables. |

---

## 14. Protocolo de Ética y Privacidad

- **Datos personales:** ECOS no procesa datos identificables de pacientes. Todos los datasets utilizados son datos agregados a nivel municipal o departamental, sin información individual de salud.
- **Scraping ético:** El módulo de scraping respeta los archivos `robots.txt` de todos los medios monitoreados. Solo accede a contenido públicamente indexado. No recolecta información personal.
- **Google Trends:** Se utilizan únicamente las tendencias agregadas y completamente anonimizadas que Google publica de forma pública. No se accede a datos de usuarios individuales.
- **Propiedad intelectual:** Todo el código es de autoría original del equipo. Las librerías utilizadas son de código abierto con licencias compatibles (MIT, Apache 2.0). Los datos utilizados son de dominio público (licencia abierta en datos.gov.co).
- **Transparencia algorítmica:** Los modelos son explicables mediante SHAP. No se toman decisiones automatizadas sobre individuos. El sistema es una herramienta de apoyo a la decisión humana, no un sustituto de la misma.
- **Reproducibilidad:** Todo el código, datos procesados y parámetros de modelo se publican en el repositorio para verificación independiente.

---

## 15. Repositorio y Publicación

- **Repositorio GitHub:** [URL a completar al momento de creación]
- **Registro en datos.gov.co:** https://herramientas.datos.gov.co/usos
- **Licencia:** MIT (código abierto, reutilizable por entidades públicas sin restricciones).
- **Demo local:** Ejecucion en laptop con servicios en localhost.
- **Documentación:** README completo en español con instrucciones de instalación, uso y descripción de cada módulo.

---

*ECOS — Early Control and Observation System*  
*Concurso Datos al Ecosistema 2026: IA para Colombia*  
*Desarrollado con datos abiertos de datos.gov.co*