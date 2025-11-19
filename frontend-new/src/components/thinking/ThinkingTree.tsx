import { useMemo } from 'react'
import { ThinkingNodeItem } from './ThinkingNodeItem'
import type { ThinkingNode } from '@/types'

interface ThinkingTreeProps {
  nodes: ThinkingNode[]
  className?: string
}

/**
 * ThinkingTree - Displays thinking nodes as a hierarchical tree
 * Automatically builds parent-child relationships based on parentId
 */
export function ThinkingTree({ nodes, className }: ThinkingTreeProps) {
  // Build tree structure from flat array of nodes
  const tree = useMemo(() => {
    // Create a map of nodes by ID for quick lookup
    const nodeMap = new Map<string, ThinkingNode & { children: ThinkingNode[] }>()

    // Initialize all nodes with empty children array
    nodes.forEach((node) => {
      nodeMap.set(node.id, { ...node, children: [] })
    })

    // Build parent-child relationships
    const rootNodes: (ThinkingNode & { children: ThinkingNode[] })[] = []

    nodes.forEach((node) => {
      const nodeWithChildren = nodeMap.get(node.id)
      if (!nodeWithChildren) return

      if (!node.parentId || node.parentId === null) {
        // Root node
        rootNodes.push(nodeWithChildren)
      } else {
        // Child node - add to parent's children
        const parent = nodeMap.get(node.parentId)
        if (parent) {
          parent.children.push(nodeWithChildren)
        } else {
          // Parent not found, treat as root
          rootNodes.push(nodeWithChildren)
        }
      }
    })

    // Sort by timestamp to maintain order
    const sortByTimestamp = (a: ThinkingNode, b: ThinkingNode) => {
      const aTime = typeof a.timestamp === 'number' ? a.timestamp : a.timestamp.getTime()
      const bTime = typeof b.timestamp === 'number' ? b.timestamp : b.timestamp.getTime()
      return aTime - bTime
    }

    rootNodes.sort(sortByTimestamp)
    rootNodes.forEach((node) => {
      if (node.children.length > 0) {
        node.children.sort(sortByTimestamp)
      }
    })

    return rootNodes
  }, [nodes])

  if (tree.length === 0) {
    return null
  }

  return (
    <div className={className}>
      {tree.map((node) => (
        <ThinkingNodeItem
          key={node.id}
          node={node}
          depth={0}
          isExpanded={true}
        />
      ))}
    </div>
  )
}
