import { NextRequest } from 'next/server'
import fs from 'fs'
import path from 'path'

const VAULT_PATH = process.env.OBSIDIAN_VAULT_PATH || 'C:/Users/sasha/Documents/Obsidian/LifeBook'

export async function GET(
  req: NextRequest,
  { params }: { params: { path: string[] } }
) {
  try {
    const filePath = params.path.join('/')
    // Prevent directory traversal
    if (filePath.includes('..')) {
      return new Response('Forbidden', { status: 403 })
    }

    const fullPath = path.join(VAULT_PATH, filePath)

    // Check if file exists
    if (!fs.existsSync(fullPath)) {
      return new Response('Not Found', { status: 404 })
    }

    const buffer = fs.readFileSync(fullPath)
    const ext = path.extname(fullPath).toLowerCase()

    // Map extensions to MIME types
    const mimeTypes: Record<string, string> = {
      '.png': 'image/png',
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.gif': 'image/gif',
      '.webp': 'image/webp',
      '.svg': 'image/svg+xml',
    }

    const contentType = mimeTypes[ext] || 'application/octet-stream'

    return new Response(buffer, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=3600',
      },
    })
  } catch (err) {
    console.error('[vault-image]', err)
    return new Response('Error loading image', { status: 500 })
  }
}
