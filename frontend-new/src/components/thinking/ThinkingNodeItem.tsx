import { useState } from 'react'
import { ChevronRightIcon, ChevronDownIcon, LightbulbIcon, BrainCircuitIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ThinkingNode } from '@/types'

interface ThinkingNodeItemProps {
  node: ThinkingNode & { children?: ThinkingNode[] }
  depth: number
  onToggle?: (nodeId: string) => void
  isExpanded?: boolean
}

// Icon mapping for different thinking types
const THINKING_ICONS = {
  thinking: LightbulbIcon,
  reasoning: BrainCircuitIcon,
}

// Color mapping for different thinking types
const THINKING_COLORS = {
  thinking: 'text-blue-500',
  reasoning: 'text-purple-500',
}

/**
 * ThinkingNodeItem - Displays an individual thinking node
 * Supports expanding/collapsing and shows depth with indentation
 */
export function ThinkingNodeItem({
  node,
  depth,
  onToggle,
  isExpanded = true,
}: ThinkingNodeItemProps) {
  const [localExpanded, setLocalExpanded] = useState(isExpanded)
  const children = node.children || []
  const hasChildren = children.length > 0
  const Icon = THINKING_ICONS[node.type]
  const colorClass = THINKING_COLORS[node.type]

  const handleToggle = () => {
    const newExpanded = !localExpanded
    setLocalExpanded(newExpanded)
    onToggle?.(node.id)
  }

  return (
    <div className="space-y-1">
      {/* Node header */}
      <div
        className={cn(
          'flex items-start gap-2 py-2 px-3 rounded-md hover:bg-muted/50 transition-colors',
          hasChildren && 'cursor-pointer'
        )}
        style={{ paddingLeft: `${depth * 1.5 + 0.75}rem` }}
        onClick={hasChildren ? handleToggle : undefined}
        role={hasChildren ? 'button' : undefined}
        aria-expanded={hasChildren ? localExpanded : undefined}
      >
        {/* Expand/collapse icon */}
        {hasChildren ? (
          localExpanded ? (
            <ChevronDownIcon className="size-4 text-muted-foreground flex-shrink-0 mt-0.5" />
          ) : (
            <ChevronRightIcon className="size-4 text-muted-foreground flex-shrink-0 mt-0.5" />
          )
        ) : (
          <div className="size-4 flex-shrink-0" />
        )}

        {/* Type icon */}
        <Icon className={cn('size-4 flex-shrink-0 mt-0.5', colorClass)} aria-hidden="true" />

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="text-sm text-foreground">{node.content}</div>
          <div className="text-xs text-muted-foreground mt-0.5 capitalize">{node.type}</div>
        </div>
      </div>

      {/* Children */}
      {hasChildren && localExpanded && (
        <div className="space-y-1">
          {children.map((child) => (
            <ThinkingNodeItem
              key={child.id}
              node={child}
              depth={depth + 1}
              onToggle={onToggle}
              isExpanded={isExpanded}
            />
          ))}
        </div>
      )}
    </div>
  )
}
