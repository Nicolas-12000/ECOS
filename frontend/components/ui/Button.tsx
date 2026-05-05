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
          "bg-(--color-tertiary) text-white border border-transparent hover:bg-(--color-tertiary-hover) shadow-sm hover:shadow-md",
        ghost:
          "bg-transparent text-(--color-primary) border border-transparent hover:bg-(--color-surface-hover)",
        outline:
          "bg-transparent text-(--color-primary) border border-(--color-border-strong) hover:border-(--color-secondary) hover:bg-(--color-surface-hover)",
        danger:
          "bg-(--color-danger-alpha) text-(--color-danger) border border-(--color-danger) hover:bg-(--color-danger) hover:text-white",
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
