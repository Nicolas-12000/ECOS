"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { TrendingUp, TrendingDown, Minus, AlertTriangle, CheckCircle2, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface SignalIndicatorProps {
  label: string
  value: string | number
  trend?: 'up' | 'down' | 'stable'
  status?: 'signal' | 'warning' | 'danger' | 'neutral'
  description?: string
  className?: string
}

export function SignalIndicator({
  label,
  value,
  trend,
  status = 'neutral',
  description,
  className
}: SignalIndicatorProps) {
  const statusColors = {
    signal: "text-signal bg-signal/10 border-signal/20",
    warning: "text-warning bg-warning/10 border-warning/20",
    danger: "text-danger bg-danger/10 border-danger/20",
    neutral: "text-foreground-muted bg-foreground-muted/5 border-border",
  }

  const StatusIcon = {
    signal: CheckCircle2,
    warning: AlertTriangle,
    danger: AlertCircle,
    neutral: Minus,
  }[status]

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "flex flex-col gap-1 p-4 rounded-2xl border transition-all hover:shadow-md",
        statusColors[status],
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider opacity-70">
          {label}
        </span>
        <StatusIcon size={16} />
      </div>
      
      <div className="flex items-baseline gap-2 mt-1">
        <span className="text-2xl font-bold tracking-tight">
          {value}
        </span>
        {trend && (
          <span className="flex items-center text-xs font-medium">
            {trend === 'up' && <TrendingUp size={14} className="mr-0.5" />}
            {trend === 'down' && <TrendingDown size={14} className="mr-0.5" />}
            {trend === 'stable' && <Minus size={14} className="mr-0.5" />}
          </span>
        )}
      </div>

      {description && (
        <p className="text-xs mt-1 opacity-80 leading-tight">
          {description}
        </p>
      )}
    </motion.div>
  )
}
