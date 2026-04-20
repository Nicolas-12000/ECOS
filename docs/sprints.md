# Plan de sprints (ECOS)

## Objetivo
Entregar un MVP funcional de ECOS con prediccion temprana y un dashboard en Power BI, basado en datos abiertos, con API estable, pipeline reproducible y un chatbot RAG conectado.

## Supuestos
- El dashboard final se construye en Power BI.
- El frontend web se limita a paginas informativas o soporte para el chatbot.
- No se requiere inicio de sesion para el dashboard publico.
- El chatbot puede requerir un control liviano (API key o token) para evitar abuso.

## Roles
- Data Engineer (DE): ingesta, limpieza, normalizacion, versionado de datos.
- Data Scientist (DS): modelado, validacion, metricas, explicabilidad.
- Dev 1 (Backend): API, servicios, endpoints, integracion con Supabase.
- Dev 2 (BI/Frontend): Power BI, modelo de datos, dashboards, refresh.

## Definicion de terminado (Definition of Done)
Cada sprint debe cerrar con lo siguiente:

- Codigo funcional en main/develop segun flujo.
- Documentacion minima actualizada (README o docs/).
- Pruebas basicas ejecutadas (pytest y validaciones de datos).
- Demo reproducible con datos y endpoints activos.

## Estandares de documentacion y pruebas
- API: Swagger/OpenAPI generado por FastAPI en /docs y /openapi.json.
- Documentos clave: docs/architecture.md, docs/data-dictionary.md, docs/api.md.
- Pruebas: pytest para API y data pipeline, validaciones de esquema para datos.
- Power BI: PBIX con data model claro y medidas documentadas.

---

## Sprint 0 - Base y definicion
Objetivo: dejar el proyecto listo para producir datos, servirlos y documentar el plan tecnico.

### DE (paso a paso)
1. Definir esquema del dataset curado (granularidad semana, municipio, enfermedad).
2. Ingesta minima: SIVIGILA + clima con pipeline reproducible.
3. Guardar dataset curado v0 en data/processed/.
4. Crear validaciones de esquema (columnas, tipos, nulos).

### DS (paso a paso)
1. Baseline rapido (Prophet o XGBoost) con validacion temporal.
2. Definir metricas objetivo (MAE, RMSE, recall) y umbrales de alerta.
3. Guardar reporte inicial de metricas en docs/.

### Dev 1 (paso a paso)
1. API base con FastAPI, /health y estructura de rutas.
2. Configuracion de entorno (envs y settings).
3. Primer set de tests (pytest) para /health.
4. Verificar Swagger en /docs.

### Dev 2 (paso a paso)
Objetivo: crear un prototipo de dashboard en Power BI que sirva como plantilla para datos reales.

Necesitas:
- Power BI Desktop instalado.
- Un archivo de datos mock en CSV/Excel con columnas minimas: fecha/semana, departamento, municipio, enfermedad, casos.
- Esquema esperado del dataset curado (definido por DE).

Pasos:
1. Crear un archivo de datos mock con 50 a 100 filas y las columnas basicas.
2. Importar el archivo a Power BI (Get Data).
3. Definir tipos de datos correctos (fecha, texto, numero).
4. Crear un modelo de datos simple (una tabla fact, sin relaciones complejas).
5. Diseñar el layout base:
	- Mapa por departamento.
	- Serie temporal de casos.
	- Filtros por enfermedad, departamento, rango de fecha.
6. Guardar el archivo como PBIX en la carpeta /docs o /frontend (segun acuerdo del equipo).

Por que es importante:
- Permite validar el flujo de visualizacion desde el inicio.
- Reduce el riesgo de cambios tardios en el dashboard.

Entregables:
- Dataset curado v0 + validaciones.
- Baseline con metricas iniciales.
- API base operativa + Swagger.
- PBIX inicial con layout y modelo vacio.

---

## Sprint 1 - MVP de datos y API
Objetivo: exponer datos reales para Power BI y predicciones iniciales.

### DE (paso a paso)
1. Unir datasets secundarios (vacunacion o movilidad, segun disponibilidad).
2. Documentar data dictionary en docs/data-dictionary.md.
3. Versionar dataset curado v1 y dejar snapshot.

### DS (paso a paso)
1. Modelo v1 con features exogenas.
2. SHAP basico por variable clave.
3. Reporte de metricas y comparacion con baseline.

### Dev 1 (paso a paso)
1. Endpoints /predict, /history, /signals (estructura estable).
2. Salida en formato amigable para Power BI (CSV/JSON).
3. Tests de endpoints y errores comunes.
4. Documentacion de API en docs/api.md.

### Dev 2 (paso a paso)
Objetivo: conectar el dashboard a datos reales y publicar la version v1.

Necesitas:
- URL de la API o acceso a tablas en Supabase.
- Documentacion de endpoints o data dictionary.
- Credenciales si aplica (token o key).

Pasos:
1. Conectar Power BI a la fuente real:
	- Si es API: usar conector Web y pegar la URL.
	- Si es Supabase: usar conector PostgreSQL con credenciales.
2. Actualizar el modelo para usar datos reales.
3. Revisar tipos de datos y limpiar columnas que no se usan.
4. Crear medidas basicas (sum de casos, promedio por semana).
5. Construir el dashboard v1:
	- Mapa por departamento.
	- Serie temporal de casos.
	- Panel de indicadores (totales y variacion semanal).
6. Probar refresh y validar que no tarde mas de 1 a 2 minutos.
7. Guardar PBIX y subir version al repo.

Por que es importante:
- Asegura que Power BI recibe datos reales y confiables.
- Permite que el equipo vea el MVP funcionando.

Entregables:
- API de datos utilizable por Power BI.
- Dashboard v1 con datos reales.
- Modelo v1 con metricas publicables.

---

## Sprint 2 - Senales tempranas + RAG
Objetivo: integrar senales tempranas y habilitar el chatbot RAG.

### DE (paso a paso)
1. Pipeline de senales (trends + RSS) con agregacion semanal.
2. Normalizar senales por region y guardar en data/external/.
3. Validaciones de cobertura y calidad.

### DS (paso a paso)
1. Evaluar impacto de senales en recall.
2. Ajustar umbral de alerta.
3. Definir features finales para modelo v2.

### Dev 1 (paso a paso)
1. Endpoint /signals y versionado de senales.
2. Implementar servicio RAG (ingesta, embeddings, retrieval, respuesta).
3. Endpoint /chat con rate limit o API key.
4. Tests de RAG (respuesta valida, timeout, errores).

### Dev 2 (paso a paso)
Objetivo: mostrar senales tempranas y (si aplica) habilitar vista de chatbot.

Necesitas:
- Dataset de senales con columnas: fecha/semana, region, fuente, score.
- Definicion de como se calcula el score de senales.

Pasos:
1. Conectar la tabla de senales al modelo de Power BI.
2. Crear visualizaciones:
	- Linea de senales en el tiempo.
	- Comparativo senales vs casos.
3. Agregar filtros por fuente (trends, RSS).
4. Si el chatbot se expone en web, coordinar con Dev 1 el endpoint /chat y mostrar un enlace o panel informativo en el dashboard.

Por que es importante:
- Permite justificar la prediccion con senales tempranas.
- Mejora interpretabilidad para usuarios no tecnicos.

Entregables:
- Senales integradas en dataset curado.
- Chatbot RAG funcional.
- Dashboard con panel de senales.

---

## Sprint 3 - Estabilizacion y narrativa
Objetivo: consolidar modelo, data, dashboard y documentacion tecnica.

### DE
- Versionado de datos y snapshots.
- Automatizar pipeline con scripts claros.

### DS
- Modelo v2 final y reporte de metricas.
- Explicabilidad final por region.

### Dev 1
- Ajustes de performance y cache basico.
- Cobertura de tests minima (API + data).
- Documentacion final de API y endpoints.

### Dev 2
Objetivo: dejar el dashboard final listo para demo y presentacion.

Necesitas:
- PBIX v1 con datos reales.
- Lista de preguntas clave que el jurado o usuarios haran.

Pasos:
1. Refinar narrativa del dashboard (titulo, textos explicativos, leyendas claras).
2. Revisar que los filtros sean utiles y no redundantes.
3. Documentar medidas y el modelo de datos dentro del PBIX.
4. Preparar 2 o 3 historias de uso (ejemplo: brote en region X).

Por que es importante:
- La demo debe ser clara para un usuario no tecnico.
- Una buena narrativa aumenta la puntuacion en usabilidad.

Entregables:
- PBIX final.
- API documentada (Swagger + docs/api.md).
- Reporte de metricas y metodologia.

---

## Sprint 4 - Empaque y entrega
Objetivo: dejar el proyecto listo para presentacion y despliegue.

### DE
- Scripts de carga automatica y README de datos.

### DS
- Informe tecnico corto para concurso.

### Dev 1
- Docker y guia de despliegue.
- Checklist de configuracion y variables de entorno.

### Dev 2
Objetivo: publicar el dashboard y dejar material listo para entrega.

Necesitas:
- PBIX final.
- Acceso a Power BI Service (si se publica en la nube).

Pasos:
1. Publicar el PBIX en Power BI Service o preparar link local.
2. Configurar refresh si la publicacion es online.
3. Tomar capturas clave (mapa, series, senales).
4. Guardar capturas en docs/.
5. Validar la demo completa con el equipo.

Por que es importante:
- Asegura que el jurado vea el resultado final sin friccion.
- Las capturas ayudan en presentaciones y reportes.

Entregables:
- Documentacion completa y demo estable.
- Paquete final para evaluacion.

---

## Notas sobre inicio de sesion
No exigir inicio de sesion para el dashboard principal. Si el chatbot se expone, usar un control liviano (token o API key) para evitar abuso. Si se requiere autenticar, hacerlo solo para el endpoint /chat.
