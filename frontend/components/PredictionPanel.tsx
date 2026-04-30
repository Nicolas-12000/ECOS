"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Search, Activity, AlertTriangle, CheckCircle, ChevronRight, Loader2 } from "lucide-react"
import { Button } from "./ui/Button"
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "./ui/Card"
import { Badge } from "./ui/Badge"
import { predict, PredictResponse } from "@/lib/api"
import { cn } from "@/lib/utils"

const DISEASES = [
  { id: 'dengue', name: 'Dengue' },
  { id: 'malaria', name: 'Malaria' },
  { id: 'zika', name: 'Zika' },
  { id: 'chikungunya', name: 'Chikungunya' }
]

export function PredictionPanel() {
  const [disease, setDisease] = React.useState('dengue')
  const [municipio, setMunicipio] = React.useState('05001') // Medellín default
  const [loading, setLoading] = React.useState(false)
  const [result, setResult] = React.useState<PredictResponse | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  const handlePredict = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await predict(municipio, disease)
      setResult(data)
    } catch (err: any) {
      setError(err.message || "Error al obtener predicción")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-center gap-2 text-accent mb-2">
          <Activity size={18} />
          <span className="text-xs font-bold uppercase tracking-widest">Motor de Inferencia</span>
        </div>
        <CardTitle>Generador de Predicciones</CardTitle>
        <CardDescription>Horizonte de 4 semanas basado en ML</CardDescription>
      </CardHeader>
      
      <CardContent className="flex-1 space-y-6">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-2">
            {DISEASES.map((d) => (
              <button
                key={d.id}
                onClick={() => setDisease(d.id)}
                className={cn(
                  "px-3 py-2 text-xs font-medium rounded-xl border transition-all",
                  disease === d.id 
                    ? "bg-primary text-primary-contrast border-primary shadow-md" 
                    : "bg-background-soft border-border text-foreground-muted hover:border-accent/30"
                )}
              >
                {d.name}
              </button>
            ))}
          </div>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted" />
            <input
              type="text"
              value={municipio}
              onChange={(e) => setMunicipio(e.target.value)}
              placeholder="Código municipio (e.g. 05001)"
              className="w-full bg-background-soft border-border border rounded-xl py-2 pl-10 pr-4 text-sm focus:ring-1 focus:ring-accent outline-none"
            />
          </div>

          <Button 
            className="w-full shadow-lg shadow-primary/10" 
            onClick={handlePredict}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Activity className="mr-2 h-4 w-4" />
            )}
            Calcular Riesgo
          </Button>
        </div>

        <AnimatePresence mode="wait">
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="p-4 rounded-2xl bg-danger/10 border border-danger/20 text-danger text-xs flex items-start gap-2"
            >
              <AlertTriangle size={14} className="shrink-0 mt-0.5" />
              <p>{error}</p>
            </motion.div>
          )}

          {result && !loading && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="space-y-4"
            >
              <div className="flex items-center justify-between border-b border-border/50 pb-2">
                <span className="text-xs font-bold text-foreground-muted uppercase">Proyección</span>
                <Badge variant={result.predictions.some(p => p.outbreak_flag) ? "danger" : "signal"}>
                  {result.predictions.some(p => p.outbreak_flag) ? "Alerta Activa" : "Riesgo Bajo"}
                </Badge>
              </div>

              <div className="space-y-2">
                {result.predictions.map((p, i) => (
                  <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-background-soft/50 group hover:bg-background-soft transition-colors">
                    <div className="flex flex-col">
                      <span className="text-[10px] text-foreground-muted uppercase font-bold">Semana {p.epi_week}</span>
                      <span className="text-xs font-medium">{new Date(p.week_start_date).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={cn(
                        "text-sm font-bold",
                        p.outbreak_flag ? "text-danger" : "text-foreground"
                      )}>
                        {Math.round(p.predicted_cases)} casos
                      </span>
                      {p.outbreak_flag ? (
                        <AlertTriangle size={14} className="text-danger" />
                      ) : (
                        <CheckCircle size={14} className="text-signal" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  )
}
