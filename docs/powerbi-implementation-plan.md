# Plan Técnico de Implementación: Power BI Dashboard (ECOS)

Este documento contiene el plan paso a paso y el código necesario para implementar el Dashboard v1 en Power BI Desktop utilizando los datos procesados de ECOS.

## 1. Ingesta y Limpieza (Power Query - Código M)

Al importar el CSV desde `data/processed/curated_weekly_csv/`, entra en **"Transform Data"** y usa este código en el **Editor Avanzado**.

> [!TIP]
> Asegúrate de ajustar la ruta del archivo en la variable `Source` según tu ubicación local.

```powerquery
let
    Source = Csv.Document(File.Contents("C:\Users\juanc\Desktop\UCC\Sexto semestre\HC\ECOS\data\processed\curated_weekly_csv\part-00000-40633e34-d0bd-4073-b2ec-8e51f385be11-c000.csv"), [Delimiter=",", Columns=17, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"epi_year", Int64.Type}, 
        {"epi_week", Int64.Type}, 
        {"week_start_date", type date}, 
        {"week_end_date", type date}, 
        {"cases_total", Int64.Type}, 
        {"temp_avg_c", type number}, 
        {"humidity_avg_pct", type number}, 
        {"precipitation_mm", type number}
    }),
    #"Replaced Errors" = Table.ReplaceErrorValues(#"Changed Type", {{"cases_total", 0}}),
    #"Filtered Rows" = Table.SelectRows(#"Replaced Errors", each ([cases_total] >= 0))
in
    #"Filtered Rows"
```

---

## 2. Modelo de Datos y Medidas (DAX)

Crea las siguientes medidas en una tabla de medidas dedicada para mantener el orden.

### A. Indicadores de Casos
```dax
// Total de casos acumulados
Total Casos = 
SUM('curated_weekly_csv'[cases_total])

// Casos de la semana anterior (para comparar)
Casos Semana Anterior = 
CALCULATE(
    [Total Casos],
    DATEADD(
        'curated_weekly_csv'[week_start_date],
        -7,
        DAY
    )
)

// Variación porcentual semanal
Variación Semanal % = 
VAR Diferencia = [Total Casos] - [Casos Semana Anterior]
RETURN 
IF(
    ISBLANK([Casos Semana Anterior]) || [Casos Semana Anterior] = 0,
    BLANK(),
    DIVIDE(Diferencia, [Casos Semana Anterior])
)
```

### B. Indicadores Climáticos
```dax
Promedio Temperatura = 
AVERAGE('curated_weekly_csv'[temp_avg_c])

Promedio Humedad = 
AVERAGE('curated_weekly_csv'[humidity_avg_pct])

Precipitación Total = 
SUM('curated_weekly_csv'[precipitation_mm])
```

### C. Lógica de Alerta (Semáforo)
```dax
Estado de Alerta = 
VAR VarPct = [Variación Semanal %]
RETURN
SWITCH(
    TRUE(),
    ISBLANK(VarPct), "⚪ Sin Datos",
    VarPct > 0.20, "🔴 Riesgo Alto (>20%)",
    VarPct > 0.05, "🟡 Incremento Ligero (>5%)",
    VarPct <= 0.05, "🟢 Estable"
)
```

---

## 3. Visualizaciones Sugeridas

| Visual | Datos | Propósito |
|---|---|---|
| **Mapa Coroplético** | `departamento_name` + `Total Casos` | Identificar hotspots regionales. |
| **Gráfico de Líneas** | `week_start_date` + `Total Casos` | Ver la tendencia temporal por enfermedad. |
| **Gráfico Combinado** | `Total Casos` (Barras) + `Promedio Temp` (Línea) | Correlación clima-epidemia. |
| **KPI Cards** | `Total Casos`, `Var Semanal %`, `Estado de Alerta` | Resumen ejecutivo rápido. |

---

## 4. Recomendaciones de Diseño Premium

- **Paleta de Colores**: Fondo oscuro (`#0F172A`) con acentos en cian y naranja, o blanco limpio con sombras suaves.
- **Interactividad**: Asegúrate de que los filtros de **Enfermedad** y **Departamento** afecten a todos los visuales.
- **Títulos**: Usa títulos descriptivos y dinámicos si es posible.
