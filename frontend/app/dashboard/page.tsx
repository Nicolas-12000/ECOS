"use client"

import { useState } from "react"
import { Badge } from "@/components/ui/Badge"
import { BarChart3, Map, ExternalLink, Monitor } from "lucide-react"
import { LottieLoader } from "@/components/ui/LottieLoader"

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
    icon: Map,
    description: "Mapa de flujos OD (origen-destino) de pasajeros intermunicipales correlacionado con propagación de riesgo epidemiológico.",
    tag: "KEPLER.GL",
    embedUrl: null as string | null,
    tech: "Kepler.gl / Deck.gl",
    source: "React Mapbox GL",
    updateFrequency: "Mensual",
  },
]

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
        {activeDashboard.embedUrl ? (
          /* Real embed */
          <div className="relative w-full" style={{ paddingBottom: "56.25%" }}>
            {iframeLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-(--color-surface) z-10 min-h-[300px]">
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
