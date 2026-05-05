"use client"

import { useState } from "react"
import { Badge } from "@/components/ui/Badge"
import { BarChart3, Map, ExternalLink, Monitor } from "lucide-react"

const DASHBOARDS = [
  {
    id: "comando",
    label: "Centro de Comando",
    icon: BarChart3,
    description: "Predicciones por departamento, alertas activas, serie temporal de predicción vs. casos reportados, y explicabilidad SHAP.",
    tag: "PLOTLY DASH",
    // Replace with actual Power BI/Plotly embed URL when available
    embedUrl: null as string | null,
  },
  {
    id: "movilidad",
    label: "Movilidad × Enfermedad",
    icon: Map,
    description: "Mapa de flujos OD (origen-destino) de pasajeros intermunicipales correlacionado con propagación de riesgo epidemiológico.",
    tag: "KEPLER.GL",
    embedUrl: null as string | null,
  },
]

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("comando")
  const activeDashboard = DASHBOARDS.find(d => d.id === activeTab) || DASHBOARDS[0]

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
            Paneles de control epidemiológico embebidos. Construidos con Plotly Dash y Kepler.gl — 100% open-source.
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
              onClick={() => setActiveTab(dash.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-md text-sm font-medium transition-all ${
                isActive
                  ? "bg-(--color-tertiary) text-white shadow-sm"
                  : "bg-(--color-surface) text-(--color-secondary) border border-(--color-border) hover:border-(--color-border-strong) hover:text-(--color-primary)"
              }`}
            >
              <Icon className="w-4 h-4" />
              {dash.label}
              <span className={`text-[9px] font-display uppercase tracking-wider ml-1 ${
                isActive ? "text-white/70" : "text-(--color-muted)"
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
            <iframe
              src={activeDashboard.embedUrl}
              className="absolute inset-0 w-full h-full border-0"
              allowFullScreen
              title={activeDashboard.label}
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
                    Ejecuta el servidor Plotly Dash: <code className="text-xs bg-(--color-surface) px-1.5 py-0.5 rounded border border-(--color-border) font-mono">python backend/app/dashboard/app.py</code>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-(--color-tertiary) font-bold text-xs mt-0.5">2.</span>
                    El dashboard estará disponible en <code className="text-xs bg-(--color-surface) px-1.5 py-0.5 rounded border border-(--color-border) font-mono">localhost:8050</code>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-(--color-tertiary) font-bold text-xs mt-0.5">3.</span>
                    O configura la URL de Power BI en este componente para embeber directamente.
                  </li>
                </ol>
              </div>

              <div className="mt-6 flex justify-center gap-3">
                <a
                  href="http://localhost:8050"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm font-medium text-(--color-tertiary) hover:text-(--color-tertiary-hover) transition-colors"
                >
                  Abrir Plotly Dash <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        {[
          { title: "Tecnología", value: "Plotly Dash 2.x + Kepler.gl", desc: "100% Python · 100% open-source" },
          { title: "Actualización", value: "Semanal automática", desc: "Pipeline corre cada lunes" },
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
