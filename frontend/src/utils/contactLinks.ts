export function buildWhatsAppUrl(whatsapp?: string | null): string | null {
  if (!whatsapp?.trim()) return null
  const digits = whatsapp.replace(/\D/g, '')
  return digits ? `https://wa.me/${digits}` : null
}

export function buildInstagramUrl(instagram?: string | null): string | null {
  if (!instagram?.trim()) return null
  const raw = instagram.trim()
  if (/^https?:\/\//i.test(raw)) return raw
  const handle = raw.replace(/^@/, '').replace(/\/$/, '')
  return handle ? `https://www.instagram.com/${handle}` : null
}
