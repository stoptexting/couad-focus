import * as React from "react"

import { cn } from "@/lib/utils"

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-11 w-full bg-white px-4 py-2 font-mono text-sm",
          "border-neo border-neo-black shadow-neo-sm",
          "transition-all duration-150",
          "placeholder:text-neo-grey",
          "focus:outline-none focus:shadow-neo-blue focus:border-neo-blue",
          "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-neo-lightgrey",
          "file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
