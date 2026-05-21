import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-sm border px-2 py-0.5 font-display text-[0.75rem] uppercase tracking-wide transition-colors focus:outline-none focus:ring-2 focus:ring-(--color-tertiary) focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-(--color-primary) text-white",
        secondary:
          "border-(--color-border) bg-transparent text-(--color-secondary)",
        destructive:
          "border-transparent bg-(--color-danger-alpha) text-(--color-danger)",
        outline: "text-(--color-secondary) border-(--color-border-strong)",
        success: "border-transparent bg-(--color-success-alpha) text-(--color-success)",
        warning: "border-transparent bg-(--color-warning-alpha) text-(--color-warning)",
        tertiary: "border-transparent bg-(--color-tertiary-alpha) text-(--color-tertiary)",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
