import fs from 'fs'
import path from 'path'

export interface ObsidianNote {
  filePath: string
  title: string
  content: string
  cluster: string   // top-level folder name
  tags: string[]
}

// Folders to skip inside the vault
const SKIP_DIRS = new Set(['.obsidian', '.trash', '_templates', 'templates', 'Template', 'Templates'])
// Files to skip
const SKIP_FILES = new Set(['README.md', 'CHANGELOG.md'])

function parseFrontmatter(raw: string): { meta: Record<string, unknown>; body: string } {
  if (!raw.startsWith('---')) return { meta: {}, body: raw }

  const end = raw.indexOf('\n---', 3)
  if (end === -1) return { meta: {}, body: raw }

  const yamlBlock = raw.slice(4, end)
  const body = raw.slice(end + 4).trimStart()

  const meta: Record<string, unknown> = {}
  for (const line of yamlBlock.split('\n')) {
    const colonIdx = line.indexOf(':')
    if (colonIdx === -1) continue
    const key = line.slice(0, colonIdx).trim()
    const val = line.slice(colonIdx + 1).trim()
    if (!key) continue

    // Handle list values: `- item` style (next lines) or inline `[a, b]`
    if (val.startsWith('[') && val.endsWith(']')) {
      meta[key] = val
        .slice(1, -1)
        .split(',')
        .map((s) => s.trim().replace(/^['"]|['"]$/g, ''))
        .filter(Boolean)
    } else if (val) {
      meta[key] = val.replace(/^['"]|['"]$/g, '')
    }
  }

  // Also pick up block-style lists (tags:\n  - foo\n  - bar)
  const blockListRe = /^(\w[\w-]*):\s*\n((?:\s+-\s+.+\n?)+)/gm
  let m: RegExpExecArray | null
  while ((m = blockListRe.exec(yamlBlock)) !== null) {
    const key = m[1]
    const items = m[2]
      .split('\n')
      .map((l) => l.replace(/^\s+-\s*/, '').trim())
      .filter(Boolean)
    if (items.length) meta[key] = items
  }

  return { meta, body }
}

function stripObsidianSyntax(text: string, noteDir?: string, vaultPath?: string): string {
  let result = text
    // [[Page|alias]] → alias, [[Page]] → Page
    .replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, '$2')
    .replace(/\[\[([^\]]+)\]\]/g, '$1')
    // ![[embed]] → remove (Obsidian wikilink embeds)
    .replace(/!\[\[[^\]]*\]\]/g, '')

  // ![alt](local-path) → rewrite to API route or remove
  if (noteDir && vaultPath) {
    const absVault = path.resolve(vaultPath)
    result = result.replace(/!\[([^\]]*)\]\((?!https?:\/\/)?([^)]+)\)/g, (match, alt, imgPath) => {
      // If it's already a URL, keep it
      if (imgPath.startsWith('http')) {
        return match
      }
      // Resolve relative to the note's directory
      const absImgPath = path.resolve(noteDir, imgPath)
      try {
        const relPath = path.relative(absVault, absImgPath)
        if (relPath.includes('..')) return '' // Outside vault, skip
        // Convert backslashes to forward slashes for URL
        const urlPath = relPath.replace(/\\/g, '/')
        return `![${alt}](/api/vault-image/${urlPath})`
      } catch {
        return '' // Error resolving, skip
      }
    })
  } else {
    // No paths provided, remove local images
    result = result.replace(/!\[([^\]]*)\]\((?!https?:\/\/)[^)]*\)/g, '')
  }

  return result
    // ==highlight== → highlight
    .replace(/==([^=]+)==/g, '$1')
    // %%comment%% → remove
    .replace(/%%[\s\S]*?%%/g, '')
    // HTML comments → remove
    .replace(/<!--[\s\S]*?-->/g, '')
    // Dataview blocks → remove
    .replace(/```dataview[\s\S]*?```/g, '')
    // Normalise whitespace
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

function extractTags(meta: Record<string, unknown>, body: string): string[] {
  const tags: string[] = []

  // Frontmatter tags / tag field
  for (const key of ['tags', 'tag']) {
    const v = meta[key]
    if (Array.isArray(v)) tags.push(...v.map(String))
    else if (typeof v === 'string' && v) tags.push(...v.split(/[,\s]+/).filter(Boolean))
  }

  // Inline #hashtags in body
  const inlineRe = /(?:^|\s)#([\w/-]+)/g
  let m: RegExpExecArray | null
  while ((m = inlineRe.exec(body)) !== null) {
    tags.push(m[1])
  }

  // Deduplicate + lowercase
  return [...new Set(tags.map((t) => t.toLowerCase().replace(/^#/, '')))]
}

/**
 * Walk a vault directory and return all parseable notes.
 * cluster = top-level folder name (or 'vault-root' for notes at root)
 */
export function* walkVault(vaultPath: string): Generator<ObsidianNote> {
  const absVault = path.resolve(vaultPath)

  if (!fs.existsSync(absVault)) {
    throw new Error(`Vault path not found: ${absVault}`)
  }

  function* walk(dir: string, cluster: string): Generator<ObsidianNote> {
    let entries: fs.Dirent[]
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true })
    } catch {
      return
    }

    for (const entry of entries) {
      if (entry.name.startsWith('.') && entry.name !== '.obsidian') continue

      if (entry.isDirectory()) {
        if (SKIP_DIRS.has(entry.name)) continue
        // Only the first level below vault root sets the cluster
        const nextCluster = dir === absVault ? entry.name : cluster
        yield* walk(path.join(dir, entry.name), nextCluster)
      } else if (entry.isFile() && entry.name.endsWith('.md')) {
        if (SKIP_FILES.has(entry.name)) continue

        const filePath = path.join(dir, entry.name)
        const raw = fs.readFileSync(filePath, 'utf-8')
        const { meta, body } = parseFrontmatter(raw)

        const noteDir = path.dirname(filePath)
        const content = stripObsidianSyntax(body, noteDir, absVault)
        if (content.length < 30) continue // skip near-empty notes

        const title =
          typeof meta.title === 'string' && meta.title
            ? meta.title
            : entry.name.replace(/\.md$/, '')

        const tags = extractTags(meta, body)

        yield { filePath, title, content, cluster: cluster || 'vault-root', tags }
      }
    }
  }

  yield* walk(absVault, 'vault-root')
}
