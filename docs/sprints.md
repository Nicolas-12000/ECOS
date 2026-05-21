# Plan final de entrega (ECOS)

## Objetivo
Cerrar ECOS como una versión definitiva, reproducible y presentable para demo técnica: datos curados, predicción operativa, señales tempranas, explicabilidad, interfaz web y documentación final.

## Criterios de cierre
- Pipeline reproducible con un comando o script principal.
- Datos curados versionados por snapshot y lineage.
- API estable con predicción, historial, señales tempranas y chat asistido.
- Experiencia web clara para consulta de predicción, contexto y explicación.
- Evidencia de pruebas y validaciones de datos.
- Dashboard Power BI conectado a datos procesados.

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

### Web
- Landing pública con visión del sistema.
- Acceso directo a predicción, señales y documentación API.
- Panel conversacional para consulta asistida.

### Dashboard BI
- Power BI conectado a datos curados en CSV/Parquet.
- Visualización de tendencias departamentales y municipales.

## Entregables finales
- Documento técnico actualizado.
- API documentada en FastAPI.
- Diccionario de datos consolidado.
- Instrucciones de demo local y verificación.
- Dashboard Power BI con datos curados.

## Notas sobre inicio de sesión
No exigir inicio de sesión para el dashboard principal. Si el chatbot se expone, usar un control liviano (token o API key) para evitar abuso. Si se requiere autenticar, hacerlo solo para el endpoint /chat.
