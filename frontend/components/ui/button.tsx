import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  // Base styles - neobrutalist
  "inline-flex items-center justify-center gap-2 whitespace-nowrap font-display font-bold uppercase tracking-wide text-sm transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neo-blue focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        // Primary - Blue with black shadow
        default:
          "bg-neo-blue text-white border-neo border-neo-black shadow-neo hover:shadow-neo-hover hover:-translate-x-0.5 hover:-translate-y-0.5 active:translate-x-0.5 active:translate-y-0.5 active:shadow-neo-active",
        // Destructive - Red with black shadow
        destructive:
          "bg-neo-error text-white border-neo border-neo-black shadow-neo hover:shadow-neo-hover hover:-translate-x-0.5 hover:-translate-y-0.5 active:translate-x-0.5 active:translate-y-0.5 active:shadow-neo-active",
        // Outline - White with black shadow
        outline:
          "bg-white text-neo-black border-neo border-neo-black shadow-neo hover:bg-neo-blue-light hover:shadow-neo-hover hover:-translate-x-0.5 hover:-translate-y-0.5 active:translate-x-0.5 active:translate-y-0.5 active:shadow-neo-active",
        // Secondary - Light grey with shadow
        secondary:
          "bg-neo-lightgrey text-neo-black border-neo border-neo-black shadow-neo hover:bg-neo-offwhite hover:shadow-neo-hover hover:-translate-x-0.5 hover:-translate-y-0.5 active:translate-x-0.5 active:translate-y-0.5 active:shadow-neo-active",
        // Ghost - No shadow, minimal
        ghost:
          "bg-transparent text-neo-black border-neo border-transparent hover:border-neo-black hover:bg-neo-lightgrey",
        // Link - Underline style
        link:
          "bg-transparent text-neo-blue border-none shadow-none underline-offset-4 hover:underline p-0 h-auto",
      },
      size: {
        default: "h-11 px-6 py-2",
        sm: "h-9 px-4 text-xs",
        lg: "h-14 px-8 text-base",
        icon: "h-11 w-11 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
