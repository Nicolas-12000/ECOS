# Contexto de Trabajo ECOS

## Qué estamos haciendo

Estamos cerrando ECOS como una versión final, manteniendo solo lo que aporta al producto operativo:
- Predicción epidemiológica con el modelo final.
- Asistente conversacional RAG que combine documentación, histórico y señales.
- Documentación pública limpia y consistente.

## Qué no estamos tocando ahora

- Frontend.
- Dashboard de Power BI.

## Cómo estamos construyendo el RAG

1. Partimos de una pregunta del usuario.
2. Extraemos enfermedad y territorio si aparecen.
3. Recuperamos fragmentos relevantes de la documentación del proyecto.
4. Mezclamos contexto documental con histórico y señales curadas.
5. Si hay municipio y enfermedad, añadimos una predicción operativa de 2 semanas.
6. Devolvemos una respuesta con fuentes para que sea trazable.

## Cómo estamos construyendo la predicción

1. El modelo final se carga desde `models/final_model.joblib`.
2. Se arma un vector de entrada con lags, clima y variables exógenas.
3. Se alinea con las columnas que el modelo espera.
4. Se generan predicciones por semana con umbral de brote.
5. El mismo motor se reutiliza tanto en el endpoint de predicción como en el chat.

## Estado actual

- La API ya expone `health`, `predict`, `history`, `signals` y `chat`.
- El modelo final comparte helpers comunes de ingeniería de variables.
- El chat ya puede responder con contexto documental y con salida del modelo.

## Pendientes reales

- Afinar el ranking de recuperación del RAG con secciones más semánticas.
- Mejorar cobertura de pruebas sobre el servicio de predicción compartido.
- Cerrar el empaque de demo local y el documento de arranque.

## Regla de trabajo

Si un archivo menciona versiones intermedias, se conserva solo si es un respaldo interno. La documentación pública debe hablar de ECOS final y del flujo operativo actual.