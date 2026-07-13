"use client"

import { useMemo, useState } from "react"
import useSWR from "swr"
import { Badge } from "@/components/ui/Badge"
import { BarChart3, Map as MapIcon, Monitor, Info, X } from "lucide-react"
import { LottieLoader } from "@/components/ui/LottieLoader"
import { fetcher } from "@/lib/api"
import DeckGL from "@deck.gl/react"
import { ArcLayer } from "@deck.gl/layers"
import Map from "react-map-gl/maplibre"
import "maplibre-gl/dist/maplibre-gl.css"

const DASHBOARDS = [
  {
    id: "comando",
    label: "Centro de Comando",
    icon: BarChart3,
    description: "Predicciones por departamento, alertas activas, serie temporal de predicción vs. casos reportados, y explicabilidad SHAP.",
    tag: "POWER BI",
    embedUrl: "https://app.powerbi.com/view?r=eyJrIjoiNGJiYzE4YmMtM2EzNy00MDc2LTkwZDctNmM0MzE3Y2U0MTk4IiwidCI6IjhkMzY4MzZlLTZiNzUtNGRlNi1iYWI5LTVmNGIxNzc1NDI3ZiIsImMiOjR9",
    tech: "Power BI Pro",
    source: "Servicio Cloud Microsoft",
    updateFrequency: "Semanal automática",
  },
  {
    id: "movilidad",
    label: "Movilidad × Enfermedad",
    icon: MapIcon,
    description: "Mapa de flujos OD (origen-destino) de pasajeros intermunicipales correlacionado con propagación de riesgo epidemiológico.",
    tag: "KEPLER.GL",
    embedUrl: null as string | null,
    tech: "Kepler.gl / Deck.gl",
    source: "React Mapbox GL",
    updateFrequency: "Mensual",
  },
]

const MUNICIPIOS = [
  { code: "86865", name: "Puerto Asís" },
  { code: "05500", name: "Medellín" },
  { code: "70708", name: "Toluviejo" },
  { code: "05579", name: "Puerto Triunfo" },
  { code: "68686", name: "San Gil" },
  { code: "25258", name: "Tocaima" },
  { code: "76760", name: "Cali" },
  { code: "11110", name: "Bogotá D.C." },
  { code: "13130", name: "Cartagena" },
  { code: "54540", name: "Cúcuta" },
]

interface MobilityODItem {
  epi_year: number
  epi_week: number
  municipio_code: string
  mobility_in: number
  mobility_out: number
}

interface MobilityODResponse {
  municipio_code: string
  records: MobilityODItem[]
}

interface MobilityArcItem {
  origin_code: string
  dest_code: string
  origin_lat: number
  origin_lon: number
  dest_lat: number
  dest_lon: number
  passengers: number
}

interface MobilityArcResponse {
  arcs: MobilityArcItem[]
  total: number
}

const MAP_STYLE = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
const INITIAL_VIEW_STATE = {
  longitude: -74.2973,
  latitude: 4.5709,
  zoom: 4.7,
  pitch: 35,
  bearing: 0,
}

const formatNumber = (value: number) => new Intl.NumberFormat("es-CO").format(value)

function buildLinePath(series: number[], width: number, height: number, padding: number) {
  if (series.length === 0) return ""
  const maxValue = Math.max(...series, 1)
  const step = (width - padding * 2) / Math.max(series.length - 1, 1)
  return series
    .map((value, index) => {
      const x = padding + step * index
      const y = height - padding - (value / maxValue) * (height - padding * 2)
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`
    })
    .join(" ")
}

const DEPTO_NAMES: Record<string, string> = {
  "05": "Antioquia",
  "08": "Atlántico",
  "11": "Bogotá D.C.",
  "13": "Bolívar",
  "15": "Boyacá",
  "17": "Caldas",
  "18": "Caquetá",
  "19": "Cauca",
  "20": "Cesar",
  "23": "Córdoba",
  "25": "Cundinamarca",
  "27": "Chocó",
  "41": "Huila",
  "44": "La Guajira",
  "47": "Magdalena",
  "50": "Meta",
  "52": "Nariño",
  "54": "Norte de Santander",
  "63": "Quindío",
  "66": "Risaralda",
  "68": "Santander",
  "70": "Sucre",
  "73": "Tolima",
  "76": "Valle del Cauca",
  "81": "Arauca",
  "85": "Casanare",
  "86": "Putumayo",
  "88": "San Andrés",
  "91": "Amazonas",
  "94": "Guainía",
  "95": "Guaviare",
  "97": "Vaupés",
  "99": "Vichada"
}

// Municipio representativo por departamento (primer código disponible en MUNICIPIOS)
const DEPTO_TO_MUNICIPIO: Record<string, string> = {
  "86": "86865", // Putumayo → Puerto Asís
  "05": "05500", // Antioquia → Medellín
  "70": "70708", // Sucre → Toluviejo
  "68": "68686", // Santander → San Gil
  "25": "25258", // Cundinamarca → Tocaima
  "76": "76760", // Valle del Cauca → Cali
  "11": "11110", // Bogotá D.C. → Bogotá
  "13": "13130", // Bolívar → Cartagena
  "54": "54540", // Norte de Santander → Cúcuta
}

const TIME_RANGES = [
  { label: "4 semanas", weeks: 4 },
  { label: "13 semanas (3 meses)", weeks: 13 },
  { label: "26 semanas (6 meses)", weeks: 26 },
  { label: "52 semanas (1 año)", weeks: 52 },
  { label: "Todo el historial", weeks: null },
]

function MobilityDashboard() {
  const [municipioCode, setMunicipioCode] = useState(MUNICIPIOS[0].code)
  const [weeksLimit, setWeeksLimit] = useState<number | null>(52)
  const [selectedDepto, setSelectedDepto] = useState<string | null>(null)

  const { data, error, isLoading } = useSWR<MobilityODResponse>(
    `/api/v3/mobility/od?municipio_code=${municipioCode}${weeksLimit !== null ? `&limit=${weeksLimit}` : ""}`,
    fetcher,
  )
  const { data: arcData, error: arcError, isLoading: arcLoading } = useSWR<MobilityArcResponse>(
    "/api/v3/mobility/od-map?limit=200",
    fetcher,
  )

  const allSeries = useMemo(() => {
    const records = data?.records ? [...data.records] : []
    return records.sort((a, b) => (a.epi_year - b.epi_year) || (a.epi_week - b.epi_week))
  }, [data])

  // Apply time window (null = all data)
  const series = useMemo(
    () => weeksLimit !== null ? allSeries.slice(-weeksLimit) : allSeries,
    [allSeries, weeksLimit]
  )

  const mobilityIn = series.map(r => r.mobility_in)
  const mobilityOut = series.map(r => r.mobility_out)
  const latest = series[series.length - 1]
  const firstRecord = series[0]

  // Totals for the selected period
  const totalIn = series.reduce((s, r) => s + r.mobility_in, 0)
  const totalOut = series.reduce((s, r) => s + r.mobility_out, 0)

  const width = 640
  const height = 220
  const padding = 28
  const inPath = buildLinePath(mobilityIn, width, height, padding)
  const outPath = buildLinePath(mobilityOut, width, height, padding)

  const allArcs = useMemo(() => arcData?.arcs ?? [], [arcData])

  // Filter arcs by selected department
  const arcs = useMemo(() => {
    if (!selectedDepto) return allArcs
    return allArcs.filter(
      a => a.origin_code === selectedDepto || a.dest_code === selectedDepto
    )
  }, [allArcs, selectedDepto])

  const maxPassengers = useMemo(
    () => arcs.reduce((max, arc) => Math.max(max, arc.passengers), 1),
    [arcs]
  )

  const arcLayer = useMemo(() => new ArcLayer<MobilityArcItem>({
    id: "mobility-arcs",
    data: arcs,
    getSourcePosition: (d: MobilityArcItem) => [d.origin_lon, d.origin_lat],
    getTargetPosition: (d: MobilityArcItem) => [d.dest_lon, d.dest_lat],
    getWidth: (d: MobilityArcItem) => Math.max(1, (d.passengers / maxPassengers) * 6),
    getSourceColor: (d: MobilityArcItem) =>
      selectedDepto && d.origin_code === selectedDepto ? [220, 38, 38, 220] : [220, 38, 38, 160],
    getTargetColor: (d: MobilityArcItem) =>
      selectedDepto && d.dest_code === selectedDepto ? [14, 116, 144, 220] : [14, 116, 144, 160],
    pickable: true,
    autoHighlight: true,
    onClick: ({ object }: { object?: MobilityArcItem }) => {
      if (!object) return
      const clickedDepto = object.origin_code
      // Toggle map filter
      setSelectedDepto(prev => prev === clickedDepto ? null : clickedDepto)
      // Sync el panel de stats con el municipio de ese departamento
      const matchingMunicipio = DEPTO_TO_MUNICIPIO[clickedDepto]
      if (matchingMunicipio) setMunicipioCode(matchingMunicipio)
    },
  }), [arcs, maxPassengers, selectedDepto])

  const historyWeeks = weeksLimit === null ? 12 : weeksLimit <= 13 ? weeksLimit : 8

  return (
    <div className="p-4 lg:p-6 space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-(--color-border) pb-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-(--color-muted) font-semibold">Movilidad intermunicipal · SIVIGILA</p>
          <h2 className="text-xl font-bold text-(--color-primary)">Flujos de Viajeros entre Municipios</h2>
          <p className="text-xs text-(--color-secondary) mt-0.5">
            Registro histórico semanal — datos disponibles hasta
            {latest ? <strong className="text-(--color-primary)"> Sem. {latest.epi_week} / {latest.epi_year}</strong> : " sin datos"}
          </p>
        </div>
        {/* Controls row */}
        <div className="flex flex-wrap gap-2 sm:justify-end">
          {/* Time range selector */}
          <div className="flex items-center gap-1 bg-(--color-surface) border border-(--color-border) rounded-md px-2 py-1 shadow-sm">
            {TIME_RANGES.map(tr => (
              <button
                key={tr.weeks}
                onClick={() => setWeeksLimit(tr.weeks)}
                className={`px-2 py-0.5 text-[10px] font-semibold rounded transition-all ${
                  weeksLimit === tr.weeks
                    ? "bg-[var(--color-tertiary)] text-white"
                    : "text-(--color-secondary) hover:text-(--color-primary)"
                }`}
              >
                {tr.label.split(" ")[0]}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Department list filter */}
      <div className="bg-(--color-background) border border-(--color-border) rounded-md p-3">
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex items-center gap-1.5">
            <Info size={12} className="text-(--color-muted)" />
            <span className="text-[10px] uppercase tracking-wider font-semibold text-(--color-muted)">
              Filtrar por departamento — clic para sincronizar mapa y estadísticas
            </span>
          </div>
          {selectedDepto && (
            <button
              onClick={() => setSelectedDepto(null)}
              className="flex items-center gap-1 text-[10px] text-(--color-tertiary) font-semibold hover:opacity-75 transition-opacity"
            >
              <X size={10} />
              Quitar filtro
            </button>
          )}
        </div>
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(DEPTO_NAMES).map(([code, name]) => {
            const isActive = selectedDepto === code
            const hasMunicipio = code in DEPTO_TO_MUNICIPIO
            return (
              <button
                key={code}
                onClick={() => {
                  if (isActive) {
                    setSelectedDepto(null)
                  } else {
                    setSelectedDepto(code)
                    const matchingMunicipio = DEPTO_TO_MUNICIPIO[code]
                    if (matchingMunicipio) setMunicipioCode(matchingMunicipio)
                  }
                }}
                className={`px-2.5 py-1 rounded-full text-[10px] font-semibold border transition-all ${
                  isActive
                    ? "bg-[var(--color-tertiary)] text-white border-[var(--color-tertiary)] shadow-sm"
                    : hasMunicipio
                    ? "border-(--color-border) text-(--color-secondary) hover:border-[var(--color-tertiary)] hover:text-(--color-primary) bg-(--color-surface)"
                    : "border-(--color-border) text-(--color-muted) bg-(--color-surface) opacity-60 cursor-pointer"
                }`}
              >
                {name}
              </button>
            )
          })}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Map OD */}
        <div className="lg:col-span-7 flex flex-col">
          <div className="bg-(--color-background) border border-(--color-border) rounded-md p-4 flex flex-col h-full min-h-[500px] lg:min-h-[580px]">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs uppercase tracking-[0.2em] text-(--color-muted) font-semibold">
                Mapa de Viajes Interdepartamentales
              </p>
              <Badge variant="outline" className="text-[10px]">Total histórico acumulado</Badge>
            </div>
            {arcLoading ? (
              <div className="flex-1 flex items-center justify-center">
                <LottieLoader variant="loading" message="Cargando mapa de movilidad..." />
              </div>
            ) : arcError || allArcs.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center gap-2 text-sm text-(--color-secondary)">
                <Badge variant="outline">Sin datos</Badge>
                <p>No hay flujos de transporte disponibles para el mapa.</p>
              </div>
            ) : (
              <div className="relative flex-1 w-full rounded-md overflow-hidden border border-(--color-border) min-h-[400px]">
                <DeckGL
                  initialViewState={INITIAL_VIEW_STATE}
                  controller
                  layers={[arcLayer]}
                  getTooltip={({ object }: { object?: MobilityArcItem }) => {
                    if (!object) return null
                    const fromDepto = DEPTO_NAMES[object.origin_code] || `Dpto. ${object.origin_code}`
                    const toDepto = DEPTO_NAMES[object.dest_code] || `Dpto. ${object.dest_code}`
                    return {
                      html: `<b>${fromDepto} → ${toDepto}</b><br/>${formatNumber(object.passengers)} pasajeros registrados en total<br/><i style="font-size:10px;color:#888">Clic para sincronizar todos los paneles con este departamento</i>`,
                      style: { fontSize: "12px", padding: "8px 10px", borderRadius: "6px" }
                    }
                  }}
                >
                  <Map reuseMaps mapStyle={MAP_STYLE} />
                </DeckGL>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Analytics & Charts */}
        <div className="lg:col-span-5 flex flex-col space-y-4">

          {/* Period summary KPIs */}
          <div className="bg-(--color-background) border border-(--color-border) rounded-md p-4">
            <div className="flex items-center justify-between mb-3">
              <p className="text-[9px] uppercase tracking-wider text-(--color-muted) font-semibold">
                Período visualizado
              </p>
              <span className="text-[9px] text-(--color-muted)">
                {TIME_RANGES.find(t => t.weeks === weeksLimit)?.label}
              </span>
            </div>
            {series.length > 0 ? (
              <div className="bg-(--color-surface) rounded-md px-3 py-2 mb-3 border border-(--color-border) text-center">
                <p className="text-[9px] text-(--color-muted) mb-0.5">Rango de datos mostrado</p>
                <p className="text-xs font-bold text-(--color-primary)">
                  Sem. {firstRecord?.epi_week} / {firstRecord?.epi_year}
                  <span className="font-normal text-(--color-muted) mx-1.5">→</span>
                  Sem. {latest?.epi_week} / {latest?.epi_year}
                </p>
                {weeksLimit !== null && latest?.epi_year && new Date().getFullYear() - latest.epi_year >= 1 && (
                  <p className="text-[9px] text-amber-600 mt-1">
                    Los datos más recientes disponibles son de {latest.epi_year} — no de los últimos {weeksLimit} semanas del calendario actual.
                  </p>
                )}
              </div>
            ) : null}
            <div className="grid grid-cols-2 gap-3">
              <div className="text-center border border-(--color-border) rounded-md p-2">
                <p className="text-[9px] text-(--color-muted)">Total entraron<br/>(suma del período)</p>
                <p className="text-xs font-bold text-emerald-600 mt-0.5">
                  {series.length > 0 ? `${formatNumber(totalIn)} pers.` : "—"}
                </p>
              </div>
              <div className="text-center border border-(--color-border) rounded-md p-2">
                <p className="text-[9px] text-(--color-muted)">Total salieron<br/>(suma del período)</p>
                <p className="text-xs font-bold text-orange-600 mt-0.5">
                  {series.length > 0 ? `${formatNumber(totalOut)} pers.` : "—"}
                </p>
              </div>
            </div>
          </div>

          {/* Timeline Chart */}
          <div className="bg-(--color-background) border border-(--color-border) rounded-md p-4 flex flex-col min-h-[200px]">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs uppercase tracking-[0.2em] text-(--color-muted) font-semibold">
                Tendencia semanal de viajeros
              </p>
              <span className="text-[9px] text-(--color-muted)">Registros por semana epidemiológica</span>
            </div>
            {isLoading ? (
              <div className="flex-1 flex items-center justify-center">
                <LottieLoader variant="loading" message="Cargando datos históricos..." />
              </div>
            ) : error || series.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center gap-2 text-sm text-(--color-secondary)">
                <Badge variant="outline">Sin datos</Badge>
                <p className="text-xs text-center">No hay registros para este municipio en el período.</p>
              </div>
            ) : (
              <div className="w-full flex-1 flex flex-col justify-between">
                <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-28">
                  <defs>
                    <linearGradient id="mobilityIn2" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#16A34A" stopOpacity="0.15" />
                      <stop offset="100%" stopColor="#16A34A" stopOpacity="0" />
                    </linearGradient>
                    <linearGradient id="mobilityOut2" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#F97316" stopOpacity="0.12" />
                      <stop offset="100%" stopColor="#F97316" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  <rect x="0" y="0" width={width} height={height} fill="transparent" />
                  <path d={inPath} fill="url(#mobilityIn2)" stroke="#16A34A" strokeWidth="2" />
                  <path d={outPath} fill="url(#mobilityOut2)" stroke="#F97316" strokeWidth="2" />
                </svg>
                <div className="flex gap-5 text-[10px] text-(--color-muted) mt-1 justify-center border-t border-(--color-border) pt-2">
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#16A34A]" />Viajeros que llegaron esa semana</span>
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#F97316]" />Viajeros que salieron esa semana</span>
                </div>
              </div>
            )}
          </div>

          {/* History table */}
          <div className="bg-(--color-background) border border-(--color-border) rounded-md p-4 flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs uppercase tracking-[0.2em] text-(--color-muted) font-semibold">
                Detalle por semana
              </p>
              <span className="text-[9px] text-(--color-muted)">Últimas {historyWeeks} semanas del período</span>
            </div>
            {series.length === 0 ? (
              <p className="text-xs text-(--color-muted) text-center mt-4">Sin registros para mostrar.</p>
            ) : (
              <div className="grid grid-cols-2 gap-2 flex-1">
                {series.slice(-historyWeeks).map((row) => (
                  <div key={`${row.epi_year}-${row.epi_week}`} className="bg-(--color-surface) border border-(--color-border) rounded-md p-2 flex flex-col justify-between">
                    <p className="text-[9px] uppercase tracking-wider text-(--color-muted) font-semibold">
                      Semana {row.epi_week} · {row.epi_year}
                    </p>
                    <div className="mt-1">
                      <p className="text-[11px] font-bold text-emerald-600 leading-tight">
                        ↓ {formatNumber(row.mobility_in)} llegaron
                      </p>
                      <p className="text-[10px] text-orange-600 leading-tight mt-0.5">
                        ↑ {formatNumber(row.mobility_out)} salieron
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("comando")
  const [iframeLoading, setIframeLoading] = useState(true)
  const activeDashboard = DASHBOARDS.find(d => d.id === activeTab) || DASHBOARDS[0]

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId)
    setIframeLoading(true)
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-10 max-w-7xl min-h-screen">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4 border-b border-(--color-border-strong) pb-6">
        <div>
          <p className="font-display text-xs uppercase tracking-[0.2em] text-(--color-tertiary) mb-2 font-semibold">
            Visualización
          </p>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-(--color-primary) flex items-center gap-3">
            <Monitor className="text-(--color-tertiary) w-8 h-8 md:w-9 md:h-9" />
            Dashboards ECOS
          </h1>
          <p className="text-(--color-secondary) mt-2 max-w-2xl text-base">
            Paneles de control epidemiológico embebidos. Construidos con Power BI y Kepler.gl — 100% integrados.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {DASHBOARDS.map((dash) => {
          const Icon = dash.icon
          const isActive = activeTab === dash.id
          return (
            <button
              key={dash.id}
              onClick={() => handleTabChange(dash.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-md text-sm font-medium transition-all ${isActive
                  ? "bg-(--color-tertiary) text-white shadow-sm"
                  : "bg-(--color-surface) text-(--color-secondary) border border-(--color-border) hover:border-(--color-border-strong) hover:text-(--color-primary)"
                }`}
            >
              <Icon className="w-4 h-4" />
              {dash.label}
              <span className={`text-[9px] font-display uppercase tracking-wider ml-1 ${isActive ? "text-white/70" : "text-(--color-muted)"
                }`}>
                {dash.tag}
              </span>
            </button>
          )
        })}
      </div>

      {/* Dashboard Content */}
      <div className="bg-(--color-surface) border border-(--color-border) rounded-md overflow-hidden">
        {activeDashboard.id === "movilidad" ? (
          <MobilityDashboard />
        ) : activeDashboard.embedUrl ? (
          /* Real embed */
          <div className="relative w-full" style={{ paddingBottom: "56.25%" }}>
            {iframeLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-(--color-surface) z-10 min-h-75">
                <LottieLoader variant="loading" message="Cargando panel de control..." />
              </div>
            )}
            <iframe
              src={activeDashboard.embedUrl}
              className="absolute inset-0 w-full h-full border-0"
              allowFullScreen
              title={activeDashboard.label}
              onLoad={() => setIframeLoading(false)}
            />
          </div>
        ) : (
          /* Placeholder when no embed URL */
          <div className="py-20 px-8 text-center">
            <div className="max-w-lg mx-auto">
              <div className="w-16 h-16 rounded-full bg-(--color-tertiary-alpha) flex items-center justify-center mx-auto mb-6">
                <activeDashboard.icon className="w-7 h-7 text-(--color-tertiary)" />
              </div>

              <h2 className="text-xl font-bold text-(--color-primary) mb-3">
                {activeDashboard.label}
              </h2>
              <p className="text-sm text-(--color-secondary) mb-6 leading-relaxed">
                {activeDashboard.description}
              </p>

              <Badge variant="outline" className="mb-6">
                {activeDashboard.tag} · Dashboard embebido
              </Badge>

              <div className="bg-(--color-background) border border-(--color-border) rounded-md p-5 text-left">
                <p className="text-[10px] font-display uppercase tracking-wider text-(--color-muted) font-semibold mb-3">
                  Para activar este dashboard
                </p>
                <ol className="space-y-2 text-sm text-(--color-secondary)">
                  <li className="flex items-start gap-2">
                    <span className="text-(--color-tertiary) font-bold text-xs mt-0.5">1.</span>
                    Ejecuta el servidor Plotly Dash o configura el enlace correspondiente en este componente.
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-(--color-tertiary) font-bold text-xs mt-0.5">2.</span>
                    Los datos de flujos y movilidad se sincronizan periódicamente con Kepler.gl.
                  </li>
                </ol>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        {[
          { title: "Tecnología", value: activeDashboard.tech, desc: activeDashboard.source },
          { title: "Actualización", value: activeDashboard.updateFrequency, desc: "Pipeline de datos unificado" },
          { title: "Audiencia", value: "Secretarías de salud", desc: "MinSalud · INS · 32 departamentos" },
        ].map((card, i) => (
          <div key={i} className="bg-(--color-surface) border border-(--color-border) rounded-md p-4">
            <p className="text-[10px] font-display uppercase tracking-wider text-(--color-muted) font-semibold">{card.title}</p>
            <p className="text-sm font-bold text-(--color-primary) mt-1">{card.value}</p>
            <p className="text-xs text-(--color-muted) mt-0.5">{card.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
