import { NextRequest } from 'next/server'
import fs from 'fs'
import path from 'path'

const VAULT_PATH = process.env.OBSIDIAN_VAULT_PATH || 'C:/Users/sasha/Documents/Obsidian/LifeBook'
const VAULT_ROOT = path.resolve(VAULT_PATH)

// Allowlist: only image types are ever served from the vault.
const MIME_TYPES: Record<string, string> = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.svg': 'image/svg+xml',
}

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const { path: pathSegments } = await params
    const requested = pathSegments.join('/')

    // Resolve to absolute and confirm it stays inside the vault root.
    // path.resolve handles .., absolute segments, and mixed separators —
    // string-level `.includes('..')` checks miss win32 `C:\` re-rooting.
    const fullPath = path.resolve(VAULT_ROOT, requested)
    const rel = path.relative(VAULT_ROOT, fullPath)
    if (rel.startsWith('..') || path.isAbsolute(rel)) {
      return new Response('Forbidden', { status: 403 })
    }

    // Extension allowlist BEFORE touching the filesystem.
    const ext = path.extname(fullPath).toLowerCase()
    const contentType = MIME_TYPES[ext]
    if (!contentType) {
      return new Response('Unsupported media type', { status: 415 })
    }

    if (!fs.existsSync(fullPath) || !fs.statSync(fullPath).isFile()) {
      return new Response('Not Found', { status: 404 })
    }

    const buffer = fs.readFileSync(fullPath)

    // SVG can carry inline scripts — never let the browser execute it inline.
    const headers: Record<string, string> = {
      'Content-Type': contentType,
      'Cache-Control': 'public, max-age=3600',
      'X-Content-Type-Options': 'nosniff',
    }
    if (ext === '.svg') {
      headers['Content-Security-Policy'] = "default-src 'none'; style-src 'unsafe-inline'; sandbox"
      headers['Content-Disposition'] = 'inline'
    }

    return new Response(buffer, { headers })
  } catch (err) {
    console.error('[vault-image]', err)
    return new Response('Error loading image', { status: 500 })
  }
}
