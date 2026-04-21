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

## Swagger

- http://localhost:8000/docs
- http://localhost:8000/openapi.json
