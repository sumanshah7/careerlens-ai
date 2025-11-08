import * as React from "react"
import { X } from "lucide-react"
import { cn } from "../../lib/utils"
import { Button } from "./button"

interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: React.ReactNode
}

const Dialog = ({ open, onOpenChange, children }: DialogProps) => {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="fixed inset-0 bg-black/50"
        onClick={() => onOpenChange(false)}
      />
      <div className="relative z-50 w-full max-w-lg max-h-[90vh] overflow-y-auto bg-background rounded-lg shadow-lg p-6">
        <Button
          variant="ghost"
          size="icon"
          className="absolute right-4 top-4"
          onClick={() => onOpenChange(false)}
        >
          <X className="h-4 w-4" />
        </Button>
        {children}
      </div>
    </div>
  )
}

const DialogContent = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={cn("", className)}>{children}</div>
)

const DialogHeader = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={cn("flex flex-col space-y-1.5 text-center sm:text-left mb-4", className)}>
    {children}
  </div>
)

const DialogTitle = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <h2 className={cn("text-lg font-semibold leading-none tracking-tight", className)}>
    {children}
  </h2>
)

const DialogDescription = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <p className={cn("text-sm text-muted-foreground", className)}>
    {children}
  </p>
)

export { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription }

