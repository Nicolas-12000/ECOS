"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { Layout, ExternalLink, RefreshCw, AlertCircle } from "lucide-react"
import { Button } from "./ui/Button"
import { Card, CardHeader, CardTitle, CardContent } from "./ui/Card"

interface PowerBIEmbedProps {
  embedUrl?: string
  title?: string
}

export function PowerBIEmbed({ 
  embedUrl, 
  title = "Dashboard Operativo ECOS" 
}: PowerBIEmbedProps) {
  const [isLoading, setIsLoading] = React.useState(true)
  const [hasError, setHasError] = React.useState(false)

  // Default fallback if no URL is provided (for demo purposes)
  const finalUrl = embedUrl || "https://app.powerbi.com/view?r=eyJrIjoiNGJiYzE4YmMtM2EzNy00MDc2LTkwZDctNmM0MzE3Y2U0MTk4IiwidCI6IjhkMzY4MzZlLTZiNzUtNGRlNi1iYWI5LTVmNGIxNzc1NDI3ZiIsImMiOjR9"

  return (
    <Card className="w-full overflow-hidden border-none shadow-xl bg-surface/50 backdrop-blur-md">
      <CardHeader className="flex flex-row items-center justify-between border-b border-border/40 pb-4">
        <div className="flex items-center gap-3">
          <div className="bg-accent/10 p-2 rounded-xl">
            <Layout className="h-5 w-5 text-accent" />
          </div>
          <div>
            <CardTitle className="text-lg font-bold">Análisis Avanzado</CardTitle>
            <p className="text-xs text-foreground-muted">Visualización interactiva de Power BI</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="h-8 text-[10px]" onClick={() => window.open(finalUrl, '_blank')}>
            <ExternalLink className="mr-1 h-3 w-3" />
            Abrir Full
          </Button>
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => { setIsLoading(true); setHasError(false); }}>
            <RefreshCw className={isLoading ? "animate-spin h-3 w-3" : "h-3 w-3"} />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="p-0 relative bg-[#f0f0f0] min-h-[600px] flex items-center justify-center">
        {isLoading && !hasError && (
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-surface/80 backdrop-blur-sm">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="h-10 w-10 border-4 border-accent border-t-transparent rounded-full"
            />
            <p className="mt-4 text-sm font-medium text-foreground-muted">Cargando reporte de Power BI...</p>
          </div>
        )}

        {hasError ? (
          <div className="flex flex-col items-center gap-4 text-center p-12">
            <AlertCircle className="h-12 w-12 text-danger opacity-50" />
            <div>
              <p className="font-bold text-foreground">Error al cargar el dashboard</p>
              <p className="text-sm text-foreground-muted max-w-xs mx-auto mt-1">
                Asegúrate de que el enlace de publicación sea válido y tengas permisos de acceso.
              </p>
            </div>
            <Button variant="primary" size="sm" onClick={() => setHasError(false)}>
              Reintentar
            </Button>
          </div>
        ) : (
          <iframe
            title={title}
            className="w-full h-[600px] border-none shadow-inner"
            src={finalUrl}
            allowFullScreen={true}
            onLoad={() => setIsLoading(false)}
            onError={() => { setIsLoading(false); setHasError(true); }}
          />
        )}
      </CardContent>
    </Card>
  )
}
