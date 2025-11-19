import { cn } from '@/lib/utils'
import { useEffect, useState, memo } from 'react'
import { codeToHtml } from 'shiki'
import { CheckIcon, CopyIcon } from 'lucide-react'

interface CodeBlockProps {
  language?: string
  value: string
  inline?: boolean
  className?: string
}

/**
 * CodeBlock - Renders code with professional syntax highlighting
 * Uses Shiki for beautiful, accurate syntax highlighting
 * Simplified version without full UI component dependencies
 */
export const CodeBlock = memo(function CodeBlock({ language, value, inline, className }: CodeBlockProps) {
  const [highlightedHtml, setHighlightedHtml] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  // Determine if we're in dark mode
  const isDarkMode =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-color-scheme: dark)').matches

  // Inline code (backticks) - pixel-perfect for Geist Mono
  if (inline) {
    return (
      <code
        className={cn(
          'rounded-md bg-muted/60 px-[6px] py-[3px] font-mono text-[13.5px] text-foreground border border-border/30 tracking-tight',
          className
        )}
      >
        {value}
      </code>
    )
  }

  // Syntax highlight block code using Shiki
  useEffect(() => {
    async function highlight() {
      if (!value) {
        setHighlightedHtml('<pre><code></code></pre>')
        return
      }

      const codeTheme = isDarkMode ? 'github-dark' : 'github-light'

      try {
        const html = await codeToHtml(value, {
          lang: language || 'plaintext',
          theme: codeTheme,
        })
        setHighlightedHtml(html)
      } catch (error) {
        // Fallback to plaintext if language is not supported
        const html = await codeToHtml(value, {
          lang: 'plaintext',
          theme: codeTheme,
        })
        setHighlightedHtml(html)
      }
    }
    highlight()
  }, [value, language, isDarkMode])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }

  // Block code (triple backticks) - professional styling with Geist Mono
  return (
    <div className="group relative my-2 rounded-xl border border-border/50 bg-card overflow-hidden shadow-sm">
      {/* Header with language badge and copy button */}
      <div className="flex items-center justify-between border-b border-border/30 bg-muted/30 px-4 py-1">
        {language && (
          <span className="text-[11px] font-medium text-muted-foreground/80 uppercase tracking-[0.08em]">
            {language}
          </span>
        )}
        <button
          onClick={handleCopy}
          className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity duration-150 p-1.5 hover:bg-muted/50 rounded"
          aria-label="Copy code"
        >
          {copied ? (
            <CheckIcon className="size-4 text-green-500" />
          ) : (
            <CopyIcon className="size-4 text-muted-foreground" />
          )}
        </button>
      </div>

      {/* Code content with syntax highlighting */}
      <div className="overflow-x-auto">
        {highlightedHtml ? (
          <div
            className="[&>pre]:p-4 [&>pre]:m-0 [&>pre]:bg-transparent [&>pre]:leading-[1.6] text-[13.5px]"
            dangerouslySetInnerHTML={{ __html: highlightedHtml }}
          />
        ) : (
          <pre className="p-4 m-0 bg-transparent leading-[1.6]">
            <code className={cn('font-mono text-[13.5px]', className)}>{value}</code>
          </pre>
        )}
      </div>
    </div>
  )
})
