"use client"

import { motion } from "framer-motion"
import { Badge } from "./ui/Badge"
import { Button } from "./ui/Button"
import { Shield, Activity, Search, MessageSquare } from "lucide-react"

export function DashboardHero() {
  return (
    <div className="relative overflow-hidden py-12 lg:py-20">
      <div className="flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between">
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-3xl"
        >
          <div className="flex items-center gap-2 mb-6">
            <Badge variant="accent" className="py-1.5 px-4">
              Sistema Nacional de Alerta Temprana
            </Badge>
            <div className="flex items-center gap-1 text-signal text-xs font-bold uppercase tracking-widest">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-signal opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-signal"></span>
              </span>
              En vivo
            </div>
          </div>
          
          <h1 className="text-5xl font-bold tracking-tight text-foreground sm:text-7xl lg:leading-[1.1]">
            Vigilancia <span className="text-accent italic font-serif">inteligente</span> para la salud pública.
          </h1>
          
          <p className="mt-8 text-lg leading-relaxed text-foreground-muted max-w-2xl">
            ECOS procesa señales climáticas, epidemiológicas y sociales en tiempo real para anticipar brotes y optimizar la respuesta sanitaria en Colombia.
          </p>

          <div className="mt-10 flex flex-wrap gap-4">
            <Button size="lg" className="shadow-lg shadow-primary/20" onClick={() => window.location.href = '#dashboard'}>
              <Activity className="mr-2 h-5 w-5" />
              Ver Mapa de Riesgo
            </Button>
            <Button variant="secondary" size="lg" onClick={() => window.dispatchEvent(new CustomEvent('open-chat'))}>
              <MessageSquare className="mr-2 h-5 w-5" />
              Consultar Asistente
            </Button>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="grid grid-cols-2 gap-4 lg:w-[400px]"
        >
          {[
            { icon: Search, label: "Análisis", value: "Real-time", sub: "Procesamiento de señales" },
            { icon: MessageSquare, label: "IA", value: "ECOS-LLM", sub: "Asistencia experta" },
          ].map((item, i) => (
            <div key={i} className="bg-surface border border-border p-5 rounded-[32px] shadow-sm hover:shadow-md transition-shadow">
              <item.icon className="h-6 w-6 text-accent mb-3" />
              <div className="text-2xl font-bold text-foreground">{item.value}</div>
              <div className="text-xs font-medium text-foreground-muted uppercase tracking-wider mt-1">{item.label}</div>
              <div className="text-[10px] text-foreground-muted/60 mt-1">{item.sub}</div>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  )
}
