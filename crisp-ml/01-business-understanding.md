# Fase 1: Comprensión del Negocio

## 1. Contexto Organizacional

**Organización:** Ministerio de Salud y Protección Social / Instituto Nacional de Salud (INS)

**Usuarios finales:**
- Secretarías de Salud Departamentales (32 instituciones)
- Equipos de vigilancia epidemiológica del INS
- Centros de Operaciones de Emergencia (COE)
- Tomadores de decisión en respuesta sanitaria

**Contexto:** Colombia enfrenta brotes cíclicos de enfermedades transmitidas por vectores (dengue, chikungunya, zika, malaria) con rezago estructural de 2-4 semanas entre ocurrencia de casos y notificación oficial a través del sistema SIVIGILA.

---

## 2. Problema de Negocio

### 2.1 Situación Actual
- **Rezago:** 2-4 semanas entre casos ocurridos y alertas generadas por SIVIGILA
- **Impacto:** Brotes llegan a fase de expansión comunitaria antes de ser detectados
- **Consecuencias:** Mayor número de casos, hospitalizaciones, muertes prevenibles
- **Recursos:** Respuesta tardía, sub-utilización de capacidad de contención local

### 2.2 Oportunidad
- Colombia tiene portal de datos abiertos (datos.gov.co) con históricos epidemiológicos desde 2007
- Señales tempranas disponibles (Google Trends, medios locales) preceden 1-3 semanas a reportes oficiales
- Infraestructura de salud digital está en expansión

### 2.3 Objetivo de Negocio
**Reducir el rezago de alertas epidemiológicas de 2-4 semanas a 0-2 semanas mediante un sistema predictivo basado en datos abiertos y señales tempranas.**

---

## 3. Criterios de Éxito

| Métrica | Target | Umbral Aceptable |
|---------|--------|------------------|
| **Anticipación promedio** | 2-3 semanas | Mínimo 1.5 semanas |
| **Sensibilidad (Recall)** | 85%+ | Mínimo 75% |
| **Especificidad** | 70%+ | Mínimo 60% |
| **Adopción** | 15+ secretarías usando | Mínimo 10 instituciones |
| **Cobertura geográfica** | Nacional + municipal | Mínimo nacional |

---

## 4. Requisitos de Negocio

### 4.1 Funcionales
1. Predicción de probabilidad de brote a 2 y 4 semanas por municipio/departamento
2. Identificación de municipios en mayor riesgo (top 10 por semana)
3. Integración de múltiples fuentes de datos (vigilancia + clima + movilidad + señales tempranas)
4. Explicabilidad de predicciones (qué variables causaron el riesgo)
5. Alertas automáticas vía correo a secretarías de salud
6. Chat conversacional en lenguaje natural para consultas epidemiológicas

### 4.2 No Funcionales
- **Reproducibilidad:** Código abierto, ejecutable en entorno local (laptop con Docker)
- **Escalabilidad:** Capacidad de procesar históricos de 15+ años con millones de registros
- **Confiabilidad:** Disponibilidad 99% para consultas (no requiere uptime continuo)
- **Cumplimiento:** Estándares CRISP-ML, ética en datos, no recolección de datos personales

---

## 5. Restricciones y Supuestos

### 5.1 Restricciones
- **Temporales:** Históricos SIVIGILA disponibles desde 2007 (con variaciones en cobertura pre-2010)
- **Geográficas:** Granularidad municipal en SIVIGILA, pero variabilidad en reporte por departamento
- **Técnicas:** Scraping ético de Google Trends (límites de rate) y feeds RSS públicos
- **Legales:** No se procesan datos personales; solo datos agregados públicos

### 5.2 Supuestos
1. Datos SIVIGILA son fuente de verdad (aunque atrasados)
2. Google Trends refleja comportamiento de búsqueda poblacional correlacionado con sintomatología real
3. Medios locales reportan alertas epidemiológicas antes que sistema central
4. Modelo predictivo puede usar series temporales + variables exógenas (no requiere variables forward-looking)
5. Disponibilidad de datos clientes (MinSalud, INS) para validación en producción

---

## 6. Alineación Estratégica

### 6.1 Hoja de Ruta Nacional
- **CONPES 4073 (2021):** Política Nacional de Vigilancia Epidemiológica
- **Hoja de Ruta Sectorial de Salud 2025-2026:** Fortalecimiento de la respuesta temprana a brotes
- **ODS 3:** Salud y bienestar — prevención de enfermedades transmisibles

### 6.2 Capacidades Existentes
- INS tiene infraestructura de datos e personal científico
- Secretarías departamentales tienen equipos de epidemiología y acceso a internet
- Ministerio tiene presupuesto para soluciones de TI en vigilancia

---

## 7. Riesgos Identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|--------|-----------|
| Baja adopción por usuarios finales | Media | Alto | Capacitación, interfaz amigable, validación local |
| Cambios en patrón de búsqueda/medios post-pandemia | Media | Medio | Re-entrenamiento periódico de modelos |
| Datos SIVIGILA incompletos en períodos específicos | Baja | Medio | Imputación robusta, validación cruzada temporal |
| Cambio de API de Google Trends | Baja | Alto | Monitoreo de TOS, feedback loop con infraestructura |

---

## 8. Cronograma de Entrega

| Fase | Duración | Entregable |
|------|----------|-----------|
| **Sprint 0** | 1-2 semanas | Pipeline Spark + modelos base + API /health |
| **Sprint 1** | 2-3 semanas | APIs completas + dashboard base |
| **Sprint 2** | 2-3 semanas | Chat RAG + alertas + SHAP explicabilidad |
| **Validación** | 1 semana | Testing con INS + secretarías piloto |
| **Despliegue** | Continuo | Demo + documentación + registros en datos.gov.co |

---

## 9. Glosario

- **SIVIGILA:** Sistema Nacional de Vigilancia en Salud Pública
- **DANE:** Departamento Administrativo Nacional de Estadística (códigos municipales)
- **Brote:** Incremento de casos sobre línea base esperada para zona y período
- **Señal temprana:** Indicador que precede detección oficial de brote
- **Walk-forward validation:** Validación temporal respetando secuencia histórica

