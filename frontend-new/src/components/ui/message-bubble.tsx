import { cn } from '@/lib/utils'
import { MarkdownRenderer } from '@/components/markdown/MarkdownRenderer'
import { FileIcon, FileTextIcon, ImageIcon, FileSpreadsheetIcon, FilmIcon, ChevronLeftIcon, ChevronRightIcon } from 'lucide-react'
import type { MessageAttachment } from '@/types'
import { Button } from '@/components/ui/button'

type MessageBubbleProps = {
  role: 'user' | 'assistant'
  content: string
  timestamp?: Date
  attachments?: MessageAttachment[]
  className?: string
  // Version control for AI messages
  currentVersion?: number
  totalVersions?: number
  onVersionChange?: (index: number) => void
}

/**
 * MessageBubble - Professional chat message bubble with enhanced styling
 * Features improved typography, subtle shadows, and smooth transitions
 */
// Helper function to get file icon based on MIME type
const getFileIcon = (type: string) => {
  if (type.startsWith('image/')) return ImageIcon
  if (type.startsWith('video/')) return FilmIcon
  if (type.includes('spreadsheet') || type.includes('excel')) return FileSpreadsheetIcon
  if (type.includes('pdf') || type.includes('document') || type.includes('text')) return FileTextIcon
  return FileIcon
}

// Helper function to format file size
const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function MessageBubble({
  role,
  content,
  timestamp,
  attachments,
  className,
  currentVersion,
  totalVersions,
  onVersionChange,
}: MessageBubbleProps) {
  const isUser = role === 'user'
  const hasVersions = !isUser && totalVersions && totalVersions > 1

  return (
    <div
      className={cn(
        'rounded-2xl px-4 py-3 space-y-2',
        'transition-all duration-200',
        isUser
          ? 'max-w-xl ml-auto bg-gray-100 dark:bg-blue-500/15 text-foreground shadow-sm'
          : 'w-full bg-muted/50 text-foreground shadow-sm',
        className
      )}
    >
      {/* Attachments - compact inline display */}
      {attachments && attachments.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {attachments.map((attachment) => {
            const Icon = getFileIcon(attachment.type)
            const isImage = attachment.type.startsWith('image/')

            return (
              <div
                key={attachment.id}
                className={cn(
                  "group/attachment relative flex items-center gap-1.5 px-1.5 py-0.5 rounded max-w-[160px]",
                  "transition-colors duration-150",
                  isUser
                    ? "bg-white/40 dark:bg-white/5 hover:bg-white/60 dark:hover:bg-white/10"
                    : "bg-background/40 hover:bg-background/60"
                )}
                title={`${attachment.name} - ${formatFileSize(attachment.size)}`}
              >
                {/* File icon or image thumbnail - square */}
                {isImage && attachment.url ? (
                  <div className="size-4 rounded-sm overflow-hidden bg-muted/30 shrink-0 border border-border/50">
                    <img
                      src={attachment.url}
                      alt={attachment.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                ) : (
                  <div className={cn(
                    "size-4 rounded-sm flex items-center justify-center shrink-0 border",
                    isUser
                      ? "bg-primary/10 border-primary/20"
                      : "bg-muted/50 border-border/50"
                  )}>
                    <Icon className={cn(
                      "size-2.5",
                      isUser ? "text-primary" : "text-muted-foreground"
                    )} />
                  </div>
                )}

                {/* File name - truncated with ellipsis */}
                <span className="text-[11px] font-medium truncate leading-tight">
                  {attachment.name}
                </span>

                {/* File size - visible on hover */}
                <span className={cn(
                  "absolute -top-6 left-1/2 -translate-x-1/2 px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap",
                  "bg-popover text-popover-foreground shadow-md border",
                  "opacity-0 group-hover/attachment:opacity-100 transition-opacity duration-200 pointer-events-none",
                  "z-10"
                )}>
                  {formatFileSize(attachment.size)}
                </span>
              </div>
            )
          })}
        </div>
      )}

      {/* Message content */}
      {isUser ? (
        // User messages: plain text with improved readability
        <div className="text-sm leading-relaxed whitespace-pre-wrap break-words">
          {content}
        </div>
      ) : (
        // Assistant messages: render markdown with consistent typography
        <div
          key={`version-${currentVersion}`}
          className="text-sm leading-relaxed animate-in fade-in slide-in-from-bottom-1 duration-300"
        >
          <MarkdownRenderer content={content} />
        </div>
      )}

      {/* Bottom row: Timestamp (left) and Version selector (right) */}
      <div className={cn(
        'flex items-center justify-between pt-1',
        (timestamp || hasVersions) ? 'opacity-100' : 'opacity-0'
      )}>
        {/* Timestamp */}
        {timestamp && (
          <div
            className={cn(
              'text-xs',
              isUser ? 'text-primary-foreground/60' : 'text-muted-foreground/70'
            )}
          >
            {timestamp.toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </div>
        )}

        {/* Version selector - bottom right for AI messages */}
        {hasVersions && (
          <div className="flex items-center gap-1" role="navigation" aria-label="Response version navigation">
            <Button
              variant="ghost"
              size="icon"
              className="h-5 w-5 hover:bg-muted/50"
              onClick={() => onVersionChange?.((currentVersion ?? 0) - 1)}
              disabled={currentVersion === 0}
              aria-label="Previous version"
            >
              <ChevronLeftIcon className="size-3" />
            </Button>
            <span className="text-[10px] text-muted-foreground font-medium px-1" aria-live="polite" aria-atomic="true">
              Version {(currentVersion ?? 0) + 1} of {totalVersions}
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="h-5 w-5 hover:bg-muted/50"
              onClick={() => onVersionChange?.((currentVersion ?? 0) + 1)}
              disabled={currentVersion === (totalVersions ?? 1) - 1}
              aria-label="Next version"
            >
              <ChevronRightIcon className="size-3" />
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
