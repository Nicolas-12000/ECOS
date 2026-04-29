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
import { getHistory } from "@/lib/api"
import { 
  BarChart3, 
  Map, 
  History, 
  ArrowUpRight, 
  Activity, 
  Wind, 
  Search,
  LayoutDashboard
} from "lucide-react"

export default function Home() {
  const [isLoaded, setIsLoaded] = React.useState(false)
  const [latestData, setLatestData] = React.useState<any>(null)

  React.useEffect(() => {
    const timer = setTimeout(() => setIsLoaded(true), 1000)
    
    // Fetch real history for a default location (Medellín - 05001) to show real environmental data
    getHistory('05001', 'dengue', 1).then(data => {
      if (data && data.records && data.records.length > 0) {
        setLatestData(data.records[0])
      }
    }).catch(err => console.error("Error fetching data:", err))

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
              {['Dashboard', 'Señales', 'Predicciones', 'Reportes'].map((item) => (
                <a 
                  key={item} 
                  href="#" 
                  className="text-sm font-medium text-foreground-muted hover:text-foreground transition-colors"
                >
                  {item}
                </a>
              ))}
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <Button variant="outline" size="sm">
              <History className="mr-2 h-4 w-4" />
              Historial
            </Button>
            <Button size="sm">
              <LayoutDashboard className="mr-2 h-4 w-4" />
              Admin
            </Button>
          </div>
        </nav>

        {/* Hero Section */}
        <DashboardHero />

        {/* Real-time Signals Grid */}
        <section className="mt-12">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold tracking-tight text-foreground">Señales Ambientales</h2>
              <p className="text-sm text-foreground-muted mt-1">Factores determinantes de riesgo biológico</p>
            </div>
            <Button variant="ghost" size="sm" className="text-accent">
              Ver todas <ArrowUpRight className="ml-1 h-4 w-4" />
            </Button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <SignalIndicator 
              label="Precipitación"
              value={latestData?.precipitation_mm !== null && latestData?.precipitation_mm !== undefined ? `${latestData.precipitation_mm}mm` : "120mm"}
              trend={latestData?.precipitation_mm > 100 ? "up" : "stable"}
              status={latestData?.precipitation_mm > 150 ? "danger" : latestData?.precipitation_mm > 80 ? "warning" : "signal"}
              description={latestData?.precipitation_mm !== null ? "Dato real de estación local" : "Aumento significativo en la región pacífica"}
            />
            <SignalIndicator 
              label="Temperatura"
              value={latestData?.temp_avg_c !== null && latestData?.temp_avg_c !== undefined ? `${latestData.temp_avg_c}°C` : "28.5°C"}
              trend="stable"
              status="signal"
              description={latestData?.temp_avg_c !== null ? "Promedio nacional actual" : "Dentro de rangos normales históricos"}
            />
            <SignalIndicator 
              label="Humedad Relativa"
              value={latestData?.humidity_avg_pct !== null && latestData?.humidity_avg_pct !== undefined ? `${latestData.humidity_avg_pct}%` : "82%"}
              trend="up"
              status="warning"
              description="Condiciones óptimas para vector Aedes"
            />
            <SignalIndicator 
              label="Vigilancia RIPS"
              value="+15.2%"
              trend="up"
              status="danger"
              description="Alerta por incremento de consultas febriles"
            />
          </div>
        </section>

        {/* Power BI Integration */}
        <section className="mt-16">
          <div className="mb-8">
            <h2 className="text-2xl font-bold tracking-tight text-foreground">Dashboard Operativo</h2>
            <p className="text-sm text-foreground-muted mt-1">Exploración profunda de datos y tendencias nacionales</p>
          </div>
          <PowerBIEmbed />
        </section>

        {/* Insights & Analysis Section */}
        <div className="mt-16 grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Analysis Card */}
          <Card className="lg:col-span-2 overflow-hidden flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between border-b border-border/50 pb-4">
              <div>
                <CardTitle>Análisis de Tendencias</CardTitle>
                <p className="text-xs text-foreground-muted mt-1">Comparativa semanal por patología</p>
              </div>
              <div className="flex gap-2">
                <Badge variant="outline" className="lowercase">Semana {latestData?.epi_week || '17'}</Badge>
                <Badge variant="signal" className="lowercase">Estable</Badge>
              </div>
            </CardHeader>
            <CardContent className="flex-1 pt-8 min-h-[350px] flex items-center justify-center bg-background-soft/30">
              <div className="flex flex-col items-center text-foreground-muted gap-4">
                <BarChart3 size={48} className="opacity-20" />
                <p className="text-sm font-medium">Visualización de datos en tiempo real</p>
                <div className="flex items-end gap-1 h-32">
                  {[40, 70, 45, 90, 65, 80, 50, 60, 30, 85].map((h, i) => (
                    <motion.div
                      key={i}
                      initial={{ height: 0 }}
                      animate={{ height: h }}
                      transition={{ delay: i * 0.1, duration: 0.5 }}
                      className="w-6 bg-accent/40 rounded-t-sm hover:bg-accent/60 transition-colors cursor-help"
                    />
                  ))}
                </div>
                <div className="flex gap-4 mt-4 text-[10px] font-bold uppercase tracking-widest opacity-40">
                  <div className="flex items-center gap-1"><div className="h-2 w-2 rounded-full bg-accent" /> Casos</div>
                  <div className="flex items-center gap-1"><div className="h-2 w-2 rounded-full bg-signal" /> Clima</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Real Prediction Panel */}
          <PredictionPanel />
        </div>

        {/* Quick Actions / Feature Cards */}
        <section className="mt-16 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6">
          {[
            { 
              title: "Predicción", 
              desc: "Horizonte de 1 a 4 semanas por municipio.",
              icon: Activity,
              color: "text-blue-500"
            },
            { 
              title: "Clima", 
              desc: "Impacto de El Niño y variabilidad local.",
              icon: Wind,
              color: "text-amber-500"
            },
            { 
              title: "RAG Docs", 
              desc: "Consulta protocolos y guías oficiales INS.",
              icon: Search,
              color: "text-emerald-500"
            },
            { 
              title: "Exportar", 
              desc: "Reportes automatizados para secretarías.",
              icon: History,
              color: "text-purple-500"
            },
          ].map((item, i) => (
            <motion.div
              key={i}
              whileHover={{ y: -5 }}
              className="p-6 rounded-3xl bg-surface border border-border shadow-sm hover:shadow-xl transition-all"
            >
              <div className={`p-3 rounded-2xl bg-background-soft w-fit mb-4 ${item.color}`}>
                <item.icon size={24} />
              </div>
              <h3 className="font-bold text-foreground">{item.title}</h3>
              <p className="text-sm text-foreground-muted mt-2 leading-relaxed">{item.desc}</p>
            </motion.div>
          ))}
        </section>

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
