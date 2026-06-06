import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Search } from 'lucide-react'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

interface SearchResult {
  id: number
  type: string
  route: string
  name?: string
  mobile?: string
  number?: string
  code?: string
  stage?: string
  project?: string
}

export function GlobalSearch() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (query.length < 2) {
      setResults([])
      return
    }
    const timer = setTimeout(async () => {
      setLoading(true)
      try {
        const { data } = await api.get<Record<string, SearchResult[]>>('/search', { params: { q: query } })
        const flat: SearchResult[] = []
        for (const [group, items] of Object.entries(data)) {
          for (const item of items) {
            flat.push({ ...item, type: item.type || group.slice(0, -1) })
          }
        }
        setResults(flat)
        setOpen(true)
      } finally {
        setLoading(false)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const go = (item: SearchResult) => {
    navigate(item.route)
    setOpen(false)
    setQuery('')
  }

  const label = (item: SearchResult) => {
    if (item.name) return item.name
    if (item.number) return item.number
    if (item.code) return item.code
    return `${item.type} #${item.id}`
  }

  const sub = (item: SearchResult) => {
    const parts = [item.mobile, item.project, item.stage, item.code].filter(Boolean)
    return parts.join(' · ')
  }

  return (
    <div ref={ref} className="relative w-96 max-w-full">
      <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => query.length >= 2 && setOpen(true)}
        placeholder={t('search')}
        className="input-field ps-10"
      />
      {open && query.length >= 2 && (
        <div className="absolute start-0 top-full z-50 mt-1 w-full rounded-xl border border-slate-200 bg-white shadow-lg">
          {loading ? (
            <p className="p-4 text-sm text-slate-500">{t('loading')}</p>
          ) : results.length === 0 ? (
            <p className="p-4 text-sm text-slate-500">{t('no_results')}</p>
          ) : (
            <ul className="max-h-80 overflow-y-auto py-2">
              {results.map((item, i) => (
                <li key={`${item.type}-${item.id}-${i}`}>
                  <button
                    onClick={() => go(item)}
                    className="flex w-full items-start gap-3 px-4 py-2.5 text-start hover:bg-slate-50"
                  >
                    <span className={cn(
                      'mt-0.5 rounded px-1.5 py-0.5 text-xs font-medium capitalize',
                      'bg-primary-50 text-primary-700',
                    )}>
                      {t(`search_type_${item.type}`)}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-slate-900">{label(item)}</p>
                      {sub(item) && <p className="text-xs text-slate-500">{sub(item)}</p>}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
