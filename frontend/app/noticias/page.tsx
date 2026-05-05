"use client"

import { useState, useEffect } from "react"
import useSWR from "swr"
import { fetcher, poster } from "@/lib/api"
import { Badge } from "@/components/ui/Badge"
import { ExternalLink, Clock, Newspaper, AlertTriangle, Radio, RefreshCcw } from "lucide-react"
import { Skeleton, LottieLoader } from "@/components/ui/LottieLoader"

// Backend returns this shape from /api/v1/news
interface NewsArticle {
  title: string
  link: string
  source: string
  published: string
  summary: string | null
  diseases: string[]
}

const DISEASE_COLORS: Record<string, string> = {
  dengue: "destructive",
  malaria: "warning",
  zika: "tertiary",
  chikungunya: "tertiary",
}

function NewsCard({ article }: { article: NewsArticle }) {

  return (
    <article className="group bg-(--color-surface) border border-(--color-border) rounded-md overflow-hidden hover:border-(--color-border-strong) hover:shadow-sm transition-all">
      <div className="p-5">
        {/* Top row: disease badges + date */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-1.5 flex-wrap">
            {article.diseases?.length > 0 ? (
              article.diseases.map((d, i) => (
                <Badge key={i} variant={DISEASE_COLORS[d] as "destructive" | "warning" | "tertiary" | "outline" || "outline"}>
                  {d}
                </Badge>
              ))
            ) : (
              <Badge variant="outline">General</Badge>
            )}
          </div>
          <span className="flex items-center text-[10px] font-display text-(--color-muted) uppercase tracking-wider shrink-0 ml-2">
            <Clock className="w-3 h-3 mr-1" />
            {article.published ? new Date(article.published).toLocaleDateString("es-CO", { day: "numeric", month: "short" }) : "—"}
          </span>
        </div>

        {/* Title */}
        <h3 className="text-base font-bold text-(--color-primary) leading-snug mb-2 group-hover:text-(--color-tertiary) transition-colors line-clamp-2">
          {article.title}
        </h3>

        {/* Summary */}
        {article.summary && (
          <p className="text-sm text-(--color-secondary) leading-relaxed line-clamp-3 mb-4">
            {article.summary}
          </p>
        )}

        {/* Bottom: source + link */}
        <div className="flex items-center justify-between pt-3 border-t border-(--color-border)">
          <span className="text-[11px] font-display uppercase tracking-wider text-(--color-muted) font-medium">
            {article.source}
          </span>
          {article.link && (
            <a
              href={article.link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center text-xs font-medium text-(--color-tertiary) hover:text-(--color-tertiary-hover) transition-colors"
            >
              Leer artículo <ExternalLink className="w-3 h-3 ml-1" />
            </a>
          )}
        </div>
      </div>
    </article>
  )
}

export default function NoticiasDashboard() {
  const { data, error, isLoading, mutate } = useSWR<NewsArticle[]>("/api/v1/news", fetcher)
  const [isSyncing, setIsSyncing] = useState(false)
  const [lastSync, setLastSync] = useState<number | null>(null)

  useEffect(() => {
    const saved = localStorage.getItem("ecos_last_scrape_news")
    if (saved) {
      setTimeout(() => setLastSync(parseInt(saved)), 0)
    }
  }, [])

  const handleSync = async () => {
    setIsSyncing(true)
    try {
      const response = await poster("/api/v1/scraping/trigger")
      
      if (response.status === "started") {
        // Real process started, wait a bit and refresh
        await new Promise(resolve => setTimeout(resolve, 3000))
        const now = Date.now()
        localStorage.setItem("ecos_last_scrape_news", now.toString())
        setLastSync(now)
      } else if (response.status === "cooldown") {
        // Cooldown active: fake some activity to give "effect" as requested, then refresh
        await new Promise(resolve => setTimeout(resolve, 1500))
        const lastRun = new Date(response.last_run).getTime()
        localStorage.setItem("ecos_last_scrape_news", lastRun.toString())
        setLastSync(lastRun)
      }
      
      await mutate()
    } catch (err) {
      console.error("Error triggering scrape:", err)
    } finally {
      setIsSyncing(false)
    }
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-10 max-w-6xl min-h-screen">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-10 gap-4 border-b border-(--color-border-strong) pb-6">
        <div>
          <p className="font-display text-xs uppercase tracking-[0.2em] text-(--color-tertiary) mb-2 font-semibold">Dashboard 4</p>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-(--color-primary) flex items-center gap-3">
            <Newspaper className="text-(--color-tertiary) w-8 h-8 md:w-9 md:h-9" />
            Monitor de Noticias
          </h1>
          <p className="text-(--color-secondary) mt-2 max-w-2xl text-base">
            Feed de menciones epidemiológicas en medios colombianos. 
            El pipeline NLP clasifica cada artículo por enfermedad detectada.
          </p>
        </div>
        <div className="flex flex-col items-end gap-3">
          <Badge variant="outline" className="bg-(--color-surface) flex items-center gap-1.5">
            <Radio className="w-3 h-3" />
            8 fuentes activas
          </Badge>
          <div className="flex flex-col items-end gap-1">
            <button
              onClick={handleSync}
              disabled={isSyncing}
              className="inline-flex items-center gap-2 px-3 py-1.5 bg-(--color-surface) border border-(--color-border) rounded-md text-xs font-semibold text-(--color-primary) hover:border-(--color-border-strong) hover:bg-gray-50 transition-all disabled:opacity-50"
            >
              <RefreshCcw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin text-(--color-tertiary)" : "text-(--color-secondary)"}`} />
              {isSyncing ? "Extrayendo noticias..." : "Sincronizar Scraping"}
            </button>
            {lastSync && (
              <p className="text-[9px] text-(--color-muted) font-display uppercase tracking-wider">
                Última act: {new Date(lastSync).toLocaleDateString("es-CO", { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* News Feed */}
        <div className="lg:col-span-3 space-y-4">
          {isLoading && (
            <div className="space-y-4">
              {[1, 2, 3, 4].map(i => (
                <Skeleton key={i} className="h-40 bg-(--color-surface) border border-(--color-border)" />
              ))}
            </div>
          )}
          
          {error && (
            <div className="flex items-center gap-3 p-5 bg-(--color-danger-alpha) border border-(--color-danger) rounded-md">
              <AlertTriangle className="w-5 h-5 text-(--color-danger) shrink-0" />
              <div>
                <p className="font-bold text-(--color-danger) text-sm">Error de conexión</p>
                <p className="text-sm text-(--color-primary)">No se pudo cargar el feed. Verifica que el backend esté corriendo.</p>
              </div>
            </div>
          )}
          
          {data && data.length === 0 && (
            <div className="text-center py-20 border border-(--color-border) rounded-md bg-(--color-surface)">
              <LottieLoader variant="empty" size={120} className="mx-auto opacity-75 mb-2" />
              <p className="text-(--color-secondary)">No hay noticias epidemiológicas recientes.</p>
              <p className="text-xs text-(--color-muted) mt-1">El pipeline de scraping se ejecuta cada 6 horas.</p>
            </div>
          )}

          {data && data.map((article, i) => (
            <NewsCard key={`${article.title}-${i}`} article={article} />
          ))}
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="sticky top-20 space-y-4">
            {/* NLP Legend */}
            <div className="bg-(--color-surface) border border-(--color-border) rounded-md p-4">
              <h3 className="text-[10px] font-display uppercase tracking-wider text-(--color-muted) font-semibold mb-4">
                Clasificación NLP
              </h3>
              <div className="space-y-3.5">
                {[
                  { color: "bg-(--color-danger)", label: "DENGUE", desc: "Aedes aegypti" },
                  { color: "bg-(--color-warning)", label: "MALARIA", desc: "Plasmodium" },
                  { color: "bg-(--color-tertiary)", label: "ZIKA / CHIKU", desc: "Arbovirus" },
                  { color: "bg-(--color-secondary)", label: "GENERAL", desc: "Sin clasificar" },
                ].map((item, i) => (
                  <div key={i} className="flex items-start gap-2.5">
                    <span className={`w-2 h-2 mt-1.5 rounded-full ${item.color} shrink-0`} />
                    <div>
                      <p className="text-xs font-bold text-(--color-primary)">{item.label}</p>
                      <p className="text-[10px] text-(--color-muted)">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Sources status */}
            <div className="bg-(--color-surface) border border-(--color-border) rounded-md p-4">
              <h3 className="text-[10px] font-display uppercase tracking-wider text-(--color-muted) font-semibold mb-3">
                Fuentes RSS
              </h3>
              <div className="space-y-2">
                {["El Tiempo", "El Heraldo", "El Colombiano", "Caracol Radio", "La Opinión", "RCN", "INS Boletines", "Diario Huila"].map((source, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="text-xs text-(--color-secondary)">{source}</span>
                    <span className="w-1.5 h-1.5 rounded-full bg-(--color-success)" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
