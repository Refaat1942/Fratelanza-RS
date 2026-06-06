export function telLink(mobile: string): string {
  return `tel:${mobile.replace(/\s/g, '')}`
}

export function whatsappLink(mobile: string): string {
  const digits = mobile.replace(/\D/g, '')
  const normalized = digits.startsWith('20') ? digits : `20${digits.replace(/^0/, '')}`
  return `https://wa.me/${normalized}`
}
