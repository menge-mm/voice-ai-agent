import { useState } from 'react'
import { ChevronRightIcon, BrainCircuitIcon } from 'lucide-react'
import { ThinkingTree } from './ThinkingTree'
import { cn } from '@/lib/utils'
import type { ThinkingNode } from '@/types'

interface ThinkingBlockProps {
  nodes: ThinkingNode[]
  className?: string
  defaultExpanded?: boolean
}

/**
 * ThinkingBlock - Professional collapsible section displaying AI thinking process
 * Features smooth expand/collapse animations, professional design, and accessibility
 */
export function ThinkingBlock({ nodes, className, defaultExpanded = false }: ThinkingBlockProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  if (!nodes || nodes.length === 0) {
    return null
  }

  return (
    <div
      className={cn(
        'rounded-xl border border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10',
        'overflow-hidden shadow-sm',
        'transition-all duration-200',
        className
      )}
    >
      {/* Header - clickable to expand/collapse */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "w-full flex items-center gap-2.5 px-4 py-3",
          "hover:bg-primary/10 active:bg-primary/15",
          "transition-colors duration-150 ease-out",
          "focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
        )}
        aria-expanded={isExpanded}
        aria-controls="thinking-content"
      >
        {/* Chevron icon with rotation animation */}
        <ChevronRightIcon
          className={cn(
            "size-4 text-muted-foreground",
            "transition-transform duration-250 ease-out",
            isExpanded && "rotate-90"
          )}
          aria-hidden="true"
        />

        {/* Brain icon */}
        <BrainCircuitIcon
          className="size-4 text-primary"
          aria-hidden="true"
        />

        {/* Text labels */}
        <span className="text-sm font-medium text-foreground">
          Thinking Process
        </span>
        <span className={cn(
          "text-xs font-medium transition-colors",
          isExpanded ? "text-primary" : "text-muted-foreground"
        )}>
          {nodes.length} {nodes.length === 1 ? 'step' : 'steps'}
        </span>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Expand/collapse hint */}
        <span className="text-xs text-muted-foreground/70">
          {isExpanded ? 'Collapse' : 'Expand'}
        </span>
      </button>

      {/* Content with smooth slide and fade animation */}
      <div
        className={cn(
          "grid transition-all duration-250 ease-out",
          isExpanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
        )}
      >
        <div className="overflow-hidden">
          {isExpanded && (
            <div
              id="thinking-content"
              className={cn(
                "px-4 pb-3 border-t border-primary/10",
                "animate-in fade-in slide-in-from-top-2 duration-300"
              )}
            >
              <ThinkingTree nodes={nodes} className="py-2" />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
