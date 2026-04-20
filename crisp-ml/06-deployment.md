# Deployment

## Local demo (hackaton)

ECOS se ejecuta localmente para la competencia. No requiere servicios pagos ni despliegue en nube.

### Requisitos
- Python 3.11+
- Node.js 20+
- Docker (opcional, solo para Spark)
- PostgreSQL local

### Pasos
1. Preparar datos (scripts/download_datasets.py y pipeline Spark si aplica).
2. Base de datos:
   - Tener un Postgres local listo (por ejemplo, instalado en el sistema).
   - Configurar `DATABASE_URL` en backend/.env.
3. Backend:
	- Crear venv e instalar backend/requirements.txt.
	- Ejecutar uvicorn app.main:app --reload.
4. Frontend:
	- npm install
	- npm run dev
5. Dashboard BI:
	- Abrir el PBIX local y apuntar a data/processed.

### Verificacion
- API: http://localhost:8000/health
- Frontend: http://localhost:3000
