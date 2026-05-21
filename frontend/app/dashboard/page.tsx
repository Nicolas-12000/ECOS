"use client"

import { useMemo, useState } from "react"
import useSWR from "swr"
import { Badge } from "@/components/ui/Badge"
import { BarChart3, Map as MapIcon, Monitor } from "lucide-react"
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
  { code: "11001", name: "Bogotá D.C." },
  { code: "05001", name: "Medellín" },
  { code: "76001", name: "Cali" },
  { code: "08001", name: "Barranquilla" },
  { code: "13001", name: "Cartagena" },
  { code: "54001", name: "Cúcuta" },
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

function MobilityDashboard() {
  const [municipioCode, setMunicipioCode] = useState(MUNICIPIOS[0].code)
  const { data, error, isLoading } = useSWR<MobilityODResponse>(
    `/api/v3/mobility/od?municipio_code=${municipioCode}&limit=52`,
    fetcher,
  )
  const { data: arcData, error: arcError, isLoading: arcLoading } = useSWR<MobilityArcResponse>(
    "/api/v3/mobility/od-map?limit=200",
    fetcher,
  )

  const series = useMemo(() => {
    const records = data?.records ? [...data.records] : []
    return records
      .sort((a, b) => (a.epi_year - b.epi_year) || (a.epi_week - b.epi_week))
  }, [data])

  const mobilityIn = series.map(r => r.mobility_in)
  const mobilityOut = series.map(r => r.mobility_out)
  const latest = series[series.length - 1]
  const previous = series[series.length - 2]
  const deltaIn = latest && previous ? latest.mobility_in - previous.mobility_in : 0
  const deltaOut = latest && previous ? latest.mobility_out - previous.mobility_out : 0

  const width = 640
  const height = 220
  const padding = 28
  const inPath = buildLinePath(mobilityIn, width, height, padding)
  const outPath = buildLinePath(mobilityOut, width, height, padding)
  const arcs = useMemo(() => arcData?.arcs ?? [], [arcData])
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
    getSourceColor: [220, 38, 38, 180],
    getTargetColor: [14, 116, 144, 180],
    pickable: true,
    autoHighlight: true,
  }), [arcs, maxPassengers])

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-(--color-muted) font-semibold">Movilidad intermunicipal</p>
          <h2 className="text-2xl font-bold text-(--color-primary)">Flujos de entrada y salida (últimas 52 semanas)</h2>
          <p className="text-sm text-(--color-secondary) mt-2 max-w-2xl">
            Usa el código DANE para explorar el historial de movilidad que alimenta el mapa de riesgo.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
          <label className="text-xs font-semibold uppercase tracking-[0.2em] text-(--color-muted)">Municipio</label>
          <select
            value={municipioCode}
            onChange={(e) => setMunicipioCode(e.target.value)}
            className="bg-(--color-background) border border-(--color-border) rounded-md px-3 py-2 text-sm text-(--color-primary)"
          >
            {MUNICIPIOS.map((m) => (
              <option key={m.code} value={m.code}>
                {m.name} · {m.code}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-(--color-background) border border-(--color-border) rounded-md p-4">
          <p className="text-[10px] uppercase tracking-wider text-(--color-muted) font-semibold">Última semana</p>
          <p className="text-sm font-bold text-(--color-primary) mt-2">
            {latest ? `S${latest.epi_week} · ${latest.epi_year}` : "Sin datos"}
          </p>
          <p className="text-xs text-(--color-muted) mt-1">Registro más reciente cargado</p>
        </div>
        <div className="bg-(--color-background) border border-(--color-border) rounded-md p-4">
          <p className="text-[10px] uppercase tracking-wider text-(--color-muted) font-semibold">Movilidad entrante</p>
          <p className="text-sm font-bold text-(--color-primary) mt-2">
            {latest ? formatNumber(latest.mobility_in) : "—"}
          </p>
          <p className="text-xs text-(--color-muted) mt-1">
            {latest && previous ? `${deltaIn >= 0 ? "+" : ""}${formatNumber(deltaIn)} vs. semana anterior` : "Comparativo no disponible"}
          </p>
        </div>
        <div className="bg-(--color-background) border border-(--color-border) rounded-md p-4">
          <p className="text-[10px] uppercase tracking-wider text-(--color-muted) font-semibold">Movilidad saliente</p>
          <p className="text-sm font-bold text-(--color-primary) mt-2">
            {latest ? formatNumber(latest.mobility_out) : "—"}
          </p>
          <p className="text-xs text-(--color-muted) mt-1">
            {latest && previous ? `${deltaOut >= 0 ? "+" : ""}${formatNumber(deltaOut)} vs. semana anterior` : "Comparativo no disponible"}
          </p>
        </div>
      </div>

      <div className="bg-(--color-background) border border-(--color-border) rounded-md p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-(--color-muted) font-semibold mb-3">Mapa OD por departamento</p>
        {arcLoading ? (
          <div className="min-h-90 flex items-center justify-center">
            <LottieLoader variant="loading" message="Cargando mapa de movilidad..." />
          </div>
        ) : arcError || arcs.length === 0 ? (
          <div className="min-h-90 flex flex-col items-center justify-center gap-2 text-sm text-(--color-secondary)">
            <Badge variant="outline">Sin datos</Badge>
            <p>No hay flujos OD disponibles para el mapa.</p>
          </div>
        ) : (
          <div className="h-105 rounded-md overflow-hidden border border-(--color-border)">
            <DeckGL
              initialViewState={INITIAL_VIEW_STATE}
              controller
              layers={[arcLayer]}
              getTooltip={({ object }: { object?: MobilityArcItem }) => (
                object ? `${object.origin_code} → ${object.dest_code} · ${formatNumber(object.passengers)}` : null
              )}
            >
              <Map reuseMaps mapStyle={MAP_STYLE} />
            </DeckGL>
          </div>
        )}
      </div>

      <div className="bg-(--color-background) border border-(--color-border) rounded-md p-4">
        {isLoading ? (
          <div className="min-h-55 flex items-center justify-center">
            <LottieLoader variant="loading" message="Cargando series de movilidad..." />
          </div>
        ) : error ? (
          <div className="min-h-50 flex flex-col items-center justify-center gap-2 text-sm text-(--color-secondary)">
            <Badge variant="outline">Sin datos</Badge>
            <p>No hay registros de movilidad para este municipio. Verifica el código DANE.</p>
          </div>
        ) : (
          <div className="w-full overflow-x-auto">
            <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-60">
              <defs>
                <linearGradient id="mobilityIn" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#16A34A" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#16A34A" stopOpacity="0" />
                </linearGradient>
                <linearGradient id="mobilityOut" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#F97316" stopOpacity="0.2" />
                  <stop offset="100%" stopColor="#F97316" stopOpacity="0" />
                </linearGradient>
              </defs>
              <rect x="0" y="0" width={width} height={height} fill="transparent" />
              <path d={inPath} fill="none" stroke="#16A34A" strokeWidth="2" />
              <path d={outPath} fill="none" stroke="#F97316" strokeWidth="2" />
            </svg>
            <div className="flex flex-wrap gap-4 text-xs text-(--color-muted) mt-3">
              <span className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#16A34A]" />
                Entrante
              </span>
              <span className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#F97316]" />
                Saliente
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="bg-(--color-background) border border-(--color-border) rounded-md p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-(--color-muted) font-semibold mb-3">Últimas 8 semanas</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {series.slice(-8).map((row) => (
            <div key={`${row.epi_year}-${row.epi_week}`} className="border border-(--color-border) rounded-md p-3">
              <p className="text-[10px] uppercase tracking-wider text-(--color-muted)">S{row.epi_week} · {row.epi_year}</p>
              <p className="text-sm font-semibold text-(--color-primary) mt-2">{formatNumber(row.mobility_in)} entrante</p>
              <p className="text-xs text-(--color-muted)">{formatNumber(row.mobility_out)} saliente</p>
            </div>
          ))}
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
