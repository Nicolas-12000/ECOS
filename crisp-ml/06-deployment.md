# Fase 6: Despliegue y Monitoreo

## 1. Estrategia de Despliegue

ECOS está diseñado para **despliegue sin dependencias en la nube** (deployable en infraestructura local).

### 1.1 Opciones de Despliegue

#### Opción 1: Local con Docker Compose (RECOMENDADO PARA MVP)
**Target:** Demostraciones, pruebas iniciales, secretarías de salud con infraestructura limitada

```bash
docker-compose up -d
# Acceso: http://localhost:8000 (API)
#         http://localhost:3000 (Dashboard)
```

**Ventajas:**
- Sin dependencias en proveedores de nube
- Control total de datos
- Bajo costo operacional
- Reproducible en cualquier laptop

**Infraestructura mínima:**
- Docker + Docker Compose
- 2GB RAM, 5GB almacenamiento (histórico comprimido)

---

#### Opción 2: Kubernetes / OpenShift (ESCALAMIENTO POSTERIOR)
**Target:** Despliegue nacional centralizado en MinSalud

**Componentes:**
- FastAPI backend (escalable horizontalmente)
- PostgreSQL + TimescaleDB (almacenamiento temporal)
- Spark worker nodes (procesamiento de batch)
- Redis (caché de predicciones)

---

## 2. Ciclo de Actualización de Datos (Semanal)

**Programación:** Cada lunes a las 6:00 AM (UTC-5)

```
1. fetch_signals.py → extrae Trends + RSS → data/raw/
2. curate_weekly_spark.py → limpia, normaliza → data/processed/
3. predict.py → XGBoost + Prophet → JSON predicciones
4. send_alerts.py → Email a secretarías + INS
5. Dashboard actualiza visualizaciones
```

---

## 3. Monitoreo y Observabilidad

### 3.1 Métricas Clave

- **Data pipeline:** Latencia de extracción, fallos de fuentes
- **Modelos:** MAPE, Anticipación promedio, Recall brotes
- **API:** Tasa de error, latencia de respuesta

### 3.2 Alertas

| Métrica | Umbral | Acción |
|---------|--------|--------|
| Trends fetch fail | > 2 fallos | Notificar equipo |
| Predicción MAPE | > 35% | Reentrenar |
| API error rate | > 5% | Reiniciar |
| Data latency | > 48 horas | Investigar |

---

## 4. Validación Continua

Cada semana post-predicción, comparar con SIVIGILA rezagado (2 semanas).

```
Semana N: Generar predicciones
Semana N+2: Validar contra datos observados en SIVIGILA
Métrica: MAE, RMSE, Recall, Anticipation
Si MAPE > 35% → Reentrenar mensual
```

---

## 5. Seguridad

- **Autenticación:** JWT tokens por departamento
- **Encriptación:** HTTPS/TLS, PostgreSQL columnas sensibles
- **Datos:** Solo agregados, sin PII

---

## 6. Runbook Operacional

```bash
# Iniciar
docker-compose up -d

# Verificar salud
curl http://localhost:8000/health

# Pipeline manual
python scripts/fetch_signals.py
python scripts/curate_weekly_spark.py
python scripts/predict.py

# Logs
docker-compose logs -f api
```

---

## 7. Escalamiento Futuro

**Fase 2:** Kubernetes en infraestructura MinSalud  
**Fase 3:** Integración datos en tiempo real de laboratorios  
**Fase 4:** Modelo bayesiano para incertidumbre  

---

## 8. Contacto

**Equipo:** desarrollo@ecos-health.gov.co  
**Docs:** https://github.com/Nicolas-12000/ECOS/wiki
- PostgreSQL local

### Pasos
1. Preparar datos (scripts/download_datasets.py y pipeline Spark si aplica).
2. Base de datos:
   - Tener un Postgres local listo (por ejemplo, instalado en el sistema).
	- Configurar `DATABASE_URL` en `.env`.
3. Backend:
	- Crear venv en la raiz e instalar requirements.txt.
	- Ejecutar uvicorn app.main:app --reload.
4. Frontend:
	- npm install
	- npm run dev
5. Dashboard BI:
	- Abrir el PBIX local y apuntar a data/processed.

### Verificacion
- API: http://localhost:8000/health
- Frontend: http://localhost:3000
