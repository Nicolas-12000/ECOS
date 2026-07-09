# Guía de Despliegue ECOS - Producción

Esta guía describe cómo desplegar ECOS en producción usando Render para el backend (RAG) y Vercel para el frontend.

## Arquitectura de Producción

```
Frontend (Vercel) → Backend RAG (Render) → Base de datos (Supabase/PostgreSQL)
```

## 1. Backend - Render (Solo RAG)

### Requisitos
- Cuenta en [Render](https://render.com)
- API Key de [Groq](https://console.groq.com) para el servicio RAG
- (Opcional) Base de datos Supabase o PostgreSQL

### Pasos para desplegar en Render

1. **Crear un nuevo servicio Web Service** en Render
2. **Conectar tu repositorio** de GitHub/GitLab
3. **Configurar las siguientes opciones**:
   - **Name**: `ecos-backend-rag`
   - **Environment**: `Python`
   - **Region**: `Oregon` (o tu región preferida)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements-prod.txt`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `.` (punto)

4. **Configurar Variables de Entorno** en Render Dashboard:

| Variable | Valor | Requerido | Descripción |
|----------|-------|-----------|-------------|
| `ENV` | `production` | Sí | Entorno de producción |
| `DEBUG` | `false` | Sí | Desactivar modo debug |
| `GROQ_API_KEY` | `tu-api-key` | Sí | API Key de Groq para RAG |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Sí | Modelo de Groq a usar |
| `CORS_ORIGINS` | `https://tu-frontend.vercel.app,http://localhost:3000` | Sí | Orígenes permitidos para CORS |
| `SUPABASE_URL` | `tu-url-supabase` | No | URL de Supabase (opcional) |
| `SUPABASE_ANON_KEY` | `tu-anon-key` | No | Key anónima de Supabase (opcional) |
| `DATABASE_URL` | `postgresql://...` | No | URL directa de PostgreSQL (opcional) |

5. **Hacer clic en "Create Web Service"**

### Verificación del Backend
- Una vez desplegado, visita: `https://ecos-backend-rag.onrender.com`
- Deberías ver la respuesta JSON con status "ok"
- Documentación Swagger: `https://ecos-backend-rag.onrender.com/docs`

## 2. Frontend - Vercel

### Requisitos
- Cuenta en [Vercel](https://vercel.com)
- URL del backend desplegado en Render

### Pasos para desplegar en Vercel

1. **Importar tu repositorio** en Vercel
2. **Configurar el proyecto**:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`

3. **Configurar Variables de Entorno** en Vercel Dashboard:

| Variable | Valor | Requerido | Descripción |
|----------|-------|-----------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://ecos-backend-rag.onrender.com` | Sí | URL del backend en Render |

4. **Hacer clic en "Deploy"**

### Verificación del Frontend
- Una vez desplegado, visita tu dominio de Vercel
- Verifica que el chat funcione correctamente
- Comprueba que las llamadas a la API se realicen al backend correcto

## 3. Variables de Entorno - Resumen

### Backend (Render)
```bash
ENV=production
DEBUG=false
GROQ_API_KEY=tu_api_key_aqui
GROQ_MODEL=llama-3.3-70b-versatile
CORS_ORIGINS=https://tu-frontend.vercel.app,http://localhost:3000
# Opcionales:
SUPABASE_URL=tu_url_supabase
SUPABASE_ANON_KEY=tu_anon_key
DATABASE_URL=postgresql://user:pass@host:port/db
```

### Frontend (Vercel)
```bash
NEXT_PUBLIC_API_URL=https://ecos-backend-rag.onrender.com
```

## 4. Verificaciones Post-Despliegue

### Backend
- [ ] API responde en `/` con status "ok"
- [ ] Endpoint `/api/v1/chat` funciona correctamente
- [ ] CORS configurado correctamente
- [ ] Variables de entorno cargadas correctamente

### Frontend
- [ ] Página carga sin errores
- [ ] Chat se conecta al backend correcto
- [ ] Todas las funcionalidades operativas
- [ ] No hay errores en la consola del navegador

### Comunicación
- [ ] Frontend puede hacer requests al backend
- [ ] No hay errores de CORS
- [ ] Las respuestas del backend son procesadas correctamente

## 5. Solución de Problemas

### CORS Errors
Si encuentras errores de CORS:
1. Verifica que `CORS_ORIGINS` en Render incluya la URL de tu frontend
2. Asegúrate de que no haya espacios en la lista de orígenes
3. Reinicia el servicio en Render después de cambiar variables

### Backend no responde
1. Revisa los logs en Render Dashboard
2. Verifica que todas las variables de entorno estén configuradas
3. Comprueba que el build se completó correctamente

### Frontend no se conecta
1. Verifica que `NEXT_PUBLIC_API_URL` esté configurada correctamente
2. Comprueba la consola del navegador para errores
3. Asegúrate de que el backend esté funcionando

## 6. Mantenimiento

### Actualizaciones
- **Backend**: Push a la rama `main` activará redeploy automático en Render
- **Frontend**: Push a la rama `main` activará redeploy automático en Vercel

### Monitoreo
- Render proporciona monitoreo básico y logs
- Vercel ofrece analytics y performance monitoring
- Configurar alertas para downtime en ambas plataformas

## 7. Consideraciones de Seguridad

1. **API Keys**: Nunca committear keys al repositorio
2. **CORS**: Limitar orígenes permitidos solo a los necesarios
3. **Variables**: Usar variables de entorno para configuración sensible
4. **Logs**: Revisar logs regularmente para detectar actividades sospechosas

## 8. Escalabilidad

### Backend (Render)
- Planes gratuitos tienen límites de uso
- Considerar upgrade a plan pago para producción real
- Configurar auto-scaling si es necesario

### Frontend (Vercel)
- Vercel maneja escalabilidad automáticamente
- Considerar CDN para assets estáticos
- Optimizar imágenes y bundles para mejor performance