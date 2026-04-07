/**
 * @fileoverview Utility functions for preprocessing Markdown content.
 * These functions were extracted from the main markdown renderer for better separation of concerns.
 * Includes preprocessing for LaTeX and custom "think" tags.
 */
import { flow } from 'es-toolkit/compat'
import { ALLOW_UNSAFE_DATA_SCHEME } from '@/config'

type OutlineNode = {
  children: OutlineNode[]
  text: string
}

const stripMarkdownInlineSyntax = (text: string) => {
  return text
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/(\*\*|__)(.*?)\1/g, '$2')
    .replace(/(\*|_)(.*?)\1/g, '$2')
    .replace(/~~(.*?)~~/g, '$1')
    .replace(/<[^>]+>/g, ' ')
    .replace(/[()[\]{}"]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

const createOutlineNode = (text: string): OutlineNode => ({
  text,
  children: [],
})

const getMindmapRoot = (children: OutlineNode[]) => {
  if (children.length === 1)
    return children[0]

  return {
    text: 'Document',
    children,
  }
}

const renderMindmapNode = (node: OutlineNode, depth: number): string[] => {
  const indentation = '  '.repeat(depth)
  const lines = [`${indentation}${node.text}`]

  node.children.forEach((child) => {
    lines.push(...renderMindmapNode(child, depth + 1))
  })

  return lines
}

export const preprocessLaTeX = (content: string) => {
  if (typeof content !== 'string')
    return content

  const codeBlockRegex = /```[\s\S]*?```/g
  const codeBlocks = content.match(codeBlockRegex) || []
  const escapeReplacement = (str: string) => str.replace(/\$/g, '_TMP_REPLACE_DOLLAR_')
  let processedContent = content.replace(codeBlockRegex, 'CODE_BLOCK_PLACEHOLDER')

  processedContent = flow([
    (str: string) => str.replace(/\\\[(.*?)\\\]/g, (_, equation) => `$$${equation}$$`),
    (str: string) => str.replace(/\\\[([\s\S]*?)\\\]/g, (_, equation) => `$$${equation}$$`),
    (str: string) => str.replace(/\\\((.*?)\\\)/g, (_, equation) => `$$${equation}$$`),
    (str: string) => str.replace(/(^|[^\\])\$(.+?)\$/g, (_, prefix, equation) => `${prefix}$${equation}$`),
  ])(processedContent)

  codeBlocks.forEach((block) => {
    processedContent = processedContent.replace('CODE_BLOCK_PLACEHOLDER', escapeReplacement(block))
  })

  processedContent = processedContent.replace(/_TMP_REPLACE_DOLLAR_/g, '$')

  return processedContent
}

export const preprocessThinkTag = (content: string) => {
  const thinkOpenTagRegex = /(<think>\s*)+/g
  const thinkCloseTagRegex = /(\s*<\/think>)+/g
  return flow([
    (str: string) => str.replace(thinkOpenTagRegex, '<details data-think=true>\n'),
    (str: string) => str.replace(thinkCloseTagRegex, '\n[ENDTHINKFLAG]</details>'),
    (str: string) => str.replace(/(<\/details>)(?![^\S\r\n]*[\r\n])(?![^\S\r\n]*$)/g, '$1\n'),
  ])(content)
}

export const markdownToMermaidMindmap = (content: string): string | null => {
  if (typeof content !== 'string' || !content.trim())
    return null

  const root = createOutlineNode('Document')
  const headingStack: OutlineNode[] = [root]
  let currentHeadingNode: OutlineNode = root
  const listStack: Array<{ indent: number, node: OutlineNode }> = []
  let inCodeBlock = false

  content.split('\n').forEach((rawLine) => {
    const trimmedLine = rawLine.trim()

    if (trimmedLine.startsWith('```')) {
      inCodeBlock = !inCodeBlock
      return
    }

    if (inCodeBlock || !trimmedLine || trimmedLine.startsWith('>'))
      return

    const headingMatch = /^(#{1,6})\s+(.+?)\s*#*\s*$/.exec(trimmedLine)
    if (headingMatch) {
      const text = stripMarkdownInlineSyntax(headingMatch[2])
      if (!text)
        return

      const level = headingMatch[1].length
      while (headingStack.length > level)
        headingStack.pop()

      const parent = headingStack[headingStack.length - 1] || root
      const node = createOutlineNode(text)
      parent.children.push(node)
      headingStack[level] = node
      headingStack.length = level + 1
      currentHeadingNode = node
      listStack.length = 0
      return
    }

    const listMatch = /^(\s*)([-*+]|\d+\.)\s+(.+)$/.exec(rawLine)
    if (!listMatch)
      return

    const text = stripMarkdownInlineSyntax(listMatch[3])
    if (!text)
      return

    const indent = listMatch[1].replace(/\t/g, '  ').length
    while (listStack.length && listStack[listStack.length - 1].indent >= indent)
      listStack.pop()

    const parent = listStack[listStack.length - 1]?.node || currentHeadingNode
    const node = createOutlineNode(text)
    parent.children.push(node)
    listStack.push({ indent, node })
  })

  if (!root.children.length)
    return null

  const mindmapRoot = getMindmapRoot(root.children)
  return [
    'mindmap',
    `  root((${mindmapRoot.text}))`,
    ...mindmapRoot.children.flatMap(child => renderMindmapNode(child, 2)),
  ].join('\n')
}

/**
 * Transforms a URI for use in react-markdown, ensuring security and compatibility.
 * This function is designed to work with react-markdown v9+ which has stricter
 * default URL handling.
 *
 * Behavior:
 * 1. Always allows the custom 'abbr:' protocol.
 * 2. Always allows page-local fragments (e.g., "#some-id").
 * 3. Always allows protocol-relative URLs (e.g., "//example.com/path").
 * 4. Always allows purely relative paths (e.g., "path/to/file", "/abs/path").
 * 5. Allows absolute URLs if their scheme is in a permitted list (case-insensitive):
 *    'http:', 'https:', 'mailto:', 'xmpp:', 'irc:', 'ircs:'.
 * 6. Intelligently distinguishes colons used for schemes from colons within
 *    paths, query parameters, or fragments of relative-like URLs.
 * 7. Returns the original URI if allowed, otherwise returns `undefined` to
 *    signal that the URI should be removed/disallowed by react-markdown.
 */
export const customUrlTransform = (uri: string): string | undefined => {
  const PERMITTED_SCHEME_REGEX = /^(https?|ircs?|mailto|xmpp|abbr):$/i

  if (uri.startsWith('#'))
    return uri

  if (uri.startsWith('//'))
    return uri

  const colonIndex = uri.indexOf(':')

  if (colonIndex === -1)
    return uri

  const slashIndex = uri.indexOf('/')
  const questionMarkIndex = uri.indexOf('?')
  const hashIndex = uri.indexOf('#')

  if (
    (slashIndex !== -1 && colonIndex > slashIndex)
    || (questionMarkIndex !== -1 && colonIndex > questionMarkIndex)
    || (hashIndex !== -1 && colonIndex > hashIndex)
  ) {
    return uri
  }

  const scheme = uri.substring(0, colonIndex + 1).toLowerCase()
  if (PERMITTED_SCHEME_REGEX.test(scheme))
    return uri

  if (ALLOW_UNSAFE_DATA_SCHEME && scheme === 'data:')
    return uri

  return undefined
}
