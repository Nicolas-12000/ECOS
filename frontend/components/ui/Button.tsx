import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--color-tertiary) focus-visible:ring-offset-2 focus-visible:ring-offset-(--color-background) disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]",
  {
    variants: {
      variant: {
        default:
          "bg-(--color-surface) text-(--color-primary) border border-(--color-border-strong) hover:bg-(--color-surface-hover) hover:border-(--color-secondary) shadow-sm",
        primary:
          "bg-[var(--color-tertiary)] text-white border border-transparent hover:bg-[var(--color-tertiary-hover)] shadow-md hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200",
        ghost:
          "bg-transparent text-[var(--color-primary)] border border-transparent hover:bg-[var(--color-surface-hover)]",
        outline:
          "bg-transparent text-[var(--color-primary)] border border-[var(--color-border-strong)] hover:border-[var(--color-tertiary)] hover:text-[var(--color-tertiary)] hover:bg-[var(--color-tertiary-alpha)] hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200",
        danger:
          "bg-[var(--color-danger-alpha)] text-[var(--color-danger)] border border-[var(--color-danger)] hover:bg-[var(--color-danger)] hover:text-white transition-all duration-200",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-12 px-8 text-base",
        icon: "h-10 w-10",
      },
      shape: {
        default: "rounded-(--radius-sm)",
        md: "rounded-(--radius-md)",
        pill: "rounded-full",
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default",
      shape: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, shape, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, shape, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
