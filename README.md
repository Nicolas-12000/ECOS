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

## Inicio rapido

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend
uvicorn app.main:app --reload
```

Nota: `requirements.txt` en la raiz es el manifiesto canonico. `backend/requirements.txt` y `models/requirements.txt` solo actuan como wrappers.

## Demo local (hackaton)

- Todo corre en local; no requiere servicios pagos.
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Base de datos: PostgreSQL local (localhost:5432)
- Dashboard BI: PBIX local usando data/processed.

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

### 3) Generar el curado semanal (unificado)

```bash
docker compose -f infra/docker-compose.spark.yml exec spark-master \
	/opt/spark/bin/spark-submit /opt/spark/work/scripts/curate_weekly_spark.py \
	--version full \
	--features all \
	--sivigila /opt/spark/work/data/raw/sivigila_4hyg-wa9d.csv \
	--climate /opt/spark/work/data/raw/clima_normales_ideam_nsz2-kzcq.csv \
	--out-parquet /opt/spark/work/data/processed/curated_weekly_parquet \
	--out-csv /opt/spark/work/data/processed/curated_weekly_csv
```

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
