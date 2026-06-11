import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  FileText, FolderOpen, Upload, Image as ImageIcon, FileType, Archive, Search,
} from 'lucide-react'
import { DataTable } from '@/components/ui/DataTable'
import { RowActions } from '@/components/ui/RowActions'
import { PageHeader } from '@/components/ui/PageHeader'
import { StatCard } from '@/components/ui/StatCard'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { useModuleList } from '@/hooks/useModuleList'
import { useProjectsLookup } from '@/hooks/useLookupData'
import { confirmDelete } from '@/hooks/useDeleteEntity'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

type CategoryKey = 'all' | 'legal_contract' | 'permit' | 'engineering_drawing' | 'insurance' | 'other'

function SelectField({ label, value, onChange, options, required }: {
  label: string
  value: string
  onChange: (v: string) => void
  options: { value: string; label: string }[]
  required?: boolean
}) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-slate-700">{label}</label>
      <select className="input-field" value={value} onChange={(e) => onChange(e.target.value)} required={required}>
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  )
}

function formatBytes(bytes?: number) {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function DocumentUploadModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { data: projects = [] } = useProjectsLookup()
  const { data: categories = [] } = useQuery({
    queryKey: ['document-categories'],
    queryFn: async () => (await api.get('/documents/categories')).data as { key: string; name_en: string; name_ar: string }[],
  })
  const [loading, setLoading] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [form, setForm] = useState({
    name: '', name_ar: '', name_en: '', category: 'legal_contract', description: '', project_id: '',
  })

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return
    setLoading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('name', form.name)
      fd.append('category', form.category)
      if (form.name_ar) fd.append('name_ar', form.name_ar)
      if (form.name_en) fd.append('name_en', form.name_en)
      if (form.description) fd.append('description', form.description)
      if (form.project_id) fd.append('project_id', form.project_id)
      await api.post('/documents', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      qc.invalidateQueries({ queryKey: ['documents'] })
      qc.invalidateQueries({ queryKey: ['documents-summary'] })
      onClose()
      setFile(null)
      setForm({ name: '', name_ar: '', name_en: '', category: 'legal_contract', description: '', project_id: '' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('upload_document')}>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">{t('file')}</label>
          <input
            type="file"
            accept=".pdf,image/jpeg,image/png,image/webp,image/gif"
            className="input-field"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            required
          />
          <p className="mt-1 text-xs text-slate-500">{t('document_upload_hint')}</p>
        </div>
        <Input label={t('title')} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        <Input label={t('name_ar')} value={form.name_ar} onChange={(e) => setForm({ ...form, name_ar: e.target.value })} />
        <Input label={t('name_en')} value={form.name_en} onChange={(e) => setForm({ ...form, name_en: e.target.value })} />
        <SelectField
          label={t('category')}
          value={form.category}
          onChange={(v) => setForm({ ...form, category: v })}
          options={(categories.length ? categories : [{ key: 'legal_contract', name_en: 'Legal Contracts', name_ar: '' }]).map((c) => ({
            value: c.key,
            label: c.name_en,
          }))}
        />
        <SelectField
          label={t('project')}
          value={form.project_id}
          onChange={(v) => setForm({ ...form, project_id: v })}
          options={[{ value: '', label: '—' }, ...projects.map((p) => ({ value: String(p.id), label: String(p.name_en) }))]}
        />
        <Input label={t('description')} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={loading} disabled={!file}>{t('upload')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}

export function DocumentsPage() {
  const { t, i18n } = useTranslation()
  const { formatInteger } = useFormatNumber()
  const qc = useQueryClient()
  const [category, setCategory] = useState<CategoryKey>('all')
  const [search, setSearch] = useState('')
  const [uploadOpen, setUploadOpen] = useState(false)

  const queryParams = useMemo(() => {
    const p = new URLSearchParams()
    if (category !== 'all') p.set('category', category)
    if (search.trim()) p.set('search', search.trim())
    return p.toString()
  }, [category, search])

  const { data: docs, isLoading, refetch } = useModuleList<Record<string, unknown>[]>(
    `documents-${category}-${search}`,
    `/documents${queryParams ? `?${queryParams}` : ''}`,
  )
  const rows = Array.isArray(docs) ? docs : []

  const { data: summary } = useQuery({
    queryKey: ['documents-summary'],
    queryFn: async () => (await api.get('/documents/summary')).data,
  })

  const deleteDoc = useMutation({
    mutationFn: (id: number) => api.delete(`/documents/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents'] })
      qc.invalidateQueries({ queryKey: ['documents-summary'] })
    },
  })

  const docName = (row: Record<string, unknown>) => {
    if (i18n.language === 'ar' && row.name_ar) return String(row.name_ar)
    if (row.name_en) return String(row.name_en)
    return String(row.name)
  }

  const categoryLabel = (row: Record<string, unknown>) =>
    i18n.language === 'ar' ? String(row.category_label_ar ?? row.category) : String(row.category_label_en ?? row.category)

  const openDownload = async (id: number, filename: string) => {
    const res = await api.get(`/documents/${id}/download`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = filename || 'document'
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  const categoryTabs: { key: CategoryKey; label: string; icon: typeof FileText }[] = [
    { key: 'all', label: t('all_documents'), icon: FolderOpen },
    { key: 'legal_contract', label: t('legal_contracts'), icon: FileText },
    { key: 'permit', label: t('permits'), icon: FileType },
    { key: 'engineering_drawing', label: t('engineering_drawings'), icon: ImageIcon },
    { key: 'insurance', label: t('insurance_docs'), icon: Archive },
    { key: 'other', label: t('other'), icon: FileText },
  ]

  return (
    <div>
      <PageHeader
        title={t('documents')}
        subtitle={t('documents_about')}
        icon={FolderOpen}
        accentIndex={6}
        actions={
          <Button onClick={() => setUploadOpen(true)}>
            <Upload className="me-2 h-4 w-4" />{t('upload_document')}
          </Button>
        }
      />

      <div className="mb-6 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
        <p className="font-medium text-slate-900">{t('documents_explainer_title')}</p>
        <p className="mt-1">{t('documents_explainer_body')}</p>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title={t('total_documents')} value={formatInteger(summary?.total)} icon={FolderOpen} />
        <StatCard title={t('legal_contracts')} value={formatInteger(summary?.by_category?.legal_contract)} icon={FileText} color="bg-blue-50 text-blue-700" />
        <StatCard title={t('permits')} value={formatInteger(summary?.by_category?.permit)} icon={FileType} color="bg-amber-50 text-amber-700" />
        <StatCard title={t('engineering_drawings')} value={formatInteger(summary?.by_category?.engineering_drawing)} icon={ImageIcon} color="bg-emerald-50 text-emerald-700" />
      </div>

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2">
          {categoryTabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => setCategory(key)}
              className={cn(
                'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium',
                category === key ? 'bg-primary-700 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200',
              )}
            >
              <Icon className="h-4 w-4" />{label}
            </button>
          ))}
        </div>
        <div className="relative max-w-xs">
          <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            className="input-field ps-9"
            placeholder={t('search_documents')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <DataTable
        title={t('document_library')}
        subtitle={t('documents_help')}
        loading={isLoading}
        exportFilename="documents"
        data={rows}
        emptyActionLabel={t('upload_document')}
        onEmptyAction={() => setUploadOpen(true)}
        columns={[
          {
            key: 'type',
            label: t('type'),
            render: (row) => row.is_pdf
              ? <span className="text-red-600">PDF</span>
              : row.is_image
                ? <span className="text-emerald-600">IMG</span>
                : '—',
          },
          { key: 'name', label: t('title'), render: (row) => docName(row) },
          { key: 'category', label: t('category'), render: (row) => categoryLabel(row) },
          { key: 'original_filename', label: t('filename') },
          { key: 'file_size', label: t('size'), render: (row) => formatBytes(row.file_size as number) },
          { key: 'created_at', label: t('date'), render: (row) => String(row.created_at ?? '').slice(0, 10) },
        ]}
        rowActions={(row) => (
          <RowActions
            extra={
              <Button
                variant="secondary"
                className="!px-2 !py-1.5 text-xs"
                onClick={() => openDownload(row.id as number, String(row.original_filename ?? 'document'))}
              >
                {t('download')}
              </Button>
            }
            onDelete={() => confirmDelete(t) && deleteDoc.mutate(row.id as number, { onSuccess: () => refetch() })}
          />
        )}
      />

      <DocumentUploadModal open={uploadOpen} onClose={() => { setUploadOpen(false); refetch() }} />
    </div>
  )
}
