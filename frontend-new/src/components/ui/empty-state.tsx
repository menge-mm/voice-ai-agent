import { Activity } from 'react'
import type { LucideIcon } from 'lucide-react'
import { InboxIcon } from 'lucide-react'

type EmptyStateProps = {
  icon?: LucideIcon
  title: string
  description?: string
  action?: React.ReactNode
  children?: React.ReactNode
}

/**
 * EmptyState - A reusable component for displaying empty states
 * Shows an icon, title, description, and optional action
 * Uses React 19's Activity component to mark as low-priority rendering
 */
export function EmptyState({
  icon: Icon = InboxIcon,
  title,
  description,
  action,
  children,
}: EmptyStateProps) {
  return (
    <Activity mode="visible">
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <Icon className="size-12 text-muted-foreground mb-4" aria-hidden="true" />
        <h3 className="text-lg font-semibold mb-2">{title}</h3>
        {description && (
          <p className="text-sm text-muted-foreground mb-4 max-w-md">
            {description}
          </p>
        )}
        {action && <div className="mt-4">{action}</div>}
        {children}
      </div>
    </Activity>
  )
}
