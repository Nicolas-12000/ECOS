# Checklist de Verificación Post-Despliegue ECOS

## ✅ Backend (Render)

### Configuración Inicial
- [ ] Servicio creado en Render con nombre `ecos-backend-rag`
- [ ] Repositorio conectado correctamente
- [ ] Build completado sin errores
- [ ] Servicio en estado "Running"

### Variables de Entorno
- [ ] `ENV=production` configurado
- [ ] `DEBUG=false` configurado
- [ ] `GROQ_API_KEY` configurada (valor válido)
- [ ] `GROQ_MODEL` configurado como `llama-3.3-70b-versatile`
- [ ] `CORS_ORIGINS` incluye URL del frontend
- [ ] Variables de base de datos configuradas (si aplica)

### Funcionalidad API
- [ ] Endpoint raíz (`/`) responde con status "ok"
- [ ] Documentación Swagger disponible en `/docs`
- [ ] Endpoint `/health` responde correctamente
- [ ] Endpoint `/api/v1/chat` acepta POST requests
- [ ] RAG funciona con preguntas de prueba

### Performance
- [ ] Tiempo de respuesta < 5 segundos para endpoints simples
- [ ] Tiempo de respuesta < 30 segundos para RAG complejo
- [ ] Memoria dentro de límites del plan
- [ ] CPU dentro de límites del plan

## ✅ Frontend (Vercel)

### Configuración Inicial
- [ ] Proyecto importado en Vercel
- [ ] Root directory configurado como `frontend`
- [ ] Build completado sin errores
- [ ] Deploy marcado como "Ready"

### Variables de Entorno
- [ ] `NEXT_PUBLIC_API_URL` configurada con URL del backend
- [ ] URL apunta al backend correcto en Render

### Funcionalidad Frontend
- [ ] Página principal carga sin errores
- [ ] Navegación funciona correctamente
- [ ] Componente de chat visible y funcional
- [ ] No hay errores en consola del navegador
- [ ] Estilos CSS cargados correctamente

### Comunicación con Backend
- [ ] Chat envía preguntas al backend
- [ ] Respuestas del backend se muestran correctamente
- [ ] No hay errores de CORS en las requests
- [ ] Loading states funcionan correctamente

## ✅ Integración Completa

### Flujo End-to-End
- [ ] Usuario puede hacer pregunta en el chat
- [ ] Pregunta se envía al backend en Render
- [ ] Backend procesa la pregunta con RAG
- [ ] Respuesta regresa al frontend
- [ ] Respuesta se muestra al usuario

### Seguridad
- [ ] CORS configurado correctamente
- [ ] No hay información sensible expuesta
- [ ] API Keys no están en código fuente
- [ ] Logs no contienen datos sensibles

### Monitoreo
- [ ] Logs de Render accesibles y sin errores críticos
- [ ] Logs de Vercel accesibles y sin errores críticos
- [ ] Métricas de performance dentro de rangos normales
- [ ] Alertas configuradas para downtime (si aplica)

## ✅ Pruebas Específicas

### Pruebas de Chat
- [ ] Pregunta simple: "¿Qué es ECOS?"
- [ ] Pregunta específica: "Riesgo de dengue en Antioquia"
- [ ] Pregunta comparativa: "Malaria 2024 vs 2023"
- [ ] Pregunta con contexto: "Brotes en el Pacífico"

### Pruebas de Performance
- [ ] Tiempo de carga inicial < 3 segundos
- [ ] Tiempo de respuesta chat < 10 segundos
- [ ] Memoria del navegador estable
- [ ] No hay memory leaks evidentes

### Pruebas de Error
- [ ] Backend offline → Frontend muestra error apropiado
- [ ] Pregunta vacía → Manejo adecuado
- [ ] Timeout requests → Manejo adecuado
- [ ] Network errors → Manejo adecuado

## ✅ Documentación

### Archivos Creados
- [ ] `requirements-prod.txt` - Dependencias optimizadas
- [ ] `render.yaml` - Configuración Render
- [ ] `gunicorn.conf.py` - Configuración Gunicorn (opcional)
- [ ] `vercel.json` - Configuración Vercel
- [ ] `.env.production.example` - Ejemplo variables frontend
- [ ] `DEPLOYMENT.md` - Guía completa de despliegue
- [ ] `DEPLOYMENT_CHECKLIST.md` - Este checklist

### Actualizaciones
- [ ] `backend/app/core/config.py` - CORS mejorado
- [ ] `backend/app/main.py` - Usa resolved_cors_origins
- [ ] `frontend/next.config.ts` - Configuración producción

## ✅ Pasos Finales

### Post-Despliegue
- [ ] Anotar URLs de producción:
  - Backend: `https://ecos-backend-rag.onrender.com`
  - Frontend: `https://tu-frontend.vercel.app`
- [ ] Probar desde diferentes dispositivos
- [ ] Verificar en diferentes navegadores
- [ ] Documentar cualquier issue encontrado

### Mantenimiento
- [ ] Establecer schedule para revisión periódica
- [ ] Configurar backups (si aplica)
- [ ] Documentar procedimientos de recovery
- [ ] Establecer contactos para soporte

---

**Estado Final**: □ No Iniciado | □ En Progreso | ✅ Completado | ⚠️ Con Issues | ❌ Fallido

**Fecha de Verificación**: _______________

**Responsable**: _______________

**Notas**:
________________________________________________________________
________________________________________________________________
________________________________________________________________