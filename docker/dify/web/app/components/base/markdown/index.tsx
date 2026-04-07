'use client'

import type { ReactMarkdownWrapperProps, SimplePluginInfo } from './react-markdown-wrapper'
import { flow } from 'es-toolkit/compat'
import dynamic from 'next/dynamic'
import { useEffect, useMemo, useState } from 'react'
import ActionButton, { ActionButtonState } from '@/app/components/base/action-button'
import { cn } from '@/utils/classnames'
import { markdownToMermaidMindmap, preprocessLaTeX, preprocessThinkTag } from './markdown-utils'
import 'katex/dist/katex.min.css'

const ReactMarkdown = dynamic(() => import('./react-markdown-wrapper').then(mod => mod.ReactMarkdownWrapper), { ssr: false })
const Flowchart = dynamic(() => import('@/app/components/base/mermaid'), { ssr: false })

/**
 * @fileoverview Main Markdown rendering component.
 * This file was refactored to extract individual block renderers and utility functions
 * into separate modules for better organization and maintainability as of [Date of refactor].
 * Further refactoring candidates (custom block components not fitting general categories)
 * are noted in their respective files if applicable.
 */
export type MarkdownProps = {
  content: string
  className?: string
  pluginInfo?: SimplePluginInfo
} & Pick<ReactMarkdownWrapperProps, 'customComponents' | 'customDisallowedElements' | 'rehypePlugins'>

export const Markdown = (props: MarkdownProps) => {
  const { customComponents = {}, pluginInfo } = props
  const latexContent = flow([
    preprocessThinkTag,
    preprocessLaTeX,
  ])(props.content)
  const mindmapCode = useMemo(() => markdownToMermaidMindmap(props.content), [props.content])
  const [displayMode, setDisplayMode] = useState<'mindmap' | 'markdown'>(mindmapCode ? 'mindmap' : 'markdown')

  useEffect(() => {
    setDisplayMode(mindmapCode ? 'mindmap' : 'markdown')
  }, [mindmapCode])

  return (
    <div className={cn('markdown-body', '!text-text-primary', props.className)}>
      {mindmapCode && (
        <div className="mb-3 flex items-center justify-end gap-2">
          <ActionButton
            size="xs"
            state={displayMode === 'mindmap' ? ActionButtonState.Active : ActionButtonState.Default}
            onClick={() => setDisplayMode('mindmap')}
          >
            Mindmap
          </ActionButton>
          <ActionButton
            size="xs"
            state={displayMode === 'markdown' ? ActionButtonState.Active : ActionButtonState.Default}
            onClick={() => setDisplayMode('markdown')}
          >
            Markdown
          </ActionButton>
        </div>
      )}
      {displayMode === 'mindmap' && mindmapCode
        ? (
            <div className="overflow-x-auto rounded-2xl border border-divider-subtle bg-components-panel-bg p-3">
              <Flowchart PrimitiveCode={mindmapCode} />
            </div>
          )
        : (
            <ReactMarkdown
              pluginInfo={pluginInfo}
              latexContent={latexContent}
              customComponents={customComponents}
              customDisallowedElements={props.customDisallowedElements}
              rehypePlugins={props.rehypePlugins}
            />
          )}
    </div>
  )
}
