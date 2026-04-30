import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'signal' | 'warning' | 'danger' | 'accent' | 'outline'
}

function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  const variants = {
    default: "bg-surface text-foreground border border-border",
    signal: "bg-signal text-primary-contrast border-none",
    warning: "bg-warning text-primary-contrast border-none",
    danger: "bg-danger text-primary-contrast border-none",
    accent: "bg-accent-soft text-primary border-none",
    outline: "bg-transparent border border-border text-foreground",
  }

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider transition-colors",
        variants[variant],
        className
      )}
      {...props}
    />
  )
}

export { Badge }
