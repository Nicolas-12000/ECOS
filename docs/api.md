# API (ECOS)

Base URL local:
- http://localhost:8000

## Endpoints base

### GET /health

Respuesta:

```json
{"status":"ok"}
```

Si DATABASE_URL o las variables DB_* estan configuradas, tambien retorna el estado de la base:

```json
{"status":"ok","database":"ok"}
```

### GET /

Respuesta:

```json
{"name":"ECOS API","status":"ok"}
```

### POST /api/predict

Predice casos para una enfermedad y un municipio.

### GET /api/history

Retorna histórico epidemiológico por municipio y enfermedad.

### GET /api/signals

Retorna señales tempranas agregadas por departamento y enfermedad.

Campos disponibles (si existen en el curado):
- vaccination_coverage_pct
- rips_visits_total
- mobility_index
- trends_score
- rss_mentions
- signals_score

### POST /api/chat

Asistente conversacional con contexto documental y epidemiológico.

## Swagger

- http://localhost:8000/docs
- http://localhost:8000/openapi.json
