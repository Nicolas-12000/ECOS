import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg' | 'icon'
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', ...props }, ref) => {
    const variants = {
      primary: "bg-primary text-primary-contrast hover:opacity-90",
      secondary: "bg-surface text-foreground border border-border hover:bg-background-soft",
      outline: "bg-transparent border border-border text-foreground hover:bg-background-soft",
      ghost: "bg-transparent text-foreground hover:bg-background-soft",
      danger: "bg-danger text-primary-contrast hover:opacity-90",
    }

    const sizes = {
      sm: "px-3 py-1.5 text-xs",
      md: "px-6 py-3 text-sm font-semibold",
      lg: "px-8 py-4 text-base font-semibold",
      icon: "p-2",
    }

    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center rounded-full transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
