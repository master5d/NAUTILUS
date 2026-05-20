'use client'

import ReactMarkdown from 'react-markdown'
import { KnowledgeNode } from '@/types/knowledge'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Badge } from '@/components/ui/badge'

interface NodeViewerProps {
  node: KnowledgeNode | null
  onClose: () => void
}

const SOURCE_LABELS: Record<string, string> = {
  file: 'File',
  url: 'URL',
  readwise: 'Readwise',
  highlight: 'Highlight',
  obsidian: 'Obsidian',
}

export function NodeViewer({ node, onClose }: NodeViewerProps) {
  return (
    <Sheet open={!!node} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-[400px] sm:w-[540px] bg-background border-zinc-800 text-foreground">
        <SheetHeader className="pr-8">
          <SheetTitle className="text-foreground text-base font-mono leading-snug">
            {node?.title ?? 'Node'}
          </SheetTitle>
        </SheetHeader>

        {node && (
          <div className="px-4 pb-4 space-y-4 overflow-y-auto max-h-[calc(100vh-120px)]">
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline" className="border-zinc-700 text-muted-foreground text-xs">
                {SOURCE_LABELS[node.source] ?? node.source}
              </Badge>
              {node.cluster && (
                <Badge
                  variant="outline"
                  className="border-zinc-700 text-xs"
                  style={{ color: node.color }}
                >
                  {node.cluster}
                </Badge>
              )}
              {node.type === 'Cluster' && (
                <Badge className="bg-zinc-800 text-zinc-300 text-xs">Cluster</Badge>
              )}
            </div>

            {node.url && (
              <div>
                <p className="text-xs text-muted-foreground mb-1 font-mono uppercase tracking-wider">URL</p>
                <a
                  href={node.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-indigo-400 hover:text-indigo-300 break-all"
                >
                  {node.url}
                </a>
              </div>
            )}

            {node.content && (
              <div>
                <p className="text-xs text-muted-foreground mb-1 font-mono uppercase tracking-wider">
                  Content
                </p>
                <div className="prose prose-sm prose-invert max-w-none text-zinc-300 [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
                  <ReactMarkdown
                    components={{
                      img: ({ src, alt }) => {
                        const srcStr = typeof src === 'string' ? src : ''
                        // Remote images render normally
                        if (srcStr.startsWith('http')) {
                          return <img src={srcStr} alt={alt} className="max-w-full rounded" />
                        }
                        // Local vault images can't be served — show a placeholder
                        return (
                          <span className="inline-flex items-center gap-1 text-xs text-muted-foreground font-mono bg-zinc-800 px-2 py-0.5 rounded">
                            ▪ {alt || srcStr || 'image'}
                          </span>
                        )
                      },
                    }}
                  >
                    {node.content}
                  </ReactMarkdown>
                </div>
              </div>
            )}

            {node.tags?.length && (
              <div>
                <p className="text-xs text-muted-foreground mb-1 font-mono uppercase tracking-wider">Tags</p>
                <div className="flex gap-1 flex-wrap">
                  {node.tags.map((t) => (
                    <Badge key={t} variant="secondary" className="text-xs bg-zinc-800 text-zinc-400">
                      #{t}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </SheetContent>
    </Sheet>
  )
}
