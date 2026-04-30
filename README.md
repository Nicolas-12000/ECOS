# ECOS

Plataforma nacional de alerta temprana para enfermedades de alto impacto en Colombia. Combina datos abiertos, senales tempranas y modelos predictivos explicables para anticipar brotes con 2 a 4 semanas de anticipacion.

## Estructura

- frontend/: app web (Next.js)
- backend/: API y servicios (FastAPI)
- data/: datos crudos, procesados y externos
- models/: artefactos de modelos
- crisp-ml/: documentacion por fases
- docs/: notas y decisiones
- notebooks/: exploracion
- scripts/: utilidades
- infra/: infraestructura local (Spark, Docker)

## Requisitos

- Node.js 20+
- Python 3.11+
- PostgreSQL 14+ (local)

## Inicio rápido

### 1. Configuración de Variables de Entorno
Copia el archivo de ejemplo y configura tu `GROQ_API_KEY` para que el asistente de IA funcione correctamente.
```bash
cp .env.example .env
```

### 2. Backend (FastAPI)
El backend procesa los modelos de ML y gestiona el motor RAG.
```bash
# Crear entorno virtual
python -m venv .venv
# Activar (Windows)
.venv\Scripts\activate
# Activar (Unix/macOS)
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor
cd backend
uvicorn app.main:app --reload
```
API disponible en: `http://localhost:8000` | Docs: `http://localhost:8000/docs`

### 3. Frontend (Next.js 15)
La interfaz moderna con dashboard interactivo y chat.
```bash
cd frontend
npm install
npm run dev
```
Dashboard disponible en: `http://localhost:3000`

### 4. Pipeline de Datos y Spark (Opcional)
Si necesitas regenerar los datos procesados desde cero:
```bash
# Descargar datasets crudos
python scripts/download_datasets.py

# Levantar infraestructura de Spark
docker compose -f infra/docker-compose.spark.yml up -d

# Ejecutar curaduría de datos
docker compose -f infra/docker-compose.spark.yml exec spark-master \
	/opt/spark/bin/spark-submit /opt/spark/work/scripts/curate_weekly_spark.py \
	--version full \
	--features all \
	--sivigila /opt/spark/work/data/raw/sivigila_4hyg-wa9d.csv \
	--climate /opt/spark/work/data/raw/clima_normales_ideam_nsz2-kzcq.csv \
	--out-parquet /opt/spark/work/data/processed/curated_weekly_parquet \
	--out-csv /opt/spark/work/data/processed/curated_weekly_csv
```

## Características Principales
- **Dashboard en Tiempo Real**: Visualización de señales climáticas y epidemiológicas.
- **Predicciones con ML**: Motor de inferencia para dengue, malaria, zika y chikungunya.
- **Asistente ECOS AI**: Chat interactivo con RAG basado en protocolos nacionales.
- **Integración Power BI**: Visualización avanzada integrada directamente en la web.

### 4) (Opcional) Validar el curado

```bash
docker compose -f infra/docker-compose.spark.yml exec spark-master \
	/opt/spark/bin/spark-submit /opt/spark/work/scripts/validate_curated_spark.py \
	--input /opt/spark/work/data/processed/curated_weekly_parquet
```

Salida esperada:
- data/processed/curated_weekly_parquet/
- data/processed/curated_weekly_csv/

Nota: data/processed esta en .gitignore.

## Configuracion

Para la demo local no se requieren servicios externos. Si usas base de datos local, configura `DATABASE_URL`:

```bash
cp .env.example .env
```

Variables opcionales: ver `.env.example`.

## Licencia

MIT
