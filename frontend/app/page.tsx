"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { DashboardHero } from "@/components/DashboardHero"
import { SignalIndicator } from "@/components/SignalIndicator"
import { ChatAssistant } from "@/components/ChatAssistant"
import { PowerBIEmbed } from "@/components/PowerBIEmbed"
import { PredictionPanel } from "@/components/PredictionPanel"
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import { Button } from "@/components/ui/Button"
import { getHistory, getSummary } from "@/lib/api"
import { cn } from "@/lib/utils"
import { 
  BarChart3, 
  Map, 
  History, 
  ArrowUpRight, 
  Activity, 
  Wind, 
  Search,
  LayoutDashboard,
  Shield
} from "lucide-react"

export default function Home() {
  const [isLoaded, setIsLoaded] = React.useState(false)
  const [latestData, setLatestData] = React.useState<any>(null)

  React.useEffect(() => {
    const timer = setTimeout(() => setIsLoaded(true), 1000)
    
    // Fetch real summary from Supabase
    getSummary().then(res => {
      if (res.success && res.data) {
        setLatestData(res.data)
      }
    }).catch(err => console.error("Error fetching summary:", err))

    return () => clearTimeout(timer)
  }, [])

  if (!isLoaded) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <motion.div
          animate={{
            scale: [1, 1.1, 1],
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="flex flex-col items-center gap-4"
        >
          <div className="h-16 w-16 rounded-full border-4 border-accent border-t-transparent animate-spin" />
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-accent">ECOS</p>
        </motion.div>
      </div>
    )
  }

  return (
    <main className="relative min-h-screen pb-20">
      {/* Dynamic Background */}
      <div className="fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(140,68,26,0.12),_transparent_35%),radial-gradient(circle_at_80%_20%,_rgba(22,114,90,0.1),_transparent_28%),linear-gradient(180deg,_#f7f1e8_0%,_#efe6d8_100%)]" />

      <div className="mx-auto max-w-7xl px-6 sm:px-10 lg:px-12">
        {/* Navigation */}
        <nav className="flex items-center justify-between py-6 border-b border-border">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2">
              <div className="bg-primary p-1.5 rounded-lg">
                <Activity className="h-5 w-5 text-primary-contrast" />
              </div>
              <span className="font-bold text-xl tracking-tighter">ECOS</span>
            </div>
            
            <div className="hidden md:flex items-center gap-6">
              {[
                { name: 'Dashboard', path: '#dashboard' },
                { name: 'Señales', path: '#senales' },
                { name: 'Predicciones', path: '#predicciones' },
                { name: 'Reportes', path: '#reportes' }
              ].map((item) => (
                <a 
                  key={item.name} 
                  href={item.path} 
                  className="text-sm font-medium text-foreground-muted hover:text-foreground transition-colors"
                >
                  {item.name}
                </a>
              ))}
            </div>
          </div>
          

        </nav>

        {/* Hero Section */}
        <DashboardHero />

        {/* Real-time Signals Grid */}
        <section id="senales" className="mt-12 scroll-mt-24">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold tracking-tight text-foreground">Señales Ambientales</h2>
              <p className="text-sm text-foreground-muted mt-1">Factores determinantes de riesgo biológico</p>
            </div>
            <Button variant="ghost" size="sm" className="text-accent" onClick={() => window.location.href = "#dashboard"}>
              Ver todas <ArrowUpRight className="ml-1 h-4 w-4" />
            </Button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <SignalIndicator 
              label="Precipitación"
              value={latestData?.avg_precip !== undefined ? `${latestData.avg_precip.toFixed(1)}mm` : "---"}
              trend={latestData?.avg_precip > 100 ? "up" : "stable"}
              status={latestData?.avg_precip > 150 ? "danger" : latestData?.avg_precip > 80 ? "warning" : "signal"}
              description={latestData?.avg_precip !== undefined ? "Promedio nacional de la última semana" : "Datos sincronizados con Supabase"}
            />
            <SignalIndicator 
              label="Temperatura"
              value={latestData?.avg_temp !== undefined ? `${latestData.avg_temp.toFixed(1)}°C` : "---"}
              trend="stable"
              status="signal"
              description={latestData?.avg_temp !== undefined ? "Promedio nacional actual" : "Datos sincronizados con Supabase"}
            />
            <SignalIndicator 
              label="Casos de Dengue (Semana)"
              value={latestData?.total_cases !== undefined ? `${latestData.total_cases}` : "---"}
              trend="stable"
              status={latestData?.total_cases > 500 ? "danger" : "warning"}
              description="Total nacional reportado en la última semana"
            />
          </div>
        </section>

        {/* Power BI Integration */}
        <section id="dashboard" className="mt-16 scroll-mt-24">
          <div className="mb-8">
            <h2 className="text-2xl font-bold tracking-tight text-foreground">Dashboard Operativo</h2>
            <p className="text-sm text-foreground-muted mt-1">Exploración profunda de datos y tendencias nacionales</p>
          </div>
          <PowerBIEmbed />
        </section>

        {/* Insights & Analysis Section */}
        <div id="predicciones" className="mt-16 scroll-mt-24">
          <div className="mb-8">
            <h2 className="text-2xl font-bold tracking-tight text-foreground">Situación Epidemiológica</h2>
            <p className="text-sm text-foreground-muted mt-1">Resumen operativo basado en los últimos reportes nacionales</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="bg-surface border-border hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Activity className="h-5 w-5 text-danger" />
                  Incidencia Actual
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-black text-foreground mb-2">
                  {latestData?.total_cases !== undefined ? latestData.total_cases : "---"}
                </div>
                <p className="text-sm text-foreground-muted">
                  Casos nacionales confirmados en la última semana epidemiológica sincronizada desde Supabase.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-surface border-border hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Map className="h-5 w-5 text-accent" />
                  Estado de Alerta
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={cn(
                  "text-2xl font-bold mb-2",
                  latestData?.total_cases > 500 ? "text-danger" : "text-warning"
                )}>
                  {latestData?.total_cases > 500 ? "ALERTA ROJA" : "ALERTA NARANJA"}
                </div>
                <p className="text-sm text-foreground-muted">
                  Estado basado en el volumen nacional de reportes comparado con el promedio histórico dinámico.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-surface border-border hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Shield className="h-5 w-5 text-primary" />
                  Recomendación INS
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-lg font-bold text-foreground mb-2">
                  Activación de Protocolos
                </div>
                <p className="text-sm text-foreground-muted">
                  Fortalecer la vigilancia pasiva y activa en IPS. Implementar fumigación perimetral en focos primarios identificados.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-24 pt-12 border-t border-border flex flex-col md:flex-row items-center justify-between gap-6 pb-12">
          <div className="flex items-center gap-2">
            <div className="bg-foreground p-1 rounded">
              <Activity size={14} className="text-background" />
            </div>
            <span className="font-bold text-sm tracking-tighter">ECOS</span>
            <span className="text-xs text-foreground-muted ml-4">© 2026 Plataforma Nacional de Alerta Temprana</span>
          </div>
          
          <div className="flex gap-8">
            {['Privacidad', 'Términos', 'Metodología', 'Contacto'].map((item) => (
              <a key={item} href="#" className="text-xs font-medium text-foreground-muted hover:text-foreground transition-colors">
                {item}
              </a>
            ))}
          </div>
        </footer>
      </div>

      {/* Floating Assistant */}
      <ChatAssistant />
    </main>
  )
}
