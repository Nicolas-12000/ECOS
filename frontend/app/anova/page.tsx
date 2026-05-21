"use client"

import { useState, useEffect } from "react"
import { Badge } from "@/components/ui/Badge"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { LottieLoader } from "@/components/ui/LottieLoader"
import {
  BarChart,
  HelpCircle,
  BookOpen,
  ArrowRightLeft,
  CheckCircle2,
  AlertCircle,
  Database,
  Info,
  Scale,
  CalendarDays,
  LineChart as LineChartIcon
} from "lucide-react"

// Color scheme matching ECOS Boston Clay
const YEAR_COLORS: Record<string, string> = {
  "0": "#B8422E", // Boston Clay Red
  "1": "#039855", // Success Green
  "2": "#DC6803", // Warning Orange
  "3": "#2563EB", // Info Blue
  "4": "#7C3AED", // Purple
  "5": "#0891B2", // Cyan
}

// Available years by table
const TABLE_YEARS = {
  fact_core_weekly: Array.from({ length: 16 }, (_, i) => 2007 + i), // 2007 - 2022
  dengue_kaggle_dataset: Array.from({ length: 13 }, (_, i) => 2007 + i), // 2007 - 2019
  anova_dataset: Array.from({ length: 12 }, (_, i) => 2011 + i), // 2011 - 2022
}

type TableType = "fact_core_weekly" | "dengue_kaggle_dataset" | "anova_dataset"
type DiseaseType = "dengue" | "zika" | "malaria" | "chikungunya"

export default function AnovaPage() {
  const [tables, setTables] = useState<TableType[]>(["fact_core_weekly"])
  const [disease, setDisease] = useState<DiseaseType>("dengue")
  const [selectedYears, setSelectedYears] = useState<number[]>([2015, 2016, 2017, 2019])
  const [transform, setTransform] = useState<boolean>(false)

  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [hoveredWeek, setHoveredWeek] = useState<number | null>(null)

  // Fetch ANOVA results whenever controls change
  useEffect(() => {
    async function fetchAnova() {
      if (selectedYears.length < 1 || tables.length < 1) {
        setError("Por favor, selecciona al menos una tabla y un año.")
        setData(null)
        setLoading(false)
        return
      }

      if (selectedYears.length * tables.length < 3) {
        setError("Se requieren al menos 3 grupos (combinación de tablas y años) para el análisis.")
        setData(null)
        setLoading(false)
        return
      }

      setLoading(true)
      setError(null)

      try {
        const sortedYears = [...selectedYears].sort((a, b) => a - b)
        const yearsParam = sortedYears.join(",")
        const tablesParam = tables.join(",")
        const url = `/api/dengue?years=${yearsParam}&tables=${tablesParam}&disease=${disease}&transform=${transform}`

        // Fetch from API
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
        const res = await fetch(`${apiBase}${url}`)
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}))
          throw new Error(errData.detail || "Error al obtener los datos del servidor.")
        }

        const json = await res.json()
        setData(json)
      } catch (err: any) {
        setError(err.message || "Error al conectar con la API de análisis estadístico.")
      } finally {
        setLoading(false)
      }
    }

    fetchAnova()
  }, [tables, selectedYears, disease, transform])

  const handleDiseaseChange = (newDisease: DiseaseType) => {
    setDisease(newDisease)
    if (newDisease !== "dengue") {
      // For other diseases, only fact_core_weekly is allowed
      setTables(["fact_core_weekly"])
    }
  }

  const handleTableToggle = (tableId: TableType) => {
    if (disease !== "dengue" && tableId !== "fact_core_weekly") return

    if (tables.includes(tableId)) {
      if (tables.length > 1) {
        setTables(tables.filter(t => t !== tableId))
      }
    } else {
      setTables([...tables, tableId])
    }
  }

  const handleYearToggle = (year: number) => {
    if (selectedYears.includes(year)) {
      if (selectedYears.length * tables.length > 3 || selectedYears.length > 1) {
        setSelectedYears(selectedYears.filter(y => y !== year))
      }
    } else {
      setSelectedYears([...selectedYears, year])
    }
  }

  // Helper to format p-value
  const formatPValue = (p: number | null | undefined) => {
    if (p === null || p === undefined) return "N/A"
    if (p < 0.00001) return "< 0.00001 (Altamente Significativo)"
    const formatted = p.toFixed(5)
    if (p < 0.05) return `${formatted} (Significativo)`
    return `${formatted} (No Significativo)`
  }

  // ═══════════════ RENDER CUSTOM SVG CHART ═══════════════
  const renderSvgChart = () => {
    if (!data || !data.chart_data || data.chart_data.length === 0) return null

    const chartData = data.chart_data
    const groups = data.metadata.analyzed_groups

    // SVG Dimensions
    const width = 800
    const height = 300
    const paddingLeft = 60
    const paddingRight = 20
    const paddingTop = 20
    const paddingBottom = 40

    // Find Max Value for Scaling Y
    let maxVal = 0
    chartData.forEach((row: any) => {
      groups.forEach((g: string) => {
        if (row[g] !== undefined && row[g] > maxVal) {
          maxVal = row[g]
        }
      })
    })
    if (maxVal === 0) maxVal = 1

    // Scale helpers
    const getX = (week: number) => {
      // weeks go from 1 to 53
      return paddingLeft + ((week - 1) / 52) * (width - paddingLeft - paddingRight)
    }

    const getY = (val: number | null | undefined) => {
      if (val === null || val === undefined) return height - paddingBottom
      return height - paddingBottom - (val / maxVal) * (height - paddingTop - paddingBottom)
    }

    // Colors mapper for groups index
    const getGroupColor = (g: string) => {
      const idx = groups.indexOf(g)
      return YEAR_COLORS[String(idx % 6)]
    }

    // Grid lines count
    const yTicks = 4
    const xTicks = [1, 10, 20, 30, 40, 50, 53]

    return (
      <div className="relative w-full overflow-x-auto">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full min-w-[700px] h-auto select-none overflow-visible">
          {/* Background Grid Lines (Horizontal) */}
          {Array.from({ length: yTicks + 1 }).map((_, i) => {
            const val = (maxVal / yTicks) * i
            const y = getY(val)
            return (
              <g key={`grid-y-${i}`}>
                <line
                  x1={paddingLeft}
                  y1={y}
                  x2={width - paddingRight}
                  y2={y}
                  stroke="var(--color-border)"
                  strokeDasharray="3,3"
                  strokeWidth="1"
                />
                <text
                  x={paddingLeft - 10}
                  y={y + 4}
                  textAnchor="end"
                  className="text-[10px] fill-(--color-secondary) font-mono"
                >
                  {val >= 1000 ? `${(val / 1000).toFixed(1)}k` : Math.round(val)}
                </text>
              </g>
            )
          })}

          {/* Grid Lines (Vertical for select weeks) */}
          {xTicks.map((week) => {
            const x = getX(week)
            return (
              <g key={`grid-x-${week}`}>
                <line
                  x1={x}
                  y1={paddingTop}
                  x2={x}
                  y2={height - paddingBottom}
                  stroke="var(--color-border)"
                  strokeDasharray="3,3"
                  strokeWidth="1"
                />
                <text
                  x={x}
                  y={height - paddingBottom + 18}
                  textAnchor="middle"
                  className="text-[10px] fill-(--color-secondary) font-mono"
                >
                  Sem {week}
                </text>
              </g>
            )
          }
          )}

          {/* Draw Group Lines */}
          {groups.map((g: string) => {
            const color = getGroupColor(g)
            let pathD = ""

            chartData.forEach((row: any, idx: number) => {
              const week = row.week
              const val = row[g]
              if (val !== undefined && val !== null) {
                const px = getX(week)
                const py = getY(val)
                if (pathD === "") {
                  pathD += `M ${px} ${py}`
                } else {
                  pathD += ` L ${px} ${py}`
                }
              }
            })

            return (
              <path
                key={`line-${g}`}
                d={pathD}
                fill="none"
                stroke={color}
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="transition-all duration-300 hover:stroke-[3.5px] cursor-pointer"
              />
            )
          })}

          {/* Interactive Hover Bar */}
          {hoveredWeek !== null && (
            <g>
              <line
                x1={getX(hoveredWeek)}
                y1={paddingTop}
                x2={getX(hoveredWeek)}
                y2={height - paddingBottom}
                stroke="var(--color-border-strong)"
                strokeWidth="1.5"
              />

              {/* Highlight points on lines */}
              {groups.map((g: string) => {
                const color = getGroupColor(g)
                const row = chartData.find((r: any) => r.week === hoveredWeek)
                const val = row ? row[g] : null
                if (val !== null && val !== undefined) {
                  return (
                    <circle
                      key={`dot-${g}`}
                      cx={getX(hoveredWeek)}
                      cy={getY(val)}
                      r="4.5"
                      fill="var(--color-surface)"
                      stroke={color}
                      strokeWidth="2"
                    />
                  )
                }
                return null
              })}
            </g>
          )}

          {/* Invisible interactive vertical segments for hover */}
          {chartData.map((row: any) => {
            const week = row.week
            const x = getX(week)
            return (
              <rect
                key={`rect-hover-${week}`}
                x={x - (width - paddingLeft - paddingRight) / 104}
                y={paddingTop}
                width={(width - paddingLeft - paddingRight) / 52}
                height={height - paddingTop - paddingBottom}
                fill="transparent"
                className="cursor-crosshair"
                onMouseEnter={() => setHoveredWeek(week)}
                onMouseLeave={() => setHoveredWeek(null)}
              />
            )
          })}
        </svg>

        {/* Dynamic Tooltip on Hover */}
        {hoveredWeek !== null && (
          <div className="absolute top-2 right-2 bg-(--color-surface) border border-(--color-border-strong) rounded-md p-3 shadow-md text-xs z-20 min-w-[200px] animate-fade-in">
            <p className="font-bold text-(--color-primary) border-b border-(--color-border) pb-1 mb-2 font-display">
              Semana Epidemiológica {hoveredWeek}
            </p>
            <div className="space-y-1.5">
              {groups.map((g: string) => {
                const color = getGroupColor(g)
                const row = chartData.find((r: any) => r.week === hoveredWeek)
                const val = row ? row[g] : null
                return (
                  <div key={`tooltip-row-${g}`} className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: color }} />
                      <span className="font-semibold text-(--color-primary) text-[10px]">{g}</span>
                    </div>
                    <span className="font-mono text-(--color-secondary)">
                      {val !== null && val !== undefined ? `${Math.round(val).toLocaleString()}` : "S.D."}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    )
  }

  // ═══════════════ MAIN COMPONENT ═══════════════
  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-10 max-w-7xl min-h-screen flex flex-col gap-8">

      {/* Header Section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end border-b border-(--color-border-strong) pb-6 gap-4">
        <div>
          <div className="inline-flex items-center gap-2 mb-2">
            <Badge variant="outline" className="text-(--color-tertiary) px-2.5 py-0.5 border-(--color-tertiary-glow)">
              <CalendarDays className="w-3.5 h-3.5 mr-1" />
              ANÁLISIS DE GRUPOS ANUALES
            </Badge>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-(--color-primary) flex items-center gap-3">
            <Scale className="text-(--color-tertiary) w-8 h-8 md:w-9 md:h-9" />
            Comparación Multianual Dengue (ANOVA)
          </h1>
          <p className="text-(--color-secondary) mt-2 max-w-3xl text-base">
            Ejecuta pruebas de varianza multianuales para comprobar de manera estadísticamente rigurosa
            si la severidad del dengue difiere entre distintos periodos anuales históricos en Colombia.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

        {/* Left Side: Parameters / Controls (4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-lg flex items-center gap-2">
                <Database className="w-4 h-4 text-(--color-tertiary)" />
                Parámetros de Control
              </CardTitle>
              <CardDescription>
                Define los datasets y variables de la prueba estadística
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-5">

              {/* Disease Selector */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold font-display uppercase tracking-wider text-(--color-primary)">
                  Enfermedad
                </label>
                <select
                  value={disease}
                  onChange={(e) => handleDiseaseChange(e.target.value as DiseaseType)}
                  className="w-full bg-(--color-background) border border-(--color-border) rounded-sm px-3 py-2 text-sm font-medium text-(--color-primary) focus:border-(--color-border-focus) focus:outline-none"
                >
                  <option value="dengue">Dengue</option>
                  <option value="zika">Zika</option>
                  <option value="malaria">Malaria</option>
                  <option value="chikungunya">Chikungunya</option>
                </select>
              </div>

              {/* Table Selector (Multiple) */}
              <div className="flex flex-col gap-1.5 border-t border-(--color-border) pt-4">
                <label className="text-xs font-bold font-display uppercase tracking-wider text-(--color-primary)">
                  Orígenes de Datos (Tablas)
                </label>
                <div className="flex flex-col gap-2">
                  {[
                    { id: "fact_core_weekly", label: "fact_core_weekly (ECOS)", available: true },
                    { id: "dengue_kaggle_dataset", label: "dengue_kaggle_dataset (Kaggle)", available: disease === "dengue" },
                    { id: "anova_dataset", label: "anova_dataset (Analytics)", available: disease === "dengue" },
                  ].map((t) => (
                    <div key={t.id} className={`flex items-center gap-2 ${!t.available ? "opacity-50" : ""}`}>
                      <input
                        type="checkbox"
                        id={`table-${t.id}`}
                        checked={tables.includes(t.id as TableType)}
                        onChange={() => handleTableToggle(t.id as TableType)}
                        disabled={!t.available}
                        className="w-4 h-4 accent-(--color-tertiary) cursor-pointer disabled:cursor-not-allowed"
                      />
                      <label htmlFor={`table-${t.id}`} className="text-sm text-(--color-primary) cursor-pointer disabled:cursor-not-allowed">
                        {t.label}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Transformation Toggle */}
              <div className="flex items-center justify-between border-t border-(--color-border) pt-4">
                <div className="flex flex-col">
                  <span className="text-xs font-bold font-display uppercase tracking-wider text-(--color-primary)">
                    Transformación Logarítmica
                  </span>
                  <span className="text-[10px] text-(--color-secondary)">
                    Aplica log(casos + 1) para estabilizar la varianza
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={transform}
                  onChange={(e) => setTransform(e.target.checked)}
                  className="w-4 h-4 accent-(--color-tertiary) cursor-pointer"
                />
              </div>

              {/* Years Selector Checkboxes */}
              <div className="flex flex-col gap-1.5 border-t border-(--color-border) pt-4">
                <label className="text-xs font-bold font-display uppercase tracking-wider text-(--color-primary) flex items-center justify-between">
                  <span>Seleccionar Años</span>
                  <Badge variant="outline" className="text-xs font-mono">
                    {selectedYears.length} seleccionados
                  </Badge>
                </label>
                <p className="text-[10px] text-(--color-secondary) mb-2">
                  Los años seleccionados se cruzarán con las tablas marcadas
                </p>
                <div className="grid grid-cols-4 gap-2">
                  {/* Show union of all possible years or a reasonable range */}
                  {Array.from({ length: 16 }, (_, i) => 2007 + i).map((year) => {
                    const isChecked = selectedYears.includes(year)
                    return (
                      <button
                        key={year}
                        onClick={() => handleYearToggle(year)}
                        className={`text-xs font-semibold font-mono py-1.5 px-1 rounded-sm border transition-all ${isChecked
                            ? "bg-(--color-tertiary-alpha) text-(--color-tertiary) border-(--color-tertiary-glow) font-bold"
                            : "bg-(--color-background) text-(--color-secondary) border-(--color-border) hover:border-(--color-border-strong) hover:text-(--color-primary)"
                          }`}
                      >
                        {year}
                      </button>
                    )
                  })}
                </div>
              </div>

            </CardContent>
          </Card>

          {/* Quick FAQ / Methods */}
          <Card className="bg-(--color-surface)">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-(--color-tertiary)" />
                Detalles Metodológicos
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-(--color-secondary) flex flex-col gap-3 leading-relaxed">
              <p>
                <strong>¿Qué es ANOVA?</strong> Es una prueba estadística que compara las medias de 3 o más grupos para ver si al menos un grupo es diferente de los otros. En nuestro caso, los grupos son los **años** y el dato son los **casos de dengue semanales**.
              </p>
              <p>
                <strong>Tukey HSD (Post-hoc):</strong> Si el ANOVA dice "hay diferencias", no nos dice *dónde*. Tukey realiza comparaciones por parejas para identificar qué pares de años específicos difieren significativamente entre sí de forma individual.
              </p>
              <p>
                <strong>Kruskal-Wallis:</strong> Es una alternativa no paramétrica robusta que no asume normalidad. Es útil en epidemiología porque las curvas epidémicas suelen ser asimétricas y con picos muy pronunciados.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Right Side: Results & Charts (8 cols) */}
        <div className="lg:col-span-8 flex flex-col gap-6">

          {loading ? (
            <div className="bg-(--color-surface) border border-(--color-border) rounded-md py-20 px-8 flex items-center justify-center min-h-[400px]">
              <LottieLoader variant="loading" message="Procesando datos en base de datos y calculando pruebas estadísticas..." />
            </div>
          ) : error ? (
            <div className="bg-(--color-surface) border border-(--color-border) rounded-md py-12 px-6 text-center flex flex-col items-center justify-center min-h-[400px] gap-4">
              <div className="w-12 h-12 rounded-full bg-(--color-danger-alpha) flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-(--color-danger)" />
              </div>
              <h3 className="text-lg font-bold text-(--color-primary)">Error de Cálculo</h3>
              <p className="text-sm text-(--color-secondary) max-w-md">
                {error}
              </p>
              <Button variant="outline" onClick={() => setSelectedYears([2015, 2016, 2017, 2019])}>
                Restablecer Parámetros por Defecto
              </Button>
            </div>
          ) : data ? (
            <div className="flex flex-col gap-6 animate-fade-in">

              {/* 1. LAYPERSON NARRATIVE INTERPRETATION (THE USER REQUESTED HIGHLIGHT) */}
              <Card className="border-l-4 border-l-(--color-tertiary) shadow-sm bg-(--color-surface)">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className={`px-2.5 py-0.5 font-bold flex items-center gap-1.5 uppercase ${data.hypothesis_tests.anova.significant
                        ? "bg-(--color-danger-alpha) text-(--color-danger) border-(--color-danger)"
                        : "bg-gray-100 text-gray-700 border-gray-300"
                      }`}>
                      {data.hypothesis_tests.anova.significant ? (
                        <>
                          <AlertCircle className="w-3.5 h-3.5" />
                          Diferencias Significativas
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Variación Normal
                        </>
                      )}
                    </Badge>
                    <span className="text-[10px] font-display uppercase tracking-wider text-(--color-muted) font-semibold flex items-center gap-1">
                      <HelpCircle className="w-3.5 h-3.5" />
                      Interpretación en Lenguaje Claro
                    </span>
                  </div>
                  <CardTitle className="text-xl text-(--color-primary) font-bold mt-2 font-display">
                    {data.interpretation.title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-4">
                  <p className="text-sm text-(--color-secondary) leading-relaxed">
                    {data.interpretation.summary}
                  </p>

                  <div className="bg-(--color-background) border border-(--color-border) rounded-sm p-4 flex items-start gap-3">
                    <Info className="w-5 h-5 text-(--color-tertiary) shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-(--color-primary) font-display">
                        Impacto e Interpretación Epidemiológica
                      </h4>
                      <p className="text-xs text-(--color-secondary) leading-relaxed mt-1">
                        {data.interpretation.epidemiological_impact}
                      </p>
                    </div>
                  </div>

                  {/* Hypotheses Explanation */}
                  <div className="mt-4 pt-4 border-t border-(--color-border) grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className={`p-3 rounded-sm border ${data.hypotheses.outcome === "null" ? "bg-(--color-success-alpha)/10 border-(--color-success-glow)" : "bg-gray-50 border-gray-200"}`}>
                      <h5 className="text-[10px] font-bold uppercase tracking-widest text-(--color-primary) mb-1 flex items-center gap-2">
                        <CheckCircle2 className={`w-3 h-3 ${data.hypotheses.outcome === "null" ? "text-(--color-success)" : "text-gray-400"}`} />
                        Hipótesis Nula (H₀)
                      </h5>
                      <p className={`text-xs ${data.hypotheses.outcome === "null" ? "text-(--color-primary) font-medium" : "text-(--color-secondary)"}`}>
                        {data.hypotheses.null}
                      </p>
                    </div>
                    <div className={`p-3 rounded-sm border ${data.hypotheses.outcome === "alternative" ? "bg-(--color-danger-alpha)/10 border-(--color-danger-glow)" : "bg-gray-50 border-gray-200"}`}>
                      <h5 className="text-[10px] font-bold uppercase tracking-widest text-(--color-primary) mb-1 flex items-center gap-2">
                        <AlertCircle className={`w-3 h-3 ${data.hypotheses.outcome === "alternative" ? "text-(--color-danger)" : "text-gray-400"}`} />
                        Hipótesis Alternativa (H₁)
                      </h5>
                      <p className={`text-xs ${data.hypotheses.outcome === "alternative" ? "text-(--color-primary) font-medium" : "text-(--color-secondary)"}`}>
                        {data.hypotheses.alternative}
                      </p>
                    </div>
                    <div className="md:col-span-2 flex items-center justify-center gap-2 py-1 px-3 bg-(--color-tertiary-alpha)/10 rounded-full border border-(--color-tertiary-glow) w-fit mx-auto">
                      <Scale className="w-3.5 h-3.5 text-(--color-tertiary)" />
                      <span className="text-xs font-bold text-(--color-tertiary)">
                        Conclusión: {data.hypotheses.conclusion}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 2. DYNAMIC CHART OF WEEKLY PATTERNS */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <LineChartIcon className="w-4 h-4 text-(--color-tertiary)" />
                      Comparación de Curvas Semanales Epidemiológicas
                    </span>
                    <Badge variant="outline" className="text-xs font-mono text-(--color-muted)">
                      Eje X: Semanas Epidemiológicas (1-53)
                    </Badge>
                  </CardTitle>
                  <CardDescription>
                    Pasa el cursor sobre el gráfico para comparar los valores semana a semana entre los diferentes años.
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-2">
                  {renderSvgChart()}

                  {/* Legend */}
                  <div className="flex flex-wrap justify-center items-center gap-4 mt-4 border-t border-(--color-border) pt-4">
                    {data.metadata.analyzed_groups.map((g: string, idx: number) => {
                      const color = YEAR_COLORS[String(idx % 6)]
                      const desc = data.descriptives.find((d: any) => d.group === g)
                      return (
                        <div key={`legend-${g}`} className="flex items-center gap-2 text-xs bg-(--color-background) border border-(--color-border) px-2.5 py-1 rounded-sm">
                          <span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: color }} />
                          <span className="font-bold text-(--color-primary) text-[10px]">{g}:</span>
                          <span className="text-(--color-secondary) font-mono">
                            {desc ? `${Math.round(desc.sum).toLocaleString()} casos total` : ""}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>

              {/* 3. DETAILED STATISTICAL CARDS */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

                {/* Parametric ANOVA */}
                <div className="bg-(--color-surface) border border-(--color-border) rounded-md p-4 flex flex-col justify-between">
                  <div>
                    <span className="text-[10px] font-display uppercase tracking-wider text-(--color-muted) font-semibold">
                      Prueba Paramétrica
                    </span>
                    <h4 className="text-sm font-bold text-(--color-primary) mt-1">ANOVA de una vía</h4>
                  </div>
                  <div className="my-4">
                    <p className="text-2xl font-bold font-mono text-(--color-primary)">
                      F = {data.hypothesis_tests.anova.f_statistic !== null ? data.hypothesis_tests.anova.f_statistic.toFixed(3) : "N/A"}
                    </p>
                    <p className="text-xs text-(--color-secondary) font-mono mt-1">
                      p-valor: {formatPValue(data.hypothesis_tests.anova.p_value)}
                    </p>
                  </div>
                  <Badge variant="outline" className={`w-fit text-[10px] font-semibold py-0.5 px-2 rounded-sm ${data.hypothesis_tests.anova.significant
                      ? "bg-(--color-danger-alpha) text-(--color-danger) border-(--color-danger)"
                      : "bg-gray-100 text-gray-700 border-gray-300"
                    }`}>
                    {data.hypothesis_tests.anova.significant ? "Significativo" : "No Significativo"}
                  </Badge>
                </div>

                {/* Non-parametric Kruskal-Wallis */}
                <div className="bg-(--color-surface) border border-(--color-border) rounded-md p-4 flex flex-col justify-between">
                  <div>
                    <span className="text-[10px] font-display uppercase tracking-wider text-(--color-muted) font-semibold">
                      Alternativa Robusta
                    </span>
                    <h4 className="text-sm font-bold text-(--color-primary) mt-1">Kruskal-Wallis</h4>
                  </div>
                  <div className="my-4">
                    <p className="text-2xl font-bold font-mono text-(--color-primary)">
                      H = {data.hypothesis_tests.kruskal_wallis.h_statistic !== null ? data.hypothesis_tests.kruskal_wallis.h_statistic.toFixed(3) : "N/A"}
                    </p>
                    <p className="text-xs text-(--color-secondary) font-mono mt-1">
                      p-valor: {formatPValue(data.hypothesis_tests.kruskal_wallis.p_value)}
                    </p>
                  </div>
                  <Badge variant="outline" className={`w-fit text-[10px] font-semibold py-0.5 px-2 rounded-sm ${data.hypothesis_tests.kruskal_wallis.significant
                      ? "bg-(--color-danger-alpha) text-(--color-danger) border-(--color-danger)"
                      : "bg-gray-100 text-gray-700 border-gray-300"
                    }`}>
                    {data.hypothesis_tests.kruskal_wallis.significant ? "Significativo" : "No Significativo"}
                  </Badge>
                </div>

                {/* Variances Homocedasticity */}
                <div className="bg-(--color-surface) border border-(--color-border) rounded-md p-4 flex flex-col justify-between">
                  <div>
                    <span className="text-[10px] font-display uppercase tracking-wider text-(--color-muted) font-semibold">
                      Supuesto ANOVA
                    </span>
                    <h4 className="text-sm font-bold text-(--color-primary) mt-1">Prueba de Levene</h4>
                  </div>
                  <div className="my-4">
                    <p className="text-2xl font-bold font-mono text-(--color-primary)">
                      W = {data.hypothesis_tests.levene_homocedasticity.statistic !== null ? data.hypothesis_tests.levene_homocedasticity.statistic.toFixed(3) : "N/A"}
                    </p>
                    <p className="text-xs text-(--color-secondary) font-mono mt-1">
                      p-valor: {formatPValue(data.hypothesis_tests.levene_homocedasticity.p_value)}
                    </p>
                  </div>
                  <Badge variant="outline" className={`w-fit text-[10px] font-semibold py-0.5 px-2 rounded-sm ${data.hypothesis_tests.levene_homocedasticity.significant
                      ? "bg-amber-50 text-amber-700 border-amber-300"
                      : "bg-green-50 text-green-700 border-green-300"
                    }`}>
                    {data.hypothesis_tests.levene_homocedasticity.significant ? "Varianza Desigual" : "Varianzas Iguales"}
                  </Badge>
                </div>

              </div>

              {/* 4. COMPARACIONES POST-HOC TUKEY TABLE */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <ArrowRightLeft className="w-4 h-4 text-(--color-tertiary)" />
                    Prueba Post-Hoc: Comparaciones de Rango Múltiple de Tukey (Tukey HSD)
                  </CardTitle>
                  <CardDescription>
                    Evalúa la diferencia estadística par por par. El p-valor se encuentra ajustado para controlar la tasa de error por comparaciones múltiples.
                  </CardDescription>
                </CardHeader>
                <CardContent className="overflow-x-auto p-0">
                  <table className="w-full border-collapse text-left text-sm select-none">
                    <thead>
                      <tr className="border-y border-(--color-border) bg-(--color-background) text-xs font-bold font-display uppercase tracking-wider text-(--color-primary)">
                        <th className="py-3 px-4">Comparación</th>
                        <th className="py-3 px-4 text-right">Diferencia Promedio</th>
                        <th className="py-3 px-4 text-right">Intervalo Confianza (95%)</th>
                        <th className="py-3 px-4 text-right">p-Valor Adj.</th>
                        <th className="py-3 px-4 text-center">Resultado</th>
                        <th className="py-3 px-4">Explicación Simple</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-(--color-border)">
                      {data.tukey_hsd.map((row: any, idx: number) => (
                        <tr
                          key={`tukey-row-${idx}`}
                          className={`hover:bg-(--color-surface-hover) transition-colors ${row.significant ? "bg-(--color-tertiary-alpha)/20" : ""
                            }`}
                        >
                          <td className="py-3 px-4 font-bold text-(--color-primary) font-mono text-[10px]">
                            {row.group_a} <span className="text-(--color-secondary)">vs</span> {row.group_b}
                          </td>
                          <td className={`py-3 px-4 text-right font-bold font-mono ${row.mean_diff_original > 0 ? "text-(--color-danger)" : "text-(--color-success)"
                            }`}>
                            {row.mean_diff_original > 0 ? "+" : ""}{row.mean_diff_original.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
                          </td>
                          <td className="py-3 px-4 text-right font-mono text-xs text-(--color-secondary)">
                            [{row.ci_lower.toFixed(1)}, {row.ci_upper.toFixed(1)}]
                          </td>
                          <td className="py-3 px-4 text-right font-mono text-xs text-(--color-primary)">
                            {row.p_value < 0.00001 ? "< 0.00001" : row.p_value.toFixed(5)}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <Badge variant="outline" className={`text-[10px] font-bold ${row.significant
                                ? "bg-(--color-danger-alpha) text-(--color-danger) border-(--color-danger)"
                                : "bg-gray-100 text-gray-500 border-gray-300"
                              }`}>
                              {row.significant ? "Diferente" : "Similar"}
                            </Badge>
                          </td>
                          <td className="py-3 px-4 text-xs text-(--color-secondary) max-w-[280px]">
                            {row.narrative}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </CardContent>
              </Card>

            </div>
          ) : null}

        </div>

      </div>

    </div>
  )
}
