# ECOS — Early Control and Observation System

## Plataforma Nacional de Alerta Temprana para Enfermedades de Alto Impacto en Colombia

> **Concurso:** Datos al Ecosistema 2026 — IA para Colombia
> **Categoría:** Innovación Social / Inteligencia Artificial Aplicada a Datos Abiertos
> **Reto:** Reto 1 — Salud y Bienestar
> **Cobertura:** Nacional · 32 departamentos · todos los municipios de Colombia

---

## 0. Índice de contenido

1. Resumen ejecutivo
2. Problema y oportunidad
3. Arquitectura general del sistema
4. Fuentes de datos y pipeline de ingesta
5. Modelos de IA y metodología CRISP-ML
6. Stack tecnológico detallado
7. **Guía visual de dashboards** ← _El corazón del proyecto_
   - Dashboard 1 — Centro de Comando Nacional (Plotly Dash)
   - Dashboard 2 — Inteligencia de Señales Tempranas (Next.js)
   - Dashboard 3 — Mapa de Calor Movilidad × Enfermedad (Plotly Dash + Kepler.gl)
   - Dashboard 4 — Monitor de Noticias Scrapeadas (Next.js)
   - Dashboard 5 — RAG Conversacional (Next.js)
8. Limitaciones técnicas reales y cómo las manejamos
9. Métricas de evaluación
10. Impacto esperado
11. Plan de ejecución y entregas
12. Criterios del concurso y puntuación estimada
13. Ética y privacidad

---

## 1. Resumen Ejecutivo

**ECOS** (Early Control and Observation System) es una plataforma de inteligencia epidemiológica que combina datos abiertos, scraping automatizado, modelos predictivos con IA y visualización avanzada para detectar brotes de dengue, chikungunya, zika y malaria **entre 2 y 4 semanas antes** de que sean reportados oficialmente por SIVIGILA.

La propuesta técnica se articula en tres capas que se comunican en tiempo real:

```
┌─────────────────────────────────────────────────────────────┐
│  WEB PORTAL  ·  Next.js 15 + Tailwind                       │
│  Monitor de Noticias · Google Trends Alerts · Chat RAG      │
├─────────────────────────────────────────────────────────────┤
│  DASHBOARDS  ·  Plotly Dash (100% Python · 100% gratuito)  │
│  Centro de Comando · Movilidad × Enfermedad · Tendencias    │
├─────────────────────────────────────────────────────────────┤
│  BACKEND  ·  FastAPI + PySpark + XGBoost + Prophet          │
│  Pipeline de datos · Modelos ML · API REST · Alertas        │
└─────────────────────────────────────────────────────────────┘
```

**¿Qué nos diferencia de otros proyectos del concurso?**

| Diferenciador                            | Descripción                                                                                                                                        |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🔴 Señales 2–3 semanas antes             | Google Trends por departamento + noticias scrapeadas en tiempo real                                                                                |
| 🟠 Correlación movilidad-enfermedad      | Mapa de calor OD (origen-destino) que muestra cómo los flujos de pasajeros propagan brotes                                                         |
| 🟡 Monitor de noticias vivo              | Feed con NLP que clasifica y georreferencia noticias epidemiológicas de los últimos 30 días                                                        |
| 🟢 RAG conversacional                    | Asistente que responde en lenguaje natural citando las fuentes y explicando las variables SHAP                                                     |
| 🔵 Explicabilidad SHAP                   | Cada predicción muestra cuánto contribuyó cada variable (clima, movilidad, tendencias)                                                             |
| 🟣 Plotly Dash + Next.js (100% gratuito) | Stack de visualización completamente open-source, embebible, sin licencias ni servicios de pago. Demo reproducible en cualquier laptop con Docker. |

---

## 2. Problema y Oportunidad

### 2.1 El rezago estructural de SIVIGILA

```
CASO OCURRE → Paciente va al médico → Notificación al municipio →
Consolidación departamental → Alerta SIVIGILA → ACCIÓN
   ↑_____________________ 2 a 4 SEMANAS _______________________↑
```

Cuando el sistema de vigilancia emite una alerta, el brote ya está en **fase de expansión comunitaria**. ECOS invierte este flujo: las señales tempranas (búsquedas en Google, noticias regionales, clima anómalo) llegan al modelo antes que los casos al hospital.

### 2.2 Por qué ahora

Colombia tiene más de 15 años de datos epidemiológicos abiertos en datos.gov.co y uno de los portales de datos más completos de América Latina. Al mismo tiempo, la adopción de herramientas de IA generativa y modelos predictivos en el sector salud aún es incipiente. **Esta es la ventana.**

### 2.3 Impacto cuantificable

- Colombia reportó **+498.000 casos de dengue** en el último ciclo epidémico.
- Una reducción del 10% en incidencia por detección oportuna = **~50.000 casos menos**.
- El costo promedio de hospitalización por dengue grave oscila entre COP $2,5 y $8 millones.
- **Impacto fiscal estimado:** +COP $125.000 millones anuales en ahorro hospitalario.

---

## 3. Arquitectura General del Sistema

```
╔═══════════════════════════════════════════════════════════════════╗
║  FUENTES DE DATOS                                                 ║
║                                                                   ║
║  [datos.gov.co]        [Google Trends]    [RSS Medios]            ║
║  SIVIGILA histórico    pytrends           feedparser              ║
║  Chikungunya events    (dept level)       BeautifulSoup           ║
║  IDEAM normales        semanal            pdfplumber (INS PDF)    ║
║  Coberturas vacunas    ─────────────────► Open-Meteo API          ║
║  RIPS atenciones                                                   ║
║  Movilidad OD                                                     ║
╚══════════════════╦════════════════════════════════════════════════╝
                   ║
                   ▼  PySpark ETL  (limpieza · normalización DANE · join semanal)
╔══════════════════╩════════════════════════════════════════════════╗
║  DATA LAKE  ·  Parquet + PostgreSQL local                         ║
║  /data/raw   /data/processed   /data/features                     ║
╚══════════════════╦════════════════════════════════════════════════╝
                   ║
          ┌────────┴────────┐
          ▼                 ▼
   [Prophet]          [XGBoost]
   series temporales  variables exógenas
   estacionalidad     clima·movilidad·trends
          └────────┬────────┘
                   ▼
              [SHAP explainer]
              contribución por variable
                   ║
                   ▼
╔══════════════════╩════════════════════════════════════════════════╗
║  FastAPI  ·  REST endpoints                                       ║
║  /predict  /alerts  /news  /trends  /dashboard-data  /chat        ║
╚══════════════════╦════════════════════════════════════════════════╝
                   ║
       ┌───────────┼───────────┐
       ▼           ▼           ▼
  [Power BI]   [Next.js]   [LangChain]
  5 dashboards  Web portal   RAG + Groq
  embedded      noticias      LLaMA 3
                chat
```

---

## 4. Fuentes de Datos y Pipeline de Ingesta

### 4.1 Seis datasets de datos.gov.co

| #   | Dataset                       | Entidad       | Variables clave                | Rol en el modelo                      |
| --- | ----------------------------- | ------------- | ------------------------------ | ------------------------------------- |
| 1   | SIVIGILA 2007–2022            | INS           | casos/semana/municipio/evento  | Variable objetivo (Y) — ground truth  |
| 2   | Chikungunya detallado         | INS           | inicio síntomas, clasificación | Calibración para chikungunya          |
| 3   | Normales climatológicas IDEAM | IDEAM         | temp, humedad, precipitación   | Features climáticas baseline          |
| 4   | Coberturas de vacunación      | MinSalud      | % cobertura/dpto/biológico     | Factor de susceptibilidad poblacional |
| 5   | RIPS atenciones               | MinSalud      | diagnóstico CIE-10, atenciones | Señal paralela al SIVIGILA            |
| 6   | Movilidad OD intermunicipal   | MinTransporte | origen-destino, pasajeros      | Difusión geográfica del riesgo        |

### 4.2 Señales tempranas scrapeadas (el diferencial competitivo)

#### A — Google Trends via `pytrends` — Enfoque híbrido (nacional + departamental selectivo)

**Decisión de diseño — por qué no tratamos Google Trends como fuente primaria geolocalizada:**

Google Trends tiene sesgos estructurales que lo hacen poco confiable como señal epidemiológica a nivel granular en Colombia:

| Sesgo                                     | Impacto en ECOS                                                                                                                                                     |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Brecha digital**                        | Chocó, Vaupés, Guainía, Vichada — donde más malaria hay — tienen baja penetración de internet. Los que más sufren la enfermedad son los que menos buscan en Google. |
| **Sesgo urbano**                          | Bogotá, Medellín y Cali pesan desproporcionadamente. Un spike nacional puede ser bogotanos leyendo noticias, no casos reales en zonas endémicas.                    |
| **Índice relativo, no absoluto**          | El 0–100 es relativo al propio período consultado. Un 80 en Vaupés no es comparable con un 80 en Antioquia.                                                         |
| **Datos insuficientes en dptos pequeños** | Google devuelve vacío si el volumen de búsquedas es bajo — precisamente en los departamentos más vulnerables.                                                       |
| **Señal reactiva, no siempre predictiva** | Cuando el INS o los medios emiten una alerta, la gente busca en Google masivamente. La señal puede estar siguiendo la noticia, no precediendo al brote.             |

**Estrategia híbrida adoptada:**

```
NIVEL NACIONAL (siempre activo)
───────────────────────────────
· Índice nacional Colombia como termómetro de atención pública al tema
· Comparable semana a semana en el mismo período histórico
· Señal de "estado de alerta social" ante una enfermedad
· Peso en el modelo: BAJO (5–8% del feature importance)
· Uso: corroboración, contexto, no predicción directa

NIVEL DEPARTAMENTAL (selectivo — solo donde hay volumen)
─────────────────────────────────────────────────────────
· Solo para departamentos con cobertura de internet >40%
  y volumen de búsquedas suficiente (Google no devuelve vacío):
  Antioquia, Valle del Cauca, Atlántico, Cundinamarca,
  Santander, Bolívar, Nariño (Pasto urbano), Huila, Tolima
· Si pytrends devuelve DataFrame vacío → se descarta, no se imputa
· Peso en el modelo: MUY BAJO (2–4% del feature importance)
· Uso: señal de apoyo en predicciones para esos dptos específicos

DESCARTADO:
  Vaupés, Guainía, Vichada, Amazonas, Chocó rural, San Andrés
  → La predicción para estas zonas viene de clima + SIVIGILA + RIPS
```

```python
from pytrends.request import TrendReq
import pandas as pd
import time

KEYWORDS = [
    "dengue síntomas", "fiebre dengue", "mosquito dengue",
    "chikungunya Colombia", "malaria síntomas",
    "zika síntomas", "fiebre alta mosquito"
]

# Departamentos con cobertura de internet suficiente para datos válidos
DPTOS_CON_VOLUMEN = {
    "Antioquia":       "CO-ANT",
    "Valle del Cauca": "CO-VAC",
    "Atlántico":       "CO-ATL",
    "Cundinamarca":    "CO-CUN",
    "Santander":       "CO-SAN",
    "Bolívar":         "CO-BOL",
    "Nariño":          "CO-NAR",
    "Huila":           "CO-HUI",
    "Tolima":          "CO-TOL",
}

def fetch_trends_nacional(keyword, timeframe="today 12-m"):
    """
    Señal nacional Colombia — siempre disponible, siempre válida.
    Devuelve serie semanal relativa (0-100) para Colombia completo.
    """
    pytrends = TrendReq(hl='es-CO', tz=300)
    pytrends.build_payload([keyword], geo="CO", timeframe=timeframe)
    time.sleep(1.5)
    df = pytrends.interest_over_time()
    if df.empty:
        return pd.DataFrame()
    df["nivel"] = "nacional"
    df["keyword"] = keyword
    return df[[keyword, "nivel", "keyword"]].rename(columns={keyword: "trend_index"})

def fetch_trends_departamental(keyword, geo_code, timeframe="today 12-m"):
    """
    Señal departamental — solo para dptos con volumen suficiente.
    Si Google devuelve vacío, se descarta (no se imputa).
    """
    pytrends = TrendReq(hl='es-CO', tz=300)
    pytrends.build_payload([keyword], geo=geo_code, timeframe=timeframe)
    time.sleep(1.5)
    df = pytrends.interest_over_time()

    if df.empty or df[keyword].sum() == 0:
        # Datos insuficientes — se registra como ausente, NO se imputa
        return None

    df["nivel"] = "departamental"
    df["geo"] = geo_code
    df["keyword"] = keyword
    return df[[keyword, "nivel", "geo", "keyword"]].rename(columns={keyword: "trend_index"})

def classify_trend_alert(current_index, historical_series):
    """
    Clasifica un spike estadísticamente vs. la media histórica del mismo geo/keyword.
    Se aplica igual para nacional y departamental.
    """
    mu = historical_series.mean()
    sigma = historical_series.std()
    if sigma == 0:
        return "VERDE", "varianza cero — serie plana"
    z_score = (current_index - mu) / sigma

    if z_score >= 3.0:
        return "ROJA", f"+{z_score:.1f} SD — atención pública muy elevada"
    elif z_score >= 2.0:
        return "AMARILLA", f"+{z_score:.1f} SD — atención pública elevada"
    else:
        return "VERDE", f"{z_score:.1f} SD — normal"
```

**Términos monitoreados:**

```
"dengue síntomas"       · "fiebre dengue"        · "mosquito dengue"
"chikungunya Colombia"  · "malaria Colombia"      · "zika síntomas"
"fiebre alta mosquito"  · "dolor articulaciones fiebre"
"picadura mosquito"     · "hospital dengue"       · "brote dengue"
```

**Cómo se visualiza (ver Dashboard 2):** El índice nacional va en la barra de contexto superior. El departamental solo aparece en los 9 departamentos válidos, con una etiqueta de cobertura que indica cuándo el dato no está disponible para el departamento consultado.

#### B — RSS + Scraping de medios regionales

```python
FUENTES_RSS = {
    # Nacionales
    "El Tiempo":     "https://www.eltiempo.com/rss/salud.xml",
    "Noticias RCN":  "https://noticias.canalrcn.com/rss/salud",
    "Caracol Radio": "https://caracol.com.co/rss/salud.xml",
    # Regionales
    "El Heraldo":    "https://www.elheraldo.co/rss.xml",         # Caribe
    "El Colombiano": "https://www.elcolombiano.com/rss.xml",     # Antioquia
    "La Opinión":    "https://www.laopinion.com.co/rss.xml",     # Nariño
    "Diario Huila":  "https://diariodelhuila.com/rss.xml",       # Huila
    # Oficial
    "INS Boletines": "https://www.ins.gov.co/buscador-eventos",  # PDF semanal
}

TERMINOS_ALERTA = [
    "dengue", "chikungunya", "malaria", "zika",
    "brote", "alerta sanitaria", "epidemia",
    "mosquito", "vector", "casos confirmados",
    "secretaría de salud", "emergencia sanitaria"
]
```

**Pipeline de clasificación de noticias:**

```
Artículo RSS
     ↓
[TF-IDF + Regresión Logística]  → ¿Es epidemiológico? (sí/no)
     ↓ (si sí)
[NER con spaCy es_core_news_sm] → Extrae municipio/departamento mencionado
     ↓
[Clasificador de enfermedad]    → ¿Cuál enfermedad? (dengue/chiku/malaria/zika/otro)
     ↓
[Sentiment + urgencia]          → Score de alerta (0-1)
     ↓
PostgreSQL  →  API  →  Dashboard de Noticias
```

#### C — Boletines INS (PDF automático)

```python
import requests, pdfplumber, re

def parse_boletin_ins(url):
    r = requests.get(url, timeout=30)
    with pdfplumber.open(io.BytesIO(r.content)) as pdf:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    # Extrae alertas por departamento con regex + patrones del INS
    alertas = re.findall(
        r"(Alerta|Umbral|Brote)[^\n]*\n([A-ZÁÉÍÓÚ][a-záéíóú]+)",
        text
    )
    return alertas
```

#### D — Open-Meteo (clima actual sin costo)

```python
import httpx

def fetch_weather_weekly(lat, lon, start_date, end_date):
    """Sin API key. Cobertura global. Gratuito."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "daily": ["temperature_2m_max","temperature_2m_min","precipitation_sum","relative_humidity_2m_mean"],
        "start_date": start_date, "end_date": end_date,
        "timezone": "America/Bogota"
    }
    r = httpx.get(url, params=params)
    return r.json()
```

---

## 5. Modelos de IA y Metodología CRISP-ML

### 5.1 Estructura del repositorio (CRISP-ML compliant)

```
ecos/
├── crisp-ml/
│   ├── 01-business-understanding.md      ← Problema, usuario final, KPIs
│   ├── 02-data-understanding.ipynb       ← EDA de los 6 datasets
│   ├── 03-data-preparation.ipynb         ← ETL con PySpark
│   ├── 04-modeling.ipynb                 ← Prophet + XGBoost + tuning
│   ├── 05-evaluation.ipynb               ← Walk-forward validation + SHAP
│   └── 06-deployment.md                  ← Docker, API, manual de usuario
├── data/
│   ├── raw/                              ← CSVs originales de datos.gov.co
│   ├── processed/                        ← Parquet por municipio/semana
│   └── features/                         ← Feature store listo para ML
├── src/
│   ├── api/                              ← FastAPI endpoints
│   ├── etl/                              ← PySpark pipelines
│   ├── models/                           ← XGBoost + Prophet + SHAP
│   ├── scraping/                         ← pytrends + feedparser + pdfplumber
│   ├── rag/                              ← LangChain + Groq (LLaMA 3)
│   └── alerts/                           ← Motor de alertas + email
├── powerbi/                              ← Archivos .pbix exportados
├── web/                                  ← Next.js 15 portal
│   ├── app/
│   │   ├── page.tsx                      ← Landing / overview
│   │   ├── noticias/                     ← Monitor de noticias
│   │   ├── tendencias/                   ← Google Trends alerts
│   │   ├── chat/                         ← RAG conversacional
│   │   └── alertas/                      ← Sistema de alertas activas
│   └── components/
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

### 5.2 Modelo predictivo — Prophet + XGBoost en pipeline

**Estrategia híbrida:**

```
PROPHET                          XGBOOST
────────                         ───────
· Serie temporal base            · Residuales de Prophet
· Estacionalidad anual           · Variables exógenas:
· Estacionalidad semanal           - Temperatura / Humedad
· Festivos colombianos             - Precipitación (IDEAM + Open-Meteo)
· Tendencia a largo plazo          - Google Trends (índice dpto, semana t-1)
                                   - Menciones en medios (conteo, semana t-1)
                                   - Movilidad OD (pasajeros, semana t-2)
                                   - Cobertura vacunación (anual, dpto)
                                   - RIPS atenciones CIE-10 (semana t-1)
                                   - Dummy: periodo COVID (2020-2021)

Prophet_pred(t) + XGBoost_residual(exog_t) = ECOS_pred(t)
```

**Validación temporal (walk-forward):**

```
──────────────────────────────────────────────────────
ENTRENAMIENTO          TEST        PREDICCIÓN
2007──────────2020 │ 2021──2022 │ 2023──2025►
                   │            │
2007──────────2021 │ 2022       │ 2023►
                   │            │
2007──────────2022 │ 2023       │ 2024►
──────────────────────────────────────────────────────
NO se mezclan datos futuros con pasado (no data leakage)
```

### 5.3 Explicabilidad — SHAP

Cada predicción expone en el dashboard qué variables la explican:

```
Predicción: RIESGO ALTO de brote en Nariño — semana 18 (2026)
─────────────────────────────────────────────────────────────
Variable                    Contribución (SHAP value)
─────────────────────────────────────────────────────────────
Humedad relativa (87%)        ████████████ +2.4 (↑ riesgo)
Temperatura (28°C)            ████████     +1.8 (↑ riesgo)
Trend "dengue síntomas"       ██████       +1.3 (↑ riesgo)
Menciones en medios (8)       █████        +1.1 (↑ riesgo)
Cobertura vacunación (61%)    ███          +0.7 (↑ riesgo)
Movilidad Pasto-Cali          ██           +0.5 (↑ riesgo)
Precipitación (120mm)         ██           +0.4 (↑ riesgo)
Casos RIPS semana anterior    ─            +0.2 (neutral)
─────────────────────────────────────────────────────────────
Predicción: 87 casos · Prob. brote: 0.83
```

### 5.4 RAG — Asistente conversacional

```
Pregunta usuario
       ↓
[Embedding con sentence-transformers]
       ↓
[Búsqueda vectorial ChromaDB]  ←── Documentos indexados:
       ↓                             · Resultados del modelo (JSON)
[Prompt enriquecido]                 · Boletines INS (texto PDF)
       ↓                             · Noticias clasificadas (últimas 4 sem)
[Groq API — LLaMA 3.1 70B]          · Histórico SIVIGILA resumido
       ↓
Respuesta con fuentes citadas + datos SHAP + recomendación de acción
```

**Ejemplos de preguntas respondibles:**

- _"¿Cuál es el riesgo de dengue en Nariño las próximas 3 semanas?"_
- _"¿Qué municipios de la Costa tienen mayor riesgo de malaria este mes?"_
- _"¿Qué noticias recientes hay sobre brotes en el Pacífico?"_
- _"¿Cómo afecta la movilidad desde Medellín al riesgo en el Eje Cafetero?"_
- _"¿Cuántos casos de chikungunya hubo en 2019 en el Valle?"_

---

## 6. Stack Tecnológico

| Capa                     | Tecnología                           | Por qué                                                                                                 | Costo                     |
| ------------------------ | ------------------------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------- |
| ETL y procesamiento      | PySpark 3.5                          | Maneja millones de registros SIVIGILA sin cuello de botella                                             | ✅ Gratuito               |
| Modelo series temporales | Prophet 1.1 (Meta)                   | Estacionalidad múltiple + festivos colombianos integrados                                               | ✅ Gratuito               |
| Modelo tabular           | XGBoost 2.0                          | Mejor desempeño en datos tabulares, manejo nativo de nulos                                              | ✅ Gratuito               |
| Explicabilidad           | SHAP 0.45                            | Gráficos listos para decisores no técnicos                                                              | ✅ Gratuito               |
| Backend API              | FastAPI 0.111 + Python 3.11          | Alto rendimiento, Swagger automático, async                                                             | ✅ Gratuito               |
| Scraping                 | pytrends + feedparser + pdfplumber   | Especializadas, sin dependencias pesadas                                                                | ✅ Gratuito               |
| NLP noticias             | spaCy es_core_news_sm + scikit-learn | NER en español + clasificador liviano                                                                   | ✅ Gratuito               |
| RAG                      | LangChain 0.2 + ChromaDB + Groq      | Groq free tier: ~30 RPM / 6000 TPM — suficiente para demo y uso moderado. Limitación documentada en §8. | ✅ Gratuito (con límites) |
| Dashboard epidemiológico | **Plotly Dash 2.x**                  | 100% Python, 100% open-source, sin licencias, embebible                                                 | ✅ Gratuito               |
| Portal web               | Next.js 15 + Tailwind + shadcn/ui    | SSR, App Router, despliegue en Vercel o Docker                                                          | ✅ Gratuito               |
| Mapas de flujo OD        | Kepler.gl (MIT License)              | Arcos origen-destino, sin costo                                                                         | ✅ Gratuito               |
| Gráficos web             | Recharts + D3.js                     | Integración nativa con React                                                                            | ✅ Gratuito               |
| Infraestructura          | Docker + Docker Compose              | Demo local reproducible, sin nube requerida                                                             | ✅ Gratuito               |
| Persistencia             | PostgreSQL 16 + Parquet              | Operacional + histórico eficiente                                                                       | ✅ Gratuito               |
| CI/CD                    | GitHub Actions                       | Tests automáticos, lint, despliegue                                                                     | ✅ Gratuito               |
| Clima actual             | Open-Meteo API                       | Sin API key, sin costo, cobertura global                                                                | ✅ Gratuito               |

> **Costo total del stack:** $0. Todas las herramientas son open-source o tienen tier gratuito suficiente para el concurso y un despliegue institucional de baja concurrencia. La única limitación real es Groq (30 requests/minuto en free tier), documentada y mitigable con caché.

---

## 7. Guía Visual de Dashboards

> Esta sección describe cada dashboard con suficiente detalle técnico y visual para que el equipo de diseño e implementación lo construya sin ambigüedad.

---

### Dashboard 1 — Centro de Comando Nacional

**Herramienta:** Plotly Dash 2.x (Python · open-source · gratuito) — servido por FastAPI, embebido en Next.js via iframe
**Audiencia:** Ministerio de Salud, INS, secretarías departamentales
**Actualización:** Semanal automática (pipeline corre cada lunes)

```
┌─────────────────────────────────────────────────────────────────────┐
│  ECOS — Centro de Comando Nacional              Semana 18 · 2026    │
│  🔴 3 alertas activas  🟡 7 en vigilancia  🟢 22 en verde          │
├──────────────┬────────────────────────────┬────────────────────────┤
│ KPI CARDS    │  MAPA NACIONAL (choropleth) │  PANEL ALERTAS         │
│              │                            │                        │
│ 🦟 Dengue    │  [Colombia por deptos]     │  🔴 Nariño · Dengue   │
│  +18% vs sw  │  Verde → Amarillo → Rojo   │  prob: 0.87 · sem 18  │
│              │  por probabilidad de brote │                        │
│ 🦟 Chiku     │  Enfermedad: [Dengue ▼]   │  🔴 Chocó · Malaria   │
│  Estable     │  Horizonte: [2 sem ▼]      │  prob: 0.81 · sem 19  │
│              │                            │                        │
│ 🦟 Malaria   │  Click en dpto → drill     │  🟡 Atlántico · Dengue│
│  -5% vs sw   │  down a municipios         │  prob: 0.65 · sem 18  │
│              │                            │                        │
│ 🦟 Zika      │                            │  [Ver todas ↓]        │
│  Sin alerta  │                            │                        │
├──────────────┴────────────────────────────┴────────────────────────┤
│  SERIE TEMPORAL — Predicción vs. Casos Reportados                   │
│                                                                     │
│  Casos  │                                    ●●●●  Predicción       │
│  400 ─  │                              ●●●●       ──── Reportados   │
│  300 ─  │                        ●●●●●            ░░░░ IC 90%       │
│  200 ─  │        ●●●●●●●●●●●●●●●●                                  │
│  100 ─  │●●●●●●●●                                                   │
│         └──────────────────────────────────────────────────►        │
│           2024-S01            2025-S01            2026-S18 (HOY)    │
│         [Departamento: Nariño ▼] [Enfermedad: Dengue ▼]            │
├─────────────────────────────────────────────────────────────────────┤
│  SHAP — Variables que explican el riesgo actual en Nariño           │
│                                                                     │
│  Humedad (87%)        ████████████████████████████  +2.4           │
│  Temperatura (28°C)   ████████████████████         +1.8            │
│  Casos sem. anterior  ███████████████              +1.5            │
│  Menciones medios (8) ████████████                 +1.1            │
│  Baja vacunación      ██████                        +0.7           │
│  Movilidad Pasto-Cali ████                          +0.5           │
│  Trends nac. (+2.6SD) ██                            +0.3  ← corroboración │
│  Trends dpto (+3.2SD) █                             +0.2  ← peso reducido │
└─────────────────────────────────────────────────────────────────────┘
```

**Componentes Plotly Dash utilizados:**

- `dcc.Graph` con `go.Choropleth` — mapa coroplético Colombia, escala verde-amarillo-rojo
- `dcc.Graph` con `go.Scatter` + banda de confianza `go.Scatter(fill='tonexty')` — predicción vs. realidad
- `dcc.Graph` con `go.Bar` horizontal — SHAP values por variable
- `html.Div` con KPI cards — contador de alertas activas por enfermedad
- `dcc.Dropdown` — filtros por departamento, enfermedad, horizonte temporal
- `dash_bootstrap_components` — layout responsivo sin CSS custom

**Datos que consume (endpoints FastAPI):**

```
GET /api/v1/predictions?week=18&year=2026&disease=dengue
GET /api/v1/alerts/active
GET /api/v1/shap?dept=nari%C3%B1o&disease=dengue&week=18
GET /api/v1/timeseries?dept=nari%C3%B1o&disease=dengue&start=2024-01
```

---

### Dashboard 2 — Inteligencia de Señales Tempranas (Google Trends)

**Herramienta:** Power BI + sección dedicada en Next.js web (`/tendencias`)
**Audiencia:** Epidemiólogos, equipo de vigilancia del INS
**Actualización:** Semanal (pytrends corre los lunes temprano)

> **Enfoque híbrido — diseño honesto:** Este dashboard implementa una estrategia en dos capas para Google Trends. La capa **nacional** es siempre válida y funciona como termómetro de atención pública. La capa **departamental** solo se activa para los 9 departamentos donde Google reporta volumen de búsquedas suficiente; para los demás (Vaupés, Guainía, Chocó rural, etc.) el panel muestra explícitamente "datos insuficientes" en lugar de valores interpolados. Esto es una decisión técnica consciente: en epidemiología es preferible reconocer un dato ausente que fabricarlo.

```
┌─────────────────────────────────────────────────────────────────────┐
│  ECOS — Monitor de Señales Tempranas (Google Trends)               │
│  Actualizado: lunes 08:00 · Semana 18 · 2026                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ━━ TERMÓMETRO NACIONAL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Atención pública al dengue en Colombia esta semana                 │
│                                                                     │
│  "dengue síntomas"     ████████████████████████████  78/100  🟡   │
│  "fiebre dengue"       ████████████████████          62/100  🟡   │
│  "malaria síntomas"    ████████                       24/100  🟢   │
│  "chikungunya"         ██████                         18/100  🟢   │
│                                                                     │
│  Contexto: índice 78 vs. media histórica 41 → +2.6 SD 🟡           │
│  Interpretación: mayor atención pública que la media, consistente  │
│  con el aumento de casos en SIVIGILA y noticias de la semana.      │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ━━ SEÑAL DEPARTAMENTAL (9 dptos con volumen válido) ━━━━━━━━━━━━  │
│                                                                     │
│  [Choropleth Colombia]                                              │
│  ● Verde/Amarillo/Rojo = spike estadístico vs. histórico dpto      │
│  ▨ Gris rayado = datos insuficientes (Google no reporta volumen)   │
│                                                                     │
│  Keyword: [dengue síntomas ▼]   Período: [últimas 8 semanas ▼]    │
│                                                                     │
│  DATOS VÁLIDOS              │  DATOS INSUFICIENTES                 │
│  ──────────────────────     │  ─────────────────────────           │
│  Nariño        +3.2 SD 🔴  │  Vaupés        ▨ sin volumen        │
│  Atlántico     +2.1 SD 🟡  │  Guainía       ▨ sin volumen        │
│  Valle         +1.6 SD 🟢  │  Vichada       ▨ sin volumen        │
│  Antioquia     +1.2 SD 🟢  │  Amazonas      ▨ sin volumen        │
│  Santander     +0.8 SD 🟢  │  Chocó*        ▨ sin volumen        │
│  Bolívar       +0.4 SD 🟢  │  * Predicción de Chocó viene de     │
│  Cundinamarca  +0.3 SD 🟢  │    clima + SIVIGILA + RIPS           │
│  Huila         +0.1 SD 🟢  │                                      │
│  Tolima        −0.2 SD 🟢  │                                      │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  SERIE HISTÓRICA — Corroboración: Trends Nacional vs. Casos SIVIGILA│
│                                                                     │
│  Índice  │  Google Trends (nacional) ────                          │
│   100 ─  │  Casos dengue Colombia ━━━━━                            │
│    80 ─  │                                                         │
│    60 ─  │        ╱╲ Trend sube     ╱╲ Casos suben 2 sem después  │
│    40 ─  │       ╱  ╲              ╱  ╲                           │
│    20 ─  │──────╱    ╲────────────╱    ╲──────────                │
│     0 ─  └──────────────────────────────────────────────►          │
│           S12   S14   S16   S18   S20   S22   S24   S26            │
│                  ↑ Trends anticipa ~2 sem en picos históricos       │
│                    (correlación observada, no garantizada)          │
│                                                                     │
│  ⚠️ Nota metodológica: la correlación Trends–casos es más          │
│  fuerte en departamentos urbanos (Bogotá, Medellín, Cali).         │
│  En zonas rurales endémicas, Trends suele subestimar el brote.     │
└─────────────────────────────────────────────────────────────────────┘
```

**Peso de Google Trends en el modelo predictivo:**

```python
# En XGBoost, el feature importance de Trends se limita explícitamente
# para evitar que sesgos de brecha digital contaminen predicciones
# en zonas rurales donde la señal es débil o inexistente.

FEATURE_WEIGHTS = {
    # Variables climáticas — alta confiabilidad geográfica
    "temperatura_media":          1.0,
    "humedad_relativa":           1.0,
    "precipitacion":              1.0,
    # SIVIGILA histórico — ground truth
    "casos_semana_anterior":      1.0,
    "casos_4sem_anteriores":      1.0,
    # RIPS — señal paralela confiable
    "atenciones_cie10":           0.9,
    # Movilidad — confiable para hubs urbanos
    "pasajeros_entrantes":        0.8,
    # Noticias scrapeadas — cobertura heterogénea pero válida
    "menciones_medios":           0.6,
    # Google Trends nacional — baja ponderación, solo corroboración
    "trend_nacional":             0.3,
    # Google Trends departamental — solo donde hay dato, peso mínimo
    "trend_departamental":        0.15,  # Solo para los 9 dptos válidos
}
```

---

### Dashboard 3 — Mapa de Calor Movilidad × Enfermedad

**Herramienta:** Plotly Dash + Kepler.gl (ambos open-source · gratuitos) — Kepler.gl para los arcos OD, Dash para las tablas y scatter plots
**Audiencia:** Equipos de rastreo de contactos, planificadores de respuesta
**Actualización:** Semanal con datos de movilidad intermunicipal

> Este dashboard responde la pregunta: **¿Cómo se mueven los casos entre municipios a través de la movilidad de pasajeros?**

```
┌─────────────────────────────────────────────────────────────────────┐
│  ECOS — Mapa de Calor: Movilidad × Enfermedad                      │
│  Difusión geográfica del riesgo epidemiológico                      │
├─────────────────────────────────────────────────────────────────────┤
│  VISTA OD (Origen-Destino)                                          │
│                                                                     │
│  [Mapa Colombia con arcos de flujo]                                 │
│                                                                     │
│  ●  Nodo = Municipio/Ciudad hub                                     │
│     Tamaño = Casos activos (ECOS prediction)                        │
│     Color  = Nivel de riesgo (verde → rojo)                         │
│                                                                     │
│  ━━ Arco = Flujo de pasajeros entre municipios                      │
│     Grosor = Volumen de pasajeros/semana                            │
│     Color  = Riesgo exportado (rojo = municipio origen en alerta)   │
│                                                                     │
│  Ejemplo visible:                                                   │
│  Pasto (🔴) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━► Cali (🟡)              │
│  12.000 pasajeros/sem · origen en alerta alta · riesgo exportado    │
│                                                                     │
│  [Filtros: Enfermedad ▼] [Semana ▼] [Riesgo mínimo ▼]             │
├─────────────────────────────────────────────────────────────────────┤
│  MATRIZ DE CORRELACIÓN — Movilidad vs. Incidencia                   │
│                                                                     │
│  Correlación de Pearson:                                            │
│  Movilidad entrante (t-2) ↔ Nuevos casos (t) = r = 0.71 ***        │
│                                                                     │
│  Scatter plot:                                                      │
│  Eje X: pasajeros entrantes semana t-2                              │
│  Eje Y: casos nuevos semana t                                       │
│  Cada punto = municipio · Tamaño = población                        │
│  Color = departamento                                               │
├─────────────────────────────────────────────────────────────────────┤
│  TOP 10 MUNICIPIOS DE MAYOR RIESGO DE IMPORTACIÓN                   │
│                                                                     │
│  #  Municipio          Pasajeros   Origen alerta   Riesgo importado │
│  1  Buenaventura       8.400/sem   Pasto (🔴)      Alto             │
│  2  Quibdó             4.200/sem   Medellín (🟡)   Medio            │
│  3  Tumaco             3.100/sem   Cali (🟡)       Medio            │
│  ...                                                                │
└─────────────────────────────────────────────────────────────────────┘
```

**Nota técnica sobre los datos de movilidad:**

- El dataset nacional de MinTransporte provee flujos OD **intermunicipales** (origen-destino entre municipios).
- Se usa como proxy de difusión regional, no intra-urbana.
- Para Medellín se complementa con datos del Terminal de Transportes.
- **Sesgo controlado:** Los flujos de movilidad no capturan informalidad (mototaxi, chalupa, etc.) que es dominante en zonas rurales como Amazonía. Esto se documenta explícitamente como limitación.

**Implementación técnica del mapa OD:**

```python
# Power BI con Kepler.gl via iframe embedding o visual custom
# Alternativamente: Deck.gl ArcLayer en Next.js

import keplergl
from keplergl import KeplerGl

# Preparar datos OD enriquecidos
od_enriched = od_df.merge(
    risk_predictions[["municipio_cod", "risk_score", "disease"]],
    left_on="municipio_origen_cod", right_on="municipio_cod"
)

# Kepler.gl config para arcos de flujo
config = {
    "visState": {
        "layers": [{
            "type": "arc",
            "config": {
                "dataId": "od_flows",
                "columns": {
                    "lat0": "lat_origen", "lng0": "lon_origen",
                    "lat1": "lat_destino", "lng1": "lon_destino"
                },
                "visConfig": {
                    "strokeScale": "pasajeros_semana",  # grosor = volumen
                    "colorField": "risk_score",          # color = riesgo
                    "colorRange": {"colors": ["#00FF00","#FFAA00","#FF0000"]}
                }
            }
        }]
    }
}
```

---

### Dashboard 4 — Monitor de Noticias Scrapeadas

**Herramienta:** Next.js 15 (React + Tailwind) — componente nativo web
**Audiencia:** Todo el equipo de respuesta + comunicadores de salud
**Actualización:** Cada 6 horas (cron job de scraping)
**Período visible:** Últimos 30 días (configurable a 14 o 7 días)

```
┌─────────────────────────────────────────────────────────────────────┐
│  ECOS — Monitor de Noticias Epidemiológicas                        │
│  Últimos 30 días · 847 artículos procesados · 124 relevantes       │
├──────────────────────────────┬──────────────────────────────────────┤
│  FILTROS                     │  TIMELINE DE MENCIONES               │
│                              │                                      │
│  Enfermedad:                 │  Menciones  │     ▄▄                 │
│  ☑ Dengue  ☑ Malaria        │  diarias    │  ▄▄▄██▄▄▄              │
│  ☑ Chiku   ☑ Zika           │    30 ─     │ ▄████████▄▄▄           │
│  ☑ General                   │    20 ─     │▄████████████▄          │
│                              │    10 ─     │███████████████         │
│  Región:                     │     0 ─     └──────────────────►     │
│  [Todas las regiones ▼]      │              Abr 03      May 03      │
│                              │                                      │
│  Nivel de alerta:            │  [Dengue ── Malaria ── Chiku ──]    │
│  ☑ Alta  ☑ Media  ○ Baja    │                                      │
├──────────────────────────────┴──────────────────────────────────────┤
│  MAPA DE CALOR — Menciones en medios por departamento (30 días)    │
│                                                                     │
│  [Colombia choropleth · color = densidad de noticias · clickable]  │
│  Escala: Gris (0 menciones) → Naranja → Rojo (15+ menciones)       │
├─────────────────────────────────────────────────────────────────────┤
│  FEED DE NOTICIAS CLASIFICADAS                                      │
│                                                                     │
│  🔴 ALTA ALERTA                                              May 01 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🦟 DENGUE · NARIÑO · La Opinión                             │   │
│  │ "Secretaría de Salud de Pasto reporta aumento del 40% en    │   │
│  │  consultas por fiebre en últimas 2 semanas"                  │   │
│  │ Score de alerta: 0.91  ·  [Leer artículo ↗]                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  🟡 VIGILANCIA                                               Apr 29 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🦟 MALARIA · CHOCÓ · El Colombiano                          │   │
│  │ "Alcaldía de Quibdó activa plan de fumigación preventivo     │   │
│  │  ante temporada de lluvias"                                  │   │
│  │ Score de alerta: 0.73  ·  [Leer artículo ↗]                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  🟡 VIGILANCIA                                               Apr 28 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🦟 DENGUE · ATLÁNTICO · El Heraldo                          │   │
│  │ "INS emite alerta por incremento de casos de dengue          │   │
│  │  en municipios del norte del Atlántico"                      │   │
│  │ Score de alerta: 0.68  ·  [Leer artículo ↗]                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  [Cargar más noticias ↓]                                            │
├─────────────────────────────────────────────────────────────────────┤
│  FUENTES ACTIVAS                                                    │
│  El Tiempo (🟢 ok) · La Opinión (🟢 ok) · El Heraldo (🟢 ok)     │
│  El Colombiano (🟢 ok) · Caracol Radio (🟢 ok) · INS (🟢 ok)     │
│  Diario del Huila (🟡 último scrape: 6h) · RCN (🟢 ok)            │
└─────────────────────────────────────────────────────────────────────┘
```

**Componente Next.js — estructura:**

```typescript
// /web/app/noticias/page.tsx
import { NewsCard } from "@/components/NewsCard";
import { MentionsTimeline } from "@/components/MentionsTimeline";
import { NewsHeatMap } from "@/components/NewsHeatMap";
import { SourceStatus } from "@/components/SourceStatus";

// Refresca cada 6 horas con ISR de Next.js
export const revalidate = 21600;

async function getNews(filters: NewsFilters) {
  const res = await fetch(
    `${API_URL}/api/v1/news?${new URLSearchParams(filters)}`,
  );
  return res.json();
}

// Los artículos tienen este shape:
interface NewsArticle {
  id: string;
  title: string;
  source: string; // "La Opinión"
  source_url: string;
  published_at: string;
  disease: "dengue" | "chikungunya" | "malaria" | "zika" | "general";
  department: string; // "Nariño" — extraído por NER
  municipality?: string; // Si el NER lo detectó
  alert_score: number; // 0.0 – 1.0
  alert_level: "alta" | "media" | "baja";
  snippet: string; // Primeros 200 chars del artículo
}
```

---

### Dashboard 5 — RAG Conversacional

**Herramienta:** Next.js 15 — interfaz de chat tipo assistant
**Audiencia:** Cualquier funcionario de salud sin conocimiento técnico
**Backend:** LangChain + ChromaDB + Groq (LLaMA 3.1 70B)

```
┌─────────────────────────────────────────────────────────────────────┐
│  ECOS — Asistente Epidemiológico                       ⚙️ Config   │
│  Consulta en lenguaje natural · Respuestas basadas en datos reales  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ 🤖 Hola. Soy el asistente de ECOS. Puedo responderte       │    │
│  │    preguntas sobre riesgo epidemiológico en Colombia,       │    │
│  │    tendencias de búsqueda, noticias recientes y predicciones│    │
│  │    del modelo. ¿En qué te puedo ayudar hoy?                 │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ 👤 ¿Cuál es el riesgo de dengue en Nariño para las         │    │
│  │    próximas tres semanas?                                   │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ 🤖 Basándome en el modelo ECOS actualizado a la semana 18  │    │
│  │    de 2026:                                                 │    │
│  │                                                             │    │
│  │  📊 Probabilidad de brote en Nariño:                       │    │
│  │    · Semana 19: 0.76 (ALTA)                                 │    │
│  │    · Semana 20: 0.83 (ALTA)                                 │    │
│  │    · Semana 21: 0.79 (ALTA)                                 │    │
│  │                                                             │    │
│  │  🔍 Principales factores (SHAP):                           │    │
│  │    1. Humedad relativa actual 87% (histórico: 72%)          │    │
│  │    2. Google Trends "dengue síntomas" Nariño: +3.2 SD       │    │
│  │    3. 8 noticias de alerta en últimas 2 semanas             │    │
│  │                                                             │    │
│  │  📰 Noticias relevantes recientes:                         │    │
│  │    · La Opinión (May 01): "Secretaría de Salud de Pasto     │    │
│  │      reporta aumento del 40% en consultas febriles"         │    │
│  │                                                             │    │
│  │  ✅ Recomendación: Activar brigadas de fumigación en Pasto  │    │
│  │  y municipios de Nariño. Reforzar puestos de salud y emitir │    │
│  │  comunicado a la comunidad. Revisar inventario de insumos.  │    │
│  │                                                             │    │
│  │  📎 Fuentes: Modelo ECOS S18·2026 · SIVIGILA histórico ·   │    │
│  │  Google Trends Nariño · La Opinión 01/05/2026               │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌──────────────────────────────────────────── [Enviar ➤] ─────┐  │
│  │ Escribe tu pregunta...                                        │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Sugerencias rápidas:                                               │
│  [Riesgo por región esta semana]  [Noticias últimas 48h]            │
│  [¿Cómo afecta la movilidad?]    [Comparar 2025 vs 2024]           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Limitaciones Técnicas, Sesgos y Mitigaciones

> Documentar limitaciones con honestidad es un indicador de madurez técnica. Un proyecto que conoce sus sesgos y los mitiga activamente es más confiable que uno que los oculta. Esta sección es parte integral de la propuesta, no un anexo de descargos.

### 8.1 Sesgos en los datos de entrada

---

**① Subnotificación estructural en SIVIGILA** ← _El más crítico_

El modelo aprende de casos _reportados_, no casos _reales_. En zonas rurales la subnotificación puede ser del 50–70% (estimaciones OPS/INS). El sistema solo ve lo que llega al sistema de salud formal.

_Impacto:_ El modelo subestimará sistemáticamente el riesgo en Amazonía, Orinoquía y Pacífico rural — justo donde la malaria y otras enfermedades tienen mayor carga real.

_Mitigación:_

- Las predicciones en zonas con alta subnotificación histórica se etiquetan con un **factor de corrección** (scaling factor) estimado por departamento a partir de estudios de prevalencia del INS.
- El dashboard muestra un indicador de "confiabilidad del dato base" por zona: alto (Bogotá, Medellín), medio (capitales departamentales), bajo (municipios rurales sin IPS).
- El RAG advierte explícitamente al usuario cuando la predicción corresponde a una zona con subnotificación conocida.

---

**② Códigos DANE inconsistentes en el histórico 2007–2022**

Entre 2007 y 2022 se crearon nuevos municipios (ej: Riosucio en Chocó, varios en Nariño) y se reasignaron códigos DANE. Un `JOIN` directo por código produce municipios fantasma o silencia registros históricos completos.

_Impacto:_ Pérdida silenciosa de datos históricos o duplicación de casos en municipios que cambiaron de código.

_Mitigación:_

```python
# ETL — tabla de equivalencias DANE (fuente: DIVIPOLA histórico del DANE)
# Mapea códigos obsoletos al código DANE vigente a 2023
dane_equivalencias = pd.read_csv("data/raw/divipola_historico.csv")
# Formato: cod_dane_historico | cod_dane_vigente | municipio | dpto | año_cambio

def normalizar_codigo_dane(df, col_codigo, col_año):
    """
    Reemplaza códigos históricos por su equivalente vigente.
    Registra cuántos registros fueron normalizados para auditoría.
    """
    df = df.merge(dane_equivalencias,
                  left_on=[col_codigo, col_año],
                  right_on=["cod_dane_historico", "año_cambio"],
                  how="left")
    df[col_codigo] = df["cod_dane_vigente"].fillna(df[col_codigo])
    return df
```

La tabla DIVIPOLA histórica del DANE es pública y se incluye en `/data/raw/`.

---

**③ Horizonte de datos insuficiente para zika y chikungunya**

| Enfermedad  | Datos desde | Ciclos epidémicos observados  | Confianza del modelo |
| ----------- | ----------- | ----------------------------- | -------------------- |
| Dengue      | 2007        | 8+ ciclos bianuales           | Alta                 |
| Malaria     | 2007        | Endémica continua             | Alta                 |
| Chikungunya | 2014        | 2 ciclos                      | Media                |
| Zika        | 2015        | 1 ciclo relevante (2015–2016) | Baja                 |

_Impacto:_ El modelo para zika y chikungunya tiene menos datos para aprender patrones de estacionalidad. Las predicciones tienen intervalos de confianza más amplios.

_Mitigación:_

- Se reporta el intervalo de confianza del 90% en cada predicción — más ancho para chikungunya/zika que para dengue.
- Prophet usa regularización más fuerte para estas enfermedades (parámetro `changepoint_prior_scale` más bajo).
- El dashboard muestra una etiqueta de confianza por enfermedad: **Alta / Media / Baja**, visible al usuario.
- El RAG aclara la limitación cuando se consulta por zika o chikungunya.

---

**④ Cobertura de vacunación: granularidad departamental aplicada a predicciones municipales**

El dataset de MinSalud (Dataset 4) reporta cobertura por departamento y biológico. Las predicciones de ECOS son a nivel municipal. Aplicar el promedio departamental a todos los municipios es incorrecto — Pasto urbano y un municipio rural de Nariño tienen coberturas radicalmente distintas.

_Impacto:_ Subestimación del riesgo en municipios rurales con cobertura real inferior al promedio departamental.

_Mitigación:_

- La variable de vacunación entra al modelo **solo a nivel departamental** (no se extrapola al municipio).
- Las predicciones municipales usan vacunación del departamento al que pertenecen, documentando esta limitación en el feature store.
- Se incluye el Índice de Pobreza Multidimensional (IPM) municipal como proxy de acceso a servicios de salud — variable que sí tiene resolución municipal.

---

**⑤ RIPS excluye al sector informal y medicina tradicional**

RIPS solo captura atenciones del sistema formal de salud (IPS habilitadas). En zonas rurales, una fracción significativa de la población recurre a promotores de salud comunitarios, médicos tradicionales indígenas o simplemente no consulta. RIPS subestima la carga real en las poblaciones más vulnerables.

_Impacto:_ RIPS refuerza el mismo sesgo que SIVIGILA — ambas fuentes capturan el sistema formal. Su "divergencia" como señal de alerta (Dataset 5 vs. Dataset 1) sigue siendo válida, pero su nivel absoluto no refleja la carga real.

_Mitigación:_

- RIPS se usa como **señal diferencial** (¿están divergiendo RIPS y SIVIGILA esta semana?), no como estimador de carga absoluta.
- La divergencia RIPS–SIVIGILA entra al modelo como feature de "subnotificación activa", no como conteo de casos.
- Se documenta explícitamente en el dashboard que RIPS no incluye sector informal.

---

**⑥ Dataset de movilidad: posible desactualización post-COVID**

El dataset de MinTransporte (Dataset 6) puede corresponder a patrones de movilidad pre-pandemia (2018–2019). Los flujos de transporte intermunicipal cambiaron significativamente durante y después de COVID-19.

_Impacto:_ Los arcos OD del mapa de movilidad pueden no reflejar los patrones actuales, sobreestimando rutas que disminuyeron o ignorando rutas que crecieron.

_Mitigación:_

- Se verifica la fecha de corte del dataset al descargarlo e se registra en los metadatos (`data/raw/movilidad_metadata.json`).
- Si los datos son pre-2020: la variable de movilidad se pondera con un coeficiente de confianza reducido en XGBoost.
- Se documenta el año de los datos en el dashboard de movilidad con una etiqueta visible.
- La movilidad actúa como proxy de conectividad estructural (rutas que existen), no como medición puntual de flujos — interpretación más robusta a la desactualización.

---

**⑦ Sesgo de cobertura mediática en el scraping de noticias**

Los medios nacionales y regionales cubren desproporcionadamente los eventos en ciudades grandes. Un brote en Quibdó puede generar 1 artículo; el mismo brote en Bogotá o Medellín genera 20. El clasificador NLP detectará más "señales" en hubs urbanos que en zonas endémicas rurales.

_Impacto:_ Exactamente el sesgo inverso al que necesitamos — más señal donde hay menos riesgo real, menos señal donde hay más.

_Mitigación:_

- El score de noticias se **normaliza por la densidad mediática histórica** del departamento: un artículo sobre Quibdó vale más (peso mayor) que un artículo sobre Bogotá.
- Se incluye el boletín del INS (Fuente C) como fuente oficial que cubre todo el territorio con igual peso independientemente del tamaño del municipio.
- Las noticias contribuyen con peso bajo al modelo (ver Feature Weights en §4.2A). No son una señal primaria.

```python
# Peso relativo de noticias por departamento
# Inversamente proporcional a la densidad mediática histórica
densidad_mediatica = {
    "Bogotá D.C.":   1.0,   # referencia
    "Antioquia":     0.9,
    "Valle del Cauca": 0.85,
    "Atlántico":     0.7,
    "Chocó":         0.25,  # artículo de Chocó = 4x el peso de Bogotá
    "Vaupés":        0.1,
    "Guainía":       0.1,
}
peso_noticia = lambda dpto: 1 / densidad_mediatica.get(dpto, 0.5)
```

---

**⑧ Período COVID 2020–2021: ruido bidireccional en el target**

Durante COVID-19:

- Dengue y COVID comparten síntomas (fiebre, malestar, dolor de cabeza). Muchos casos de dengue fueron clasificados como COVID y viceversa → **subregistro de dengue en SIVIGILA**.
- Las restricciones de movilidad redujeron la transmisión vectorial en algunos periodos → **reducción real de casos**, no solo de reporte.
- Los servicios de salud colapsaron → **reducción de consultas y notificaciones**, no de casos reales.

_Impacto:_ El modelo podría aprender patrones incorrectos del período 2020–2021 si se trata como datos normales.

_Mitigación:_

```python
# Variable dummy en XGBoost — período COVID
df["periodo_covid"] = df["año"].isin([2020, 2021]).astype(int)

# El período 2020-2021 se EXCLUYE del validation set
# Solo se usa para entrenamiento con la dummy activa
VALIDATION_YEARS = [2022, 2023]   # años post-COVID, datos confiables
TRAINING_YEARS   = list(range(2007, 2022))  # incluye COVID con dummy
```

El EDA del período COVID se documenta en `crisp-ml/02-data-understanding.ipynb` con análisis explícito de la anomalía.

---

**⑨ Definición de "brote": el umbral que hace válidas todas las métricas**

Sin una definición epidemiológica precisa de "brote", el AUC-ROC, el recall y el accuracy-score no tienen significado porque el threshold de clasificación es arbitrario.

_Definición adoptada por ECOS (alineada con el INS):_

> **Brote** = semana en que los casos reportados superan el percentil 75 del canal endémico histórico del mismo municipio para la misma semana epidemiológica, calculado sobre los últimos 5 años con datos disponibles, excluyendo años atípicos (2020–2021).

```python
def calcular_canal_endemico(serie_historica: pd.Series,
                             semana_epi: int,
                             años_excluidos: list = [2020, 2021]) -> dict:
    """
    Canal endémico histórico para una semana epidemiológica dada.
    Retorna los percentiles 25, 50, 75 (zona de seguridad, alerta, epidemia).
    Alineado con la metodología del INS Colombia.
    """
    datos = serie_historica[
        (serie_historica.index.isocalendar().week == semana_epi) &
        (~serie_historica.index.year.isin(años_excluidos))
    ]
    return {
        "p25": datos.quantile(0.25),  # límite inferior canal
        "p50": datos.quantile(0.50),  # mediana histórica
        "p75": datos.quantile(0.75),  # umbral de alerta (BROTE)
        "p90": datos.quantile(0.90),  # umbral de epidemia
    }

# Y = 1 (brote) si casos_semana > canal_endemico["p75"]
# Y = 0 (no brote) si casos_semana <= canal_endemico["p75"]
```

Esta definición es citable (metodología INS), reproducible y consistente con la práctica de vigilancia epidemiológica colombiana.

---

**⑩ pytrends no es una API oficial de Google**

`pytrends` es una librería no oficial que hace scraping de la interfaz web de Google Trends. Google puede bloquearla, cambiar su estructura o añadir CAPTCHAs sin previo aviso.

_Impacto para el concurso:_ Ninguno — funciona estable en demos y desarrollo.
_Impacto para producción:_ Riesgo de interrupción del servicio sin aviso.

_Mitigación:_

- Rate limiting agresivo (1.5s entre requests) para minimizar riesgo de bloqueo.
- Health check semanal que detecta si pytrends deja de retornar datos.
- Si falla: el sistema continúa operando con las otras 5 fuentes. Google Trends tiene peso bajo en el modelo (§4.2A), por lo que su ausencia no invalida las predicciones.
- Para producción a largo plazo: migrar a la API oficial de Google Trends (beta, requiere aprobación). Documentado como deuda técnica.

---

### 8.2 Resumen ejecutivo de sesgos

| #   | Sesgo                                 | Severidad     | ¿Invalida el modelo? | Mitigación                                            |
| --- | ------------------------------------- | ------------- | -------------------- | ----------------------------------------------------- |
| ①   | Subnotificación SIVIGILA              | 🔴 Alta       | No — ajustable       | Factor de corrección + etiqueta de confiabilidad      |
| ②   | Códigos DANE inconsistentes           | 🟠 Media-Alta | Sí si no se corrige  | Tabla DIVIPOLA histórica en ETL                       |
| ③   | Pocos datos zika/chikungunya          | 🟠 Media      | Parcialmente         | IC más ancho + etiqueta de confianza                  |
| ④   | Vacunación solo departamental         | 🟡 Media      | No                   | Documentado + IPM municipal como proxy                |
| ⑤   | RIPS excluye sector informal          | 🟡 Media      | No                   | RIPS como señal diferencial, no absoluta              |
| ⑥   | Movilidad posiblemente desactualizada | 🟡 Media      | No                   | Fecha de corte visible + peso reducido si pre-2020    |
| ⑦   | Sesgo mediático urbano en noticias    | 🟡 Media      | No                   | Peso inversamente proporcional a densidad mediática   |
| ⑧   | Ruido COVID 2020–2021                 | 🟠 Media      | No si se maneja      | Dummy variable + excluir de validation set            |
| ⑨   | Definición de brote ambigua           | 🔴 Alta       | Sí si no se define   | Definición canal endémico INS, citable y reproducible |
| ⑩   | pytrends no es API oficial            | 🟢 Baja       | No                   | Rate limiting + fallback a otras fuentes              |

---

## 9. Métricas de Evaluación

### 9.0 Definición operacional de "brote" (prerequisito de todas las métricas)

Ver §8.1 ⑨ para la definición completa. Resumen:

> **Brote = semana con casos > percentil 75 del canal endémico histórico** del mismo municipio, misma semana epidemiológica, últimos 5 años, excluyendo 2020–2021. Metodología INS Colombia.

Esta definición determina el threshold de clasificación binaria (Y=1 / Y=0) sobre el que se calculan AUC-ROC, recall y precision.

### 9.1 Métricas del modelo predictivo

| Métrica               | Definición                                                 | Meta ECOS                   |
| --------------------- | ---------------------------------------------------------- | --------------------------- |
| MAE                   | Error absoluto medio en casos predichos                    | < 15 casos/semana/municipio |
| RMSE                  | Error cuadrático medio                                     | < 30 casos/semana/municipio |
| AUC-ROC               | Clasificación brote/no-brote (umbral = p75 canal endémico) | > 0.82                      |
| Sensibilidad (recall) | % de brotes reales detectados                              | > 0.80 (prioridad)          |
| Anticipación promedio | Semanas de adelanto vs. SIVIGILA oficial                   | ≥ 2.0 semanas               |
| Falsa alarma rate     | % de alertas que no se materializaron en brote             | < 25%                       |

> **Nota de salud pública:** En epidemiología, una falsa alarma es mucho menos costosa que un brote no detectado. Por eso priorizamos sensibilidad (recall) sobre precisión.

**Confianza del modelo por enfermedad** (derivada del volumen histórico disponible):

| Enfermedad  | Datos desde | Meta AUC-ROC | IC predicción |
| ----------- | ----------- | ------------ | ------------- |
| Dengue      | 2007        | > 0.85       | ±12%          |
| Malaria     | 2007        | > 0.83       | ±15%          |
| Chikungunya | 2014        | > 0.78       | ±22%          |
| Zika        | 2015        | > 0.72       | ±30%          |

Las metas son diferenciadas porque pretender el mismo AUC para zika (1 ciclo epidémico observado) que para dengue (8+ ciclos) sería epidemiológicamente deshonesto.

### 9.2 Métricas del sistema de noticias

| Métrica                                                   | Meta         |
| --------------------------------------------------------- | ------------ |
| Precisión del clasificador (noticia epidemiológica sí/no) | > 0.90       |
| Exactitud NER municipio/departamento                      | > 0.85       |
| Latencia de scraping a visualización                      | < 30 minutos |

### 9.3 Métricas de tendencias

| Métrica                               | Meta                               |
| ------------------------------------- | ---------------------------------- |
| Correlación Tendencia(t-2) ↔ Casos(t) | > 0.60 Pearson                     |
| Detección anticipada de spikes        | ≥ 1 semana antes del pico SIVIGILA |

---

## 10. Impacto Esperado

### 10.1 Salud pública

- **Anticipación:** 2–4 semanas de aviso antes del reporte oficial en SIVIGILA.
- **Casos prevenidos (estimado conservador):** 10% de reducción en incidencia = ~50.000 casos anuales de dengue.
- **Muertes evitables:** La detección temprana reduce la tasa de dengue grave; estimado 30–50 muertes evitables por ciclo epidémico.
- **Recursos optimizados:** Brigadas de fumigación, insumos hospitalarios y kits de diagnóstico focalizados en zonas de mayor riesgo predicho.

### 10.2 Institucional

- Herramienta directamente utilizable por el INS, MinSalud y 32 secretarías departamentales.
- El dashboard Power BI puede publicarse en Power BI Service y compartirse con credenciales institucionales.
- Los reportes PDF automáticos reemplazan trabajo manual de los equipos de epidemiología.

### 10.3 Escalabilidad

| Dimensión                     | Descripción                                                                     |
| ----------------------------- | ------------------------------------------------------------------------------- |
| **Horizontal (enfermedades)** | Leptospirosis, leishmaniasis, hepatitis A, COVID-19 — cualquier evento SIVIGILA |
| **Vertical (volumen)**        | Arquitectura Spark lista para el data lake completo del INS                     |
| **Regional (países)**         | Replicable en Perú, Ecuador, Brasil con sistemas similares                      |
| **Temporal (sostenibilidad)** | Diseñado para transferencia al INS como herramienta de uso continuo             |

---

## 11. Plan de Ejecución

### Semanas 1–2 — Fundamentos de datos y ETL

- [ ] Descargar y documentar los 6 datasets de datos.gov.co
- [ ] Pipeline PySpark: limpieza, normalización DANE, join semanal
- [ ] EDA completo (crisp-ml/02-data-understanding.ipynb)
- [ ] Módulo de scraping base: pytrends + feedparser funcionando
- [ ] Setup Docker Compose + PostgreSQL + FastAPI esqueleto

### Semanas 3–4 — Modelos e IA

- [ ] Modelo Prophet baseline por enfermedad
- [ ] Feature engineering: clima, vacunación, movilidad, trends, noticias
- [ ] XGBoost sobre residuales Prophet
- [ ] Walk-forward validation + métricas
- [ ] SHAP explainer integrado en API
- [ ] Clasificador NLP de noticias (TF-IDF + spaCy NER)

### Semanas 5–6 — Dashboards y portal web

- [ ] Power BI: Dashboard 1 (Centro de Comando) completo
- [ ] Power BI: Dashboard 3 (Movilidad × Enfermedad) completo
- [ ] Next.js: Portal con autenticación básica
- [ ] Next.js: Dashboard 2 (Google Trends alerts) — página `/tendencias`
- [ ] Next.js: Dashboard 4 (Monitor de Noticias) — página `/noticias`

### Semana 7 — RAG y sistema de alertas

- [ ] ChromaDB indexado con datos del modelo + boletines INS
- [ ] LangChain pipeline RAG + Groq (LLaMA 3.1)
- [ ] Interfaz de chat en Next.js (`/chat`)
- [ ] Sistema de alertas automáticas por email (reportlab PDF)

### Semana 8 — Pulido y presentación

- [ ] Integración Power BI embedded en Next.js
- [ ] Demo end-to-end en Docker local
- [ ] Video demo (2–3 minutos)
- [ ] README completo en español con instalación paso a paso
- [ ] Publicación en herramientas.datos.gov.co/usos
- [ ] Registro GitHub público con licencia MIT

---

## 12. Criterios del Concurso y Puntuación Estimada

| Criterio                    | Pts máximos | ECOS       | Justificación                                                                                                                                              |
| --------------------------- | ----------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Innovación y creatividad    | 15          | **14–15**  | Google Trends + noticias en tiempo real + RAG conversacional + mapa OD movilidad. Diferencial claro frente a análisis descriptivos.                        |
| Uso de datos abiertos       | 20          | **19–20**  | 6 datasets datos.gov.co incluyendo SIVIGILA 15 años. Movilidad, vacunación, RIPS, clima. Perfectamente alineado con Reto 1 y Hoja de Ruta Salud 2025-2026. |
| Análisis y rigor técnico    | 15          | **14–15**  | PySpark + CRISP-ML + walk-forward validation sin data leakage + SHAP + documentación de limitaciones.                                                      |
| Tecnologías emergentes — IA | 20          | **19–20**  | Predictivo (XGBoost + Prophet) + generativo (RAG LLaMA 3) + explicabilidad (SHAP) + NLP clasificador noticias (spaCy).                                     |
| Impacto y escalabilidad     | 20          | **18–20**  | Impacto directo MinSalud/INS. Escalable a otros eventos SIVIGILA y otros países. Cuantificación económica del impacto.                                     |
| Diseño y usabilidad         | 10          | **9–10**   | Power BI profesional + Next.js moderno + chat RAG + monitor de noticias. Listo para uso institucional.                                                     |
| **Total estimado**          | **100**     | **93–100** |                                                                                                                                                            |

---

## 13. Ética y Privacidad

| Principio                              | Implementación en ECOS                                                                                   |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Sin datos personales**               | Todos los datasets son agregados (municipio/departamento). Sin información individual de pacientes.      |
| **Scraping ético**                     | Respeto estricto de `robots.txt`. Solo feeds RSS públicos. Sin redes sociales. Sin datos personales.     |
| **Google Trends anonimizado**          | Solo tendencias agregadas publicadas por Google. Sin datos de usuarios individuales.                     |
| **Transparencia algorítmica**          | SHAP en cada predicción. Código open-source. No hay caja negra.                                          |
| **Herramienta de apoyo, no sustituto** | El sistema genera recomendaciones; la decisión final es siempre humana.                                  |
| **Reproducibilidad total**             | Código, datos procesados y parámetros publicados en GitHub para verificación independiente.              |
| **Propiedad intelectual**              | Todo el código es de autoría original. Librerías con licencias MIT/Apache 2.0. Datos en dominio público. |

---

## 14. Repositorio y Publicación

```
GitHub:     https://github.com/[equipo]/ecos-colombia
Licencia:   MIT (reutilizable por entidades públicas sin restricciones)
Demo:       Docker Compose local · localhost:3000 (web) · localhost:8000 (API)
Docs API:   localhost:8000/docs  (Swagger automático)
Power BI:   .pbix incluidos en /powerbi + publicados en Power BI Service
Registro:   https://herramientas.datos.gov.co/usos
```

---

## Apéndice A — Estructura de la API REST

```
GET  /api/v1/health                          → Estado del sistema
GET  /api/v1/predictions                     → Predicciones por dept/municipio/semana
GET  /api/v1/alerts/active                   → Alertas activas en tiempo real
GET  /api/v1/shap?dept=X&disease=Y&week=Z   → Explicación SHAP de predicción
GET  /api/v1/trends?dept=X&keyword=Y        → Índices Google Trends + alertas estadísticas
GET  /api/v1/news?disease=X&days=30         → Feed de noticias clasificadas
GET  /api/v1/mobility/od                    → Flujos OD enriquecidos con riesgo
GET  /api/v1/timeseries?dept=X&disease=Y   → Serie histórica + predicción
POST /api/v1/chat                           → Endpoint del RAG conversacional
POST /api/v1/whatif                         → Simulador de escenarios
GET  /api/v1/report/pdf?dept=X             → Reporte PDF automático (reportlab)
```

---

## Apéndice B — Variables del Feature Store

```
Por municipio + semana epidemiológica:

EPIDEMIOLÓGICAS (de SIVIGILA + RIPS):
  casos_dengue, casos_chiku, casos_malaria, casos_zika (semana t-1, t-2, t-4)
  atenciones_cie10_dengue (RIPS, semana t-1)
  divergencia_rips_sivigila (señal de subnotificación)

CLIMÁTICAS (IDEAM normales + Open-Meteo actual):
  temp_max, temp_min, temp_media, humedad_relativa, precipitacion

MOVILIDAD (dataset OD MinTransporte):
  pasajeros_entrantes_semana, pasajeros_salientes_semana
  conectividad_municipios_alerta (cuántos municipios conectados están en alerta)

SEÑALES TEMPRANAS (scraping):
  # Google Trends — enfoque híbrido
  trend_nacional_dengue         # índice 0-100, Colombia completo, siempre válido
  trend_nacional_malaria        # ídem
  trend_nacional_chiku          # ídem
  trend_nacional_zika           # ídem
  trend_nacional_zscore         # desviación vs. histórico — variable que entra al modelo
  trend_dpto_dengue             # solo para 9 dptos con volumen (None si insuficiente)
  trend_dpto_zscore             # zscore departamental — entra al modelo con peso reducido
  trend_dpto_disponible         # bool — indica si el dato departamental es válido
  # Noticias scrapeadas
  menciones_medios_dpto         # conteo noticias epidemiológicas, semana t-1
  score_alerta_noticias         # promedio scores del clasificador NLP

ESTRUCTURALES (anuales, nivel departamental):
  cobertura_vacunacion_dpt
  indice_pobreza_multidimensional
  cobertura_acueducto, cobertura_alcantarillado

TARGET:
  prob_brote_2sem (clasificación binaria)
  casos_predichos_2sem (regresión)
  casos_predichos_4sem (regresión)
```

---

_ECOS — Early Control and Observation System_
_Concurso Datos al Ecosistema 2026 — IA para Colombia_
_Desarrollado con datos abiertos de datos.gov.co_
_Licencia MIT · Código abierto · Transferible al INS y MinSalud_
