"use client"

import { useState, useEffect } from "react"
import useSWR from "swr"
import { fetcher, poster } from "@/lib/api"
import { Badge } from "@/components/ui/Badge"
import { TrendingUp, AlertCircle, ArrowUpRight, Search, RefreshCcw } from "lucide-react"
import { Skeleton, LottieLoader } from "@/components/ui/LottieLoader"

// Backend shape: GET /api/v1/trends?departamento_code=XX&disease=YY
interface TrendsResponse {
  departamento_code: string
  disease: string
  records: TrendRecord[]
}

interface TrendRecord {
  epi_year: number
  epi_week: number
  week_start_date: string
  disease: string
  trends_score: number
}

const DEPARTMENTS = [
  { code: "05", name: "Antioquia" },
  { code: "08", name: "Atlántico" },
  { code: "13", name: "Bolívar" },
  { code: "25", name: "Cundinamarca" },
  { code: "41", name: "Huila" },
  { code: "52", name: "Nariño" },
  { code: "68", name: "Santander" },
  { code: "73", name: "Tolima" },
  { code: "76", name: "Valle del Cauca" },
]

const DISEASES = ["dengue", "malaria", "zika", "chikungunya"]

function TrendBar({ score, maxScore }: { score: number; maxScore: number }) {
  const pct = maxScore > 0 ? (score / maxScore) * 100 : 0
  const color = pct > 75 ? "bg-(--color-danger)" : pct > 50 ? "bg-(--color-warning)" : "bg-(--color-tertiary)"
  return (
    <div className="flex items-center gap-2 w-full">
      <div className="flex-1 h-2 bg-(--color-background) rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${Math.min(pct, 100)}%` }} />
      </div>
      <span className="text-xs font-mono text-(--color-secondary) w-10 text-right">{score.toFixed(0)}</span>
    </div>
  )
}

export default function TendenciasDashboard() {
  const [selectedDept, setSelectedDept] = useState("52") // Nariño default
  const [selectedDisease, setSelectedDisease] = useState("dengue")

  const apiUrl = `/api/v1/trends?departamento_code=${selectedDept}&disease=${selectedDisease}&limit=12`
  const { data, error, isLoading, mutate } = useSWR<TrendsResponse>(apiUrl, fetcher)
  const [isSyncing, setIsSyncing] = useState(false)
  const [lastSync, setLastSync] = useState<number | null>(null)

  useEffect(() => {
    const saved = localStorage.getItem("ecos_last_scrape_trends")
    if (saved) {
      setTimeout(() => setLastSync(parseInt(saved)), 0)
    }
  }, [])

  const handleSync = async () => {
    setIsSyncing(true)
    try {
      const response = await poster("/api/v1/scraping/trigger")
      
      if (response.status === "started") {
        await new Promise(resolve => setTimeout(resolve, 3000))
        const now = Date.now()
        localStorage.setItem("ecos_last_scrape_trends", now.toString())
        setLastSync(now)
      } else if (response.status === "cooldown") {
        await new Promise(resolve => setTimeout(resolve, 1500))
        const lastRun = new Date(response.last_run).getTime()
        localStorage.setItem("ecos_last_scrape_trends", lastRun.toString())
        setLastSync(lastRun)
      }
      
      await mutate()
    } catch (err) {
      console.error("Error triggering trends scrape:", err)
    } finally {
      setIsSyncing(false)
    }
  }

  const deptName = DEPARTMENTS.find(d => d.code === selectedDept)?.name || selectedDept
  const maxScore = data?.records?.reduce((max, r) => Math.max(max, r.trends_score), 0) || 100

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-10 max-w-6xl min-h-screen">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-10 gap-4 border-b border-(--color-border-strong) pb-6">
        <div>
          <p className="font-display text-xs uppercase tracking-[0.2em] text-(--color-tertiary) mb-2 font-semibold">Dashboard 2</p>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-(--color-primary) flex items-center gap-3">
            <TrendingUp className="text-(--color-tertiary) w-8 h-8 md:w-9 md:h-9" />
            Señales Tempranas
          </h1>
          <p className="text-(--color-secondary) mt-2 max-w-2xl text-base">
            Monitor de interés de búsqueda en Google Trends para síntomas clave por departamento. 
            Las desviaciones por encima de 3.0 SD disparan una alerta institucional.
          </p>
        </div>
        <div className="flex flex-col items-end gap-3">
          <Badge variant="outline" className="px-3 py-1.5 bg-(--color-surface) text-(--color-secondary)">
            Fuente: pytrends API
          </Badge>
          <div className="flex flex-col items-end gap-1">
            <button
              onClick={handleSync}
              disabled={isSyncing}
              className="inline-flex items-center gap-2 px-3 py-1.5 bg-(--color-surface) border border-(--color-border) rounded-md text-xs font-semibold text-(--color-primary) hover:border-(--color-border-strong) hover:bg-gray-50 transition-all disabled:opacity-50"
            >
              <RefreshCcw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin text-(--color-tertiary)" : "text-(--color-secondary)"}`} />
              {isSyncing ? "Scrapeando Google Trends..." : "Sincronizar Scraping"}
            </button>
            {lastSync && (
              <p className="text-[9px] text-(--color-muted) font-display uppercase tracking-wider">
                Última act: {new Date(lastSync).toLocaleDateString("es-CO", { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-8">
        <div className="flex-1">
          <label className="text-[10px] font-display uppercase tracking-wider text-(--color-muted) font-semibold mb-1.5 block">
            Departamento
          </label>
          <div className="relative">
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="w-full appearance-none bg-(--color-surface) border border-(--color-border) rounded-md px-4 py-2.5 text-sm text-(--color-primary) focus:outline-none focus:border-(--color-tertiary) focus:ring-2 focus:ring-(--color-tertiary-alpha) transition-all pr-10"
            >
              {DEPARTMENTS.map(d => (
                <option key={d.code} value={d.code}>{d.name}</option>
              ))}
            </select>
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-(--color-muted) pointer-events-none" />
          </div>
        </div>
        <div className="sm:w-48">
          <label className="text-[10px] font-display uppercase tracking-wider text-(--color-muted) font-semibold mb-1.5 block">
            Enfermedad
          </label>
          <select
            value={selectedDisease}
            onChange={(e) => setSelectedDisease(e.target.value)}
            className="w-full appearance-none bg-(--color-surface) border border-(--color-border) rounded-md px-4 py-2.5 text-sm text-(--color-primary) capitalize focus:outline-none focus:border-(--color-tertiary) focus:ring-2 focus:ring-(--color-tertiary-alpha) transition-all"
          >
            {DISEASES.map(d => (
              <option key={d} value={d} className="capitalize">{d}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Current selection summary */}
      <div className="bg-(--color-surface) border border-(--color-border) rounded-md p-5 mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <p className="text-[10px] font-display uppercase tracking-wider text-(--color-muted) font-semibold mb-1">
              Consultando
            </p>
            <p className="text-lg font-bold text-(--color-primary)">
              {deptName} — <span className="capitalize">{selectedDisease}</span>
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-[10px] font-display uppercase tracking-wider text-(--color-muted) font-semibold">Registros</p>
              <p className="text-lg font-bold text-(--color-primary)">{data?.records?.length ?? "—"}</p>
            </div>
            <div className="text-right">
              <p className="text-[10px] font-display uppercase tracking-wider text-(--color-muted) font-semibold">Pico</p>
              <p className="text-lg font-bold text-(--color-primary)">{maxScore?.toFixed(0) ?? "—"}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <Skeleton key={i} className="h-12 bg-(--color-surface) border border-(--color-border)" />
          ))}
        </div>
      )}

      {error && (
        <div className="flex items-center gap-3 p-5 bg-(--color-danger-alpha) border border-(--color-danger) rounded-md">
          <AlertCircle className="w-5 h-5 text-(--color-danger) shrink-0" />
          <div>
            <p className="font-bold text-(--color-danger) text-sm">Error de conexión</p>
            <p className="text-sm text-(--color-primary)">No se pudo cargar la informacion. Revisa tu conexion e intenta de nuevo.</p>
          </div>
        </div>
      )}

      {data && data.records && data.records.length > 0 && (
        <div className="bg-(--color-surface) border border-(--color-border) rounded-md overflow-hidden">
          {/* Table header */}
          <div className="grid grid-cols-12 gap-4 px-5 py-3 bg-(--color-background) border-b border-(--color-border) text-[10px] font-display uppercase tracking-wider text-(--color-muted) font-semibold">
            <div className="col-span-2">Semana</div>
            <div className="col-span-2">Fecha</div>
            <div className="col-span-6">Volumen de Búsqueda</div>
            <div className="col-span-2 text-right">Score</div>
          </div>

          {/* Rows */}
          <div className="divide-y divide-(--color-border)">
            {data.records.map((record, i) => {
              const isHigh = record.trends_score > 70
              const isMed = record.trends_score > 40
              return (
                <div key={i} className="grid grid-cols-12 gap-4 px-5 py-3 items-center hover:bg-(--color-surface-hover) transition-colors">
                  <div className="col-span-2">
                    <span className="text-sm font-semibold text-(--color-primary)">S{record.epi_week}</span>
                    <span className="text-xs text-(--color-muted) ml-1">/ {record.epi_year}</span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-xs text-(--color-secondary)">
                      {new Date(record.week_start_date).toLocaleDateString("es-CO", { day: "numeric", month: "short" })}
                    </span>
                  </div>
                  <div className="col-span-6">
                    <TrendBar score={record.trends_score} maxScore={maxScore} />
                  </div>
                  <div className="col-span-2 flex items-center justify-end gap-1.5">
                    <span className={`text-sm font-bold ${isHigh ? "text-(--color-danger)" : isMed ? "text-(--color-warning)" : "text-(--color-primary)"}`}>
                      {record.trends_score.toFixed(1)}
                    </span>
                    {isHigh && <ArrowUpRight className="w-3.5 h-3.5 text-(--color-danger)" />}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {data && (!data.records || data.records.length === 0) && (
        <div className="text-center py-20 border border-(--color-border) rounded-md bg-(--color-surface)">
          <LottieLoader variant="search" size={120} className="mx-auto opacity-75 mb-2" />
          <p className="text-(--color-secondary)">No hay datos de tendencias para esta combinación.</p>
          <p className="text-xs text-(--color-muted) mt-1">Intenta con otro departamento o enfermedad.</p>
        </div>
      )}

      {/* Methodology note */}
      <div className="mt-8 p-4 bg-(--color-surface) border border-(--color-border) rounded-md">
        <p className="text-[10px] font-display uppercase tracking-wider text-(--color-muted) font-semibold mb-2">
          ⚠️ Nota metodológica
        </p>
        <p className="text-xs text-(--color-secondary) leading-relaxed">
          Google Trends tiene sesgos de brecha digital. Los departamentos con baja penetración de internet (Vaupés, Guainía, Chocó rural) 
          no generan datos suficientes. El índice 0–100 es relativo al período consultado, no absoluto. ECOS usa Trends como señal 
          de corroboración (peso 5–8% en el modelo), no como predictor primario.
        </p>
      </div>
    </div>
  )
}
