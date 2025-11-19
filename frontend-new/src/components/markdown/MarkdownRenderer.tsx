import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import rehypeRaw from 'rehype-raw'
import { CodeBlock } from './CodeBlock'
import { cn } from '@/lib/utils'
import { memo, useMemo } from 'react'
import type { Components } from 'react-markdown'

interface MarkdownRendererProps {
  content: string
  className?: string
}

/**
 * MarkdownRenderer - Renders markdown content with syntax highlighting
 * Supports GitHub Flavored Markdown (tables, task lists, strikethrough, etc.)
 * Provides custom styling for all markdown elements
 * Optimized with memoization to reduce re-renders during streaming
 */
function MarkdownRendererComponent({ content, className }: MarkdownRendererProps) {
  // Helper function to extract text from React children
  const extractText = useMemo(() => (children: any): string => {
    if (typeof children === 'string') {
      return children
    }
    if (Array.isArray(children)) {
      return children.map(extractText).join('')
    }
    if (children && typeof children === 'object') {
      // Handle React elements
      if (children.props && children.props.children) {
        return extractText(children.props.children)
      }
    }
    return ''
  }, [])

  // Custom components for markdown elements - memoized to prevent recreation
  const components: Components = useMemo(() => ({
    // Code blocks and inline code
    code(props: any) {
      const { node, inline, className, children, ...rest } = props
      const match = /language-(\w+)/.exec(className || '')
      const language = match ? match[1] : undefined
      const value = extractText(children).replace(/\n$/, '')

      // Inline code should not have a language class and should be marked as inline
      // Block code has language-* class or is NOT inline
      const isInline = inline !== false && !className

      return (
        <CodeBlock
          language={language}
          value={value}
          inline={isInline}
          className={className}
          {...rest}
        />
      )
    },

    // Headings - pixel-perfect for Geist Sans (8px grid)
    h1: ({ children, ...props }) => (
      <h1 className="text-[26px] font-bold leading-[1.2] tracking-[-0.022em] mb-3 mt-6 first:mt-0" {...props}>
        {children}
      </h1>
    ),
    h2: ({ children, ...props }) => (
      <h2 className="text-[22px] font-bold leading-[1.25] tracking-[-0.019em] mb-3 mt-5 first:mt-0" {...props}>
        {children}
      </h2>
    ),
    h3: ({ children, ...props }) => (
      <h3 className="text-[18px] font-semibold leading-[1.35] tracking-[-0.014em] mb-2 mt-4 first:mt-0" {...props}>
        {children}
      </h3>
    ),
    h4: ({ children, ...props }) => (
      <h4 className="text-[16px] font-semibold leading-[1.4] tracking-[-0.011em] mb-2 mt-3 first:mt-0" {...props}>
        {children}
      </h4>
    ),
    h5: ({ children, ...props }) => (
      <h5 className="text-[14px] font-semibold leading-[1.45] tracking-[-0.006em] mb-2 mt-3 first:mt-0" {...props}>
        {children}
      </h5>
    ),
    h6: ({ children, ...props }) => (
      <h6 className="text-[14px] font-semibold leading-[1.45] tracking-[-0.006em] mb-2 mt-3 first:mt-0 text-muted-foreground/90" {...props}>
        {children}
      </h6>
    ),

    // Paragraphs - optimized for Geist Sans readability
    p: ({ children, ...props }) => (
      <p className="mb-4 last:mb-0 text-[15px] leading-[1.6] tracking-[-0.011em]" {...props}>
        {children}
      </p>
    ),

    // Lists - pixel-perfect spacing (4px increments)
    ul: ({ children, ...props }) => (
      <ul className="list-disc list-outside ml-6 mb-4 space-y-1.5" {...props}>
        {children}
      </ul>
    ),
    ol: ({ children, ...props }) => (
      <ol className="list-decimal list-outside ml-6 mb-4 space-y-1.5" {...props}>
        {children}
      </ol>
    ),
    li: ({ children, ...props }) => (
      <li className="text-[15px] leading-[1.6] tracking-[-0.011em] pl-1" {...props}>
        {children}
      </li>
    ),

    // Links - professional underline with perfect spacing
    a: ({ children, href, ...props }) => (
      <a
        href={href}
        className="text-primary underline decoration-primary/30 underline-offset-[3px] decoration-[0.5px] hover:decoration-primary/90 hover:decoration-[1px] transition-all duration-150"
        target="_blank"
        rel="noopener noreferrer"
        {...props}
      >
        {children}
      </a>
    ),

    // Blockquotes - elegant serif styling with proper spacing
    blockquote: ({ children, ...props }) => (
      <blockquote
        className="border-l-[3px] border-primary/25 pl-4 pr-3 py-2 my-4 text-muted-foreground/95 text-[15px] leading-[1.65] tracking-[-0.008em]"
        {...props}
      >
        {children}
      </blockquote>
    ),

    // Horizontal rule - subtle divider
    hr: (props) => <hr className="my-6 border-t border-border/50" {...props} />,

    // Tables - professional data presentation with pixel-perfect spacing
    table: ({ children, ...props }) => (
      <div className="overflow-x-auto my-4 rounded-xl border border-border/50 shadow-sm">
        <table className="w-full border-collapse" {...props}>
          {children}
        </table>
      </div>
    ),
    thead: ({ children, ...props }) => (
      <thead className="bg-muted/40 border-b border-border/50" {...props}>
        {children}
      </thead>
    ),
    tbody: ({ children, ...props }) => <tbody {...props}>{children}</tbody>,
    tr: ({ children, ...props }) => (
      <tr className="border-b border-border/30 last:border-b-0 hover:bg-muted/20 transition-colors duration-150" {...props}>
        {children}
      </tr>
    ),
    th: ({ children, ...props }) => (
      <th className="px-4 py-3 text-left font-semibold text-[14px] leading-[1.35] tracking-[-0.006em]" {...props}>
        {children}
      </th>
    ),
    td: ({ children, ...props }) => (
      <td className="px-4 py-3 text-[14px] leading-[1.5] tracking-[-0.011em]" {...props}>
        {children}
      </td>
    ),

    // Strong and emphasis - optimized for Geist Sans
    strong: ({ children, ...props }) => (
      <strong className="font-semibold tracking-[-0.014em]" {...props}>
        {children}
      </strong>
    ),
    em: ({ children, ...props }) => (
      <em className="italic" {...props}>
        {children}
      </em>
    ),

    // Task lists (GitHub Flavored Markdown) - pixel-perfect alignment
    input: (props) => (
      <input
        type="checkbox"
        disabled
        className="mr-2 mt-[3px] align-top accent-primary w-4 h-4"
        {...props}
      />
    ),
  }), [extractText])

  return (
    <div className={cn('prose prose-sm max-w-none dark:prose-invert antialiased', className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight, rehypeRaw]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

// Memoize to prevent unnecessary re-renders, but always allow updates when content changes
// Return true to PREVENT re-render, false to ALLOW re-render
export const MarkdownRenderer = memo(MarkdownRendererComponent, (prevProps, nextProps) => {
  // Always re-render if content changed (important for streaming)
  if (prevProps.content !== nextProps.content) return false
  // Prevent re-render only if everything is the same
  return prevProps.className === nextProps.className
})
