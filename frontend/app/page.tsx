"use client"

import Link from "next/link"
import { Activity, TrendingUp, Newspaper, ShieldAlert, Map, Zap, ArrowRight, Database, CloudSun, Radio, Scale } from "lucide-react"
import { Button } from "@/components/ui/Button"
import { Badge } from "@/components/ui/Badge"
import { LottieLoader } from "@/components/ui/LottieLoader"

const MODULES = [
  {
    icon: TrendingUp,
    title: "Señales Tempranas",
    description: "Google Trends + análisis de Z-Score para detectar picos de interés en síntomas clave antes de que los casos sean reportados oficialmente.",
    href: "/tendencias",
    tag: "TRENDS API",
  },
  {
    icon: Newspaper,
    title: "Monitor de Medios",
    description: "Feed de noticias clasificado por NLP. Extracción automática de enfermedad, departamento y nivel de alerta de medios colombianos.",
    href: "/noticias",
    tag: "NLP PIPELINE",
  },
  {
    icon: ShieldAlert,
    title: "Predicción Híbrida",
    description: "Prophet (estacionalidad) + XGBoost (variables exógenas) con explicabilidad SHAP. Cada predicción muestra por qué el modelo alerta.",
    href: "/dashboard",
    tag: "ML MODEL",
  },
  {
    icon: Map,
    title: "Movilidad × Enfermedad",
    description: "Correlación entre flujos de pasajeros intermunicipales y propagación de brotes. Mapa OD con arcos de riesgo.",
    href: "/dashboard",
    tag: "GEO DATA",
  },
  {
    icon: Scale,
    title: "Pruebas ANOVA",
    description: "Comparador estadístico multianual para contrastar la severidad del dengue a lo largo de los años con análisis post-hoc Tukey y lenguaje claro.",
    href: "/anova",
    tag: "ESTADÍSTICA",
  },
]

const DISEASES = [
  { name: "Dengue", emoji: "🦟", color: "bg-(--color-danger-alpha) text-(--color-danger)" },
  { name: "Malaria", emoji: "🦟", color: "bg-(--color-warning-alpha) text-(--color-warning)" },
  { name: "Zika", emoji: "🧬", color: "bg-blue-50 text-blue-700" },
  { name: "Chikungunya", emoji: "🔬", color: "bg-purple-50 text-purple-700" },
]

const DATA_SOURCES = [
  { name: "datos.gov.co", desc: "SIVIGILA histórico", icon: Database },
  { name: "Google Trends", desc: "Señales de búsqueda", icon: TrendingUp },
  { name: "Open-Meteo", desc: "Clima en tiempo real", icon: CloudSun },
  { name: "RSS Medios", desc: "Scraping activo", icon: Radio },
]

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-(--color-background)">

      {/* ═══════════════ HERO ═══════════════ */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, var(--color-primary) 1px, transparent 0)`,
          backgroundSize: "32px 32px",
        }} />

        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24 relative">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
            {/* Left: Text */}
            <div className="max-w-xl">
              <div className="animate-fade-in-up inline-flex items-center gap-2 mb-6">
                <Badge variant="outline" className="text-(--color-secondary) px-3 py-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-(--color-success) mr-2 inline-block animate-pulse" />
                  VIGILANCIA EPIDEMIOLÓGICA
                </Badge>
              </div>

              <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-(--color-primary) leading-[1.08] mb-5 animate-fade-in-up" style={{ animationDelay: "0.1s" }}>
                Observatorio de{" "}
                <span className="relative inline-block">
                  <span className="relative z-10">Riesgo Epidemiológico</span>
                  <span className="absolute bottom-1 left-0 right-0 h-3 bg-(--color-tertiary-alpha) rounded-sm z-0" />
                </span>
              </h1>

              <p className="text-lg text-(--color-secondary) leading-relaxed mb-8 animate-fade-in-up" style={{ animationDelay: "0.2s" }}>
                ECOS cruza datos climáticos, movilidad y señales NLP para predecir brotes de Dengue, Malaria, Zika y Chikungunya{" "}
                <strong className="text-(--color-primary)">2–4 semanas antes</strong> del reporte oficial.
              </p>

              <div className="flex flex-col sm:flex-row gap-3 animate-fade-in-up" style={{ animationDelay: "0.3s" }}>
                <Button variant="primary" shape="md" size="lg" asChild>
                  <Link href="/tendencias" className="gap-2">
                    Explorar Tendencias <ArrowRight className="w-4 h-4" />
                  </Link>
                </Button>
                <Button variant="outline" shape="md" size="lg" asChild>
                  <Link href="/dashboard">Ver Dashboard</Link>
                </Button>
              </div>
            </div>

            {/* Right: Lottie Animation */}
            <div className="hidden md:flex justify-center items-center animate-fade-in-up" style={{ animationDelay: "0.4s" }}>
              <LottieLoader
                variant="health"
                size={320}
                message=""
              />
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════ STATS ═══════════════ */}
      <section className="border-y border-(--color-border) bg-(--color-surface)">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-(--color-border)">
            {[
              { value: "32", label: "Departamentos", desc: "Cobertura nacional" },
              { value: "4", label: "Enfermedades", desc: "Dengue · Malaria · Zika · Chiku" },
              { value: "2–4 sem", label: "Anticipación", desc: "Antes del reporte oficial" },
              { value: "6", label: "Fuentes de datos", desc: "SIVIGILA · Trends · Clima · RSS" },
            ].map((stat, i) => (
              <div key={i} className="py-8 px-4 md:px-6 text-center md:text-left">
                <p className="text-2xl md:text-3xl font-bold text-(--color-primary) tracking-tight">{stat.value}</p>
                <p className="text-sm font-semibold text-(--color-primary) mt-1">{stat.label}</p>
                <p className="text-xs text-(--color-muted) mt-0.5">{stat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════ HOW IT WORKS ═══════════════ */}
      <section className="py-20 md:py-24 bg-(--color-background)">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-5xl">
          <div className="text-center mb-14">
            <p className="font-display text-xs uppercase tracking-[0.2em] text-(--color-tertiary) mb-3 font-semibold">Metodología</p>
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-(--color-primary)">Cómo funciona ECOS</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-4 relative stagger-children">
            <div className="hidden md:block absolute top-16 left-[20%] right-[20%] h-px bg-(--color-border-strong)" />

            {[
              { step: "01", title: "Ingesta", desc: "6 datasets de datos.gov.co + Google Trends + RSS de medios colombianos + clima Open-Meteo.", icon: Database },
              { step: "02", title: "Modelo IA", desc: "Prophet captura estacionalidad. XGBoost procesa variables exógenas. SHAP explica cada predicción.", icon: Zap },
              { step: "03", title: "Alerta", desc: "Dashboards en tiempo real + chat RAG conversacional + reportes PDF para secretarías de salud.", icon: ShieldAlert },
            ].map((item, i) => (
              <div key={i} className="relative bg-(--color-surface) border border-(--color-border) rounded-md p-6 text-center hover:border-(--color-border-strong) hover:shadow-sm transition-all">
                <div className="w-12 h-12 rounded-full bg-(--color-tertiary-alpha) flex items-center justify-center mx-auto mb-4 relative z-10">
                  <item.icon className="w-5 h-5 text-(--color-tertiary)" />
                </div>
                <span className="font-display text-[10px] uppercase tracking-[0.2em] text-(--color-muted) font-semibold">Paso {item.step}</span>
                <h3 className="text-lg font-bold text-(--color-primary) mt-2 mb-2">{item.title}</h3>
                <p className="text-sm text-(--color-secondary) leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════ MODULES ═══════════════ */}
      <section className="py-20 md:py-24 bg-(--color-surface) border-t border-(--color-border)">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-12 gap-4">
            <div>
              <p className="font-display text-xs uppercase tracking-[0.2em] text-(--color-tertiary) mb-3 font-semibold">Arquitectura</p>
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-(--color-primary)">Módulos del Sistema</h2>
            </div>
            <Badge variant="outline" className="px-3 py-1.5 text-(--color-secondary)">
              <Activity className="w-3 h-3 mr-1.5" />
              4 Módulos
            </Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 stagger-children">
            {MODULES.map((mod, i) => (
              <Link key={i} href={mod.href} className="group block">
                <div className="h-full bg-(--color-background) border border-(--color-border) rounded-md p-6 transition-all hover:border-(--color-border-strong) hover:shadow-sm group-hover:-translate-y-0.5">
                  <div className="flex items-start justify-between mb-4">
                    <div className="p-2.5 bg-(--color-surface) border border-(--color-border) rounded-sm group-hover:border-(--color-tertiary-glow) transition-colors">
                      <mod.icon className="h-5 w-5 text-(--color-tertiary)" />
                    </div>
                    <span className="font-display text-[9px] uppercase tracking-[0.15em] text-(--color-muted) font-semibold px-2 py-0.5 bg-(--color-surface) rounded-sm border border-(--color-border)">
                      {mod.tag}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-(--color-primary) mb-2 group-hover:text-(--color-tertiary) transition-colors">{mod.title}</h3>
                  <p className="text-sm text-(--color-secondary) leading-relaxed">{mod.description}</p>
                  <div className="mt-4 flex items-center text-sm font-medium text-(--color-tertiary) opacity-0 group-hover:opacity-100 transition-opacity">
                    Explorar <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════ DISEASES ═══════════════ */}
      <section className="py-20 md:py-24 bg-(--color-background) border-t border-(--color-border)">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-5xl">
          <div className="text-center mb-12">
            <p className="font-display text-xs uppercase tracking-[0.2em] text-(--color-tertiary) mb-3 font-semibold">Vigilancia</p>
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-(--color-primary)">Enfermedades Monitoreadas</h2>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 stagger-children">
            {DISEASES.map((d, i) => (
              <div key={i} className="bg-(--color-surface) border border-(--color-border) rounded-md p-5 text-center hover:border-(--color-border-strong) transition-all hover:shadow-sm">
                <span className="text-3xl mb-3 block">{d.emoji}</span>
                <h3 className="font-bold text-(--color-primary) text-base">{d.name}</h3>
                <div className="mt-3">
                  <span className={`inline-flex text-[10px] font-display uppercase tracking-wider px-2 py-0.5 rounded-sm font-semibold ${d.color}`}>
                    SIVIGILA
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════ DATA SOURCES ═══════════════ */}
      <section className="py-16 border-t border-(--color-border) bg-(--color-surface)">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-4xl">
          <p className="font-display text-xs uppercase tracking-[0.2em] text-(--color-muted) text-center mb-8 font-semibold">
            Fuentes de datos abiertas
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {DATA_SOURCES.map((src, i) => (
              <div key={i} className="flex items-center gap-3 px-4 py-3 rounded-sm bg-(--color-background) border border-(--color-border)">
                <src.icon className="w-4 h-4 text-(--color-secondary) shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-(--color-primary) leading-tight">{src.name}</p>
                  <p className="text-[10px] text-(--color-muted)">{src.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
