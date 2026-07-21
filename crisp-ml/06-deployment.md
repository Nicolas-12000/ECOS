# Fase 6: Despliegue y Monitoreo

## Estado Actual

### 1. Componentes Listos
ECOS cuenta actualmente con:
- **Backend FastAPI** (`/backend/app/`) – API con endpoints de salud, histórico, señales y chat RAG
- **Frontend Next.js** (`/frontend/`) – Interfaz de usuario básica con chat
- **Scripts de Pipeline de Datos** (`/scripts/`):
  - `fetch_signals.py`
  - `curate_weekly_spark.py`
  - `predict.py`
  - `send_alerts.py` (placeholder)
- **Modelo Híbrido Entrenado** (`/models/`)
- **Dashboard Power BI** (`/dashboard/`)

---

## 2. Despliegue Local (Actual)

Para ejecutar ECOS localmente hoy día:

### 2.1 Backend
```bash
# Crear y activar venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar API
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2.2 Frontend
```bash
# Navegar a frontend
cd frontend

# Instalar dependencias (pnpm recomendado)
pnpm install

# Ejecutar frontend
pnpm dev
```

### 2.3 Verificación
- API salud: http://localhost:8000/health
- Frontend: http://localhost:3000
- Swagger API: http://localhost:8000/docs

---

## 3. Trabajo Futuro

### 3.1 Despliegue con Docker Compose (MVP)
**Objetivo:** Simplificar instalación con contenedores
- Componentes:
  - FastAPI backend
  - PostgreSQL (para datos y knowledge base)
  - Frontend Next.js
- Archivo planificado: `docker-compose.yml`

### 3.2 Monitoreo y Observabilidad
- Métricas de pipeline (latencia, fallos)
- Métricas de modelo (MAE, Recall)
- Alertas automáticas
- Dashboard de monitoreo

### 3.3 Validación Continua
- Comparar predicciones semanales con SIVIGILA rezagado (2 semanas)
- Reentrenamiento automático si el rendimiento baja

### 3.4 Seguridad
- Autenticación JWT por departamento
- HTTPS/TLS para despliegues en producción
- Encriptación de datos sensibles

### 3.5 Escalamiento Nacional
- Kubernetes/OpenShift en infraestructura de MinSalud
- PostgreSQL + TimescaleDB para series temporales
- Spark para procesamiento de batch
- Redis para caché de predicciones
- Integración con datos en tiempo real de laboratorios

---

