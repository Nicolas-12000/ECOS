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
