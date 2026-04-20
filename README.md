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
- infra/: despliegue

## Requisitos

- Node.js 20+
- Python 3.11+

## Inicio rapido

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Nota: cada componente tiene su propio requirements.txt (por ejemplo, backend/ y models/).
Si prefieres instalar desde la raiz:

```bash
python -m venv .venv-backend
source .venv-backend/bin/activate
pip install -r backend/requirements.txt
```

## Datos y pipeline (Spark)

### 1) Descargar datasets

```bash
python scripts/download_datasets.py
```

Notas:
- Los archivos descargados quedan en data/raw/.

### 2) Levantar Spark con Docker Compose

```bash
docker compose -f infra/docker-compose.spark.yml up -d
```

### 3) Generar el curado v0

```bash
docker compose -f infra/docker-compose.spark.yml exec spark-master \
	/opt/spark/bin/spark-submit /opt/spark/work/scripts/curate_weekly_v0_spark.py \
	--sivigila /opt/spark/work/data/raw/sivigila_4hyg-wa9d.csv \
	--clima /opt/spark/work/data/raw/clima_normales_ideam_nsz2-kzcq.csv \
	--out-parquet /opt/spark/work/data/processed/curated_weekly_v0_parquet \
	--out-csv /opt/spark/work/data/processed/curated_weekly_v0_csv
```

### 4) (Opcional) Validar el curado

```bash
docker compose -f infra/docker-compose.spark.yml exec spark-master \
	/opt/spark/bin/spark-submit /opt/spark/work/scripts/validate_curated_v0_spark.py \
	--input /opt/spark/work/data/processed/curated_weekly_v0_parquet
```

Salida esperada:
- data/processed/curated_weekly_v0_parquet/
- data/processed/curated_weekly_v0_csv/

Nota: data/processed esta en .gitignore.

## Configuracion

Copia el archivo de ejemplo y completa variables:

```bash
cd backend
cp .env.example .env
```

Variables principales:
- SUPABASE_URL
- SUPABASE_ANON_KEY

## Licencia

MIT
