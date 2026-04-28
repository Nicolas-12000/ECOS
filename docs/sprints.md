# Plan final de entrega (ECOS)

## Objetivo
Cerrar ECOS como una version definitiva, reproducible y presentable para demo tecnica: datos curados, prediccion operativa, señales tempranas, explicabilidad, interfaz web y documentacion final.

## Criterios de cierre
- Un solo lenguaje de producto: final, definitivo y consistente en toda la documentacion publica.
- Pipeline reproducible con un comando o script principal.
- Datos curados versionados por snapshot y lineage.
- API estable con prediccion, historial y señales tempranas.
- Experiencia web clara para consulta de prediccion, contexto y explicación.
- Evidencia de pruebas y validaciones de datos.

## Estado consolidado

### Ya resuelto
- Ingesta y curado semanal con PySpark.
- Dataset consolidado en Parquet/CSV.
- Validaciones de datos y snapshot.
- Modelo predictivo con horizonte de 1 a 4 semanas.
- API base con salud, historia, predicción y señales.
- Base documental de datos, API y pipeline.
- Dependencias y entornos unificados en un flujo canónico.

### Falta cerrar
- Asistente conversacional RAG con retrieval semántico totalmente validado en local.
- Cobertura de pruebas más amplia para API, datos y flujo de predicción; ya existe cobertura base para chat y predicción recursiva.
- Integración completa con Supabase/pgvector para persistir embeddings.
- Empaque final de demo local, instrucciones de arranque y capturas.
- Limpieza terminológica en documentos públicos para eliminar labels intermedios.

## Componentes finales

### Datos
- Fuente principal: SIVIGILA curado semanal.
- Fuentes de soporte: clima, vacunación, RIPS y movilidad.
- Señales tempranas: Trends y RSS agregados semanalmente.

### Predicción
- Salida por municipio, enfermedad y horizonte de 1 a 4 semanas.
- Umbral de brote definido por salud pública.
- Explicación mediante variables históricas, exógenas y SHAP.

### RAG
- Propósito: responder preguntas operativas sobre riesgo, historial, señales y contexto.
- Fuentes: dataset curado, predicciones, señales tempranas y documentación de negocio.
- Requisito: cada respuesta debe incluir contexto y origen de datos.
- Estado actual: ya existe un índice semántico local y un loader para Supabase; falta cerrar la prueba de extremo a extremo.

### Pruebas
- Ya hay tests para `/health`, `/chat` y el comportamiento recursivo de `predict_cases`.
- Falta ampliar cobertura para errores de datos, fallback de modelo y casos límite de RAG.

### Web
- Landing pública con visión del sistema.
- Acceso directo a predicción, señales y documentación API.
- Panel conversacional para consulta asistida cuando el módulo RAG esté conectado.

## Entregables finales
- Documento técnico actualizado.
- API documentada en FastAPI.
- Diccionario de datos consolidado.
- Instrucciones de demo local y verificación.
- Paquete de dependencias y envs simplificado a un flujo principal.

Por que es importante:
- Asegura que el jurado vea el resultado final sin friccion.
- Las capturas ayudan en presentaciones y reportes.

Entregables:
- Documentacion completa y demo estable.
- Paquete final para evaluacion.

---

## Notas sobre inicio de sesion
No exigir inicio de sesion para el dashboard principal. Si el chatbot se expone, usar un control liviano (token o API key) para evitar abuso. Si se requiere autenticar, hacerlo solo para el endpoint /chat.
