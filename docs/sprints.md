# Plan de sprints (ECOS)

## Objetivo
Entregar una version solida y presentable de ECOS (nivel top), con pipeline robusto en PySpark, modelos validados, API estable, dashboard consistente y chatbot RAG integrado, todo reproducible y listo para demo tecnica.

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

- Codigo funcional en develop/main segun flujo.
- Pipeline reproducible (comando unico o script) sin pasos manuales.
- Validaciones de datos automatizadas (esquema, nulos, rangos, duplicados).
- Dataset versionado (snapshots o hash) y registro de cambios.
- Pruebas ejecutadas (pytest + validaciones de datos).
- Documentacion actualizada y demo reproducible.

## Estandares de documentacion y pruebas
- Pipeline de datos: PySpark + Parquet como formato principal.
- Validaciones: esquema, rangos, nulos, duplicados y consistencia temporal.
- API: Swagger/OpenAPI generado por FastAPI en /docs y /openapi.json.
- Documentos clave: docs/architecture.md, docs/data-dictionary.md, docs/api.md.
- Pruebas: pytest para API y data pipeline, validaciones de datos automatizadas.
- Power BI: PBIX con data model claro, medidas documentadas y refresh probado.

---

## Sprint 0 - Base y definicion
Objetivo: dejar el proyecto listo para producir datos con calidad, servirlos y documentar el plan tecnico con estandares de produccion.

### DE (paso a paso)
1. Definir esquema del dataset curado (semana, municipio, enfermedad) y documentarlo.
2. Implementar pipeline PySpark de ingesta minima (SIVIGILA + clima IDEAM).
3. Generar dataset curado v0 en Parquet y CSV en data/processed/.
4. Implementar validaciones automatas (esquema, nulos, rangos, duplicados).
5. Registrar version de datos (snapshot o hash) y data lineage basico.

### DS (paso a paso)
1. Baseline inicial (Prophet y/o XGBoost) con validacion temporal (walk-forward).
2. Definir metricas objetivo (MAE, RMSE, recall, precision) y umbrales.
3. Generar reporte de metricas y supuestos en docs/.

### Dev 1 (paso a paso)
1. API base con FastAPI, /health y estructura de rutas.
2. Configuracion de entorno y settings tipados.
3. Tests basicos (pytest) y logging estructurado.
4. Verificar Swagger en /docs y documentar ejemplo de uso.

### Dev 2 (paso a paso)
Objetivo: crear un dashboard base en Power BI con datos reales del curado v0.

Necesitas:
- Power BI Desktop instalado.
- Dataset curado v0 en CSV/Parquet.
- Esquema esperado del dataset curado (definido por DE).

Pasos:
1. Importar dataset curado v0 en Power BI (Get Data).
2. Definir tipos de datos correctos (fecha, texto, numero).
3. Crear modelo simple (tabla fact + medidas basicas).
4. Diseñar layout base:
	- Mapa por departamento.
	- Serie temporal de casos.
	- Filtros por enfermedad, departamento, rango de fecha.
5. Guardar PBIX con medidas documentadas.

Por que es importante:
- Permite validar el flujo de visualizacion desde el inicio.
- Reduce el riesgo de cambios tardios en el dashboard.

Entregables:
- Dataset curado v0 (Parquet/CSV) + validaciones automatas.
- Baseline con metricas iniciales y reporte.
- API base operativa + Swagger.
- PBIX inicial con datos reales.

Estado actual (Sprint 0):
- DE: completado (pipeline PySpark, curado v0, validaciones, snapshot/hash + lineage).
- DS: completado (baseline v0 + metricas).
- Dev 1: pendiente.
- Dev 2: pendiente.

---

## Sprint 1 - Datos y API robusta
Objetivo: consolidar el pipeline con mas fuentes, exponer datos reales y preparar predicciones iniciales con calidad.

### DE (paso a paso)
1. Integrar fuentes secundarias (vacunacion, movilidad, RIPS vista agregada).
2. Normalizar llaves (DANE) y reglas de union.
3. Versionar dataset curado v1 y generar snapshot.
4. Actualizar data dictionary en docs/data-dictionary.md.

### DS (paso a paso)
1. Modelo v1 con features exogenas (clima, movilidad, vacunacion, RIPS).
2. SHAP basico por variable clave y estabilidad temporal.
3. Reporte de metricas comparado con baseline.

### Dev 1 (paso a paso)
1. Endpoints /predict, /history, /signals (estructura estable).
2. Respuestas optimizadas para Power BI (CSV/JSON).
3. Tests de endpoints y manejo de errores comunes.
4. Documentacion de API en docs/api.md.

### Dev 2 (paso a paso)
Objetivo: conectar el dashboard a datos reales y publicar version v1 con medidas clave.

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
- Dashboard v1 con datos reales y medidas clave.
- Modelo v1 con metricas publicables.

---

## Sprint 2 - Senales tempranas + RAG
Objetivo: integrar senales tempranas con pipeline estable y habilitar el chatbot RAG con evaluacion basica.

### DE (paso a paso)
1. Pipeline de senales (trends + RSS) con agregacion semanal.
2. Normalizar senales por region y guardar en data/external/.
3. Validaciones de cobertura, duplicados y calidad.

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
Objetivo: consolidar modelo, data, dashboard y documentacion tecnica con estandares de presentacion.

### DE
- Versionado de datos y snapshots.
- Automatizar pipeline con scripts claros.
- Chequeos de regresion de datos.

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
Objetivo: dejar el proyecto listo para presentacion y despliegue con checklist tecnico.

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
