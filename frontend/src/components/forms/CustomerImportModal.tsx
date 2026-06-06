import { useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQueryClient } from '@tanstack/react-query'
import { Download, Upload, CheckCircle, AlertTriangle, XCircle, ArrowRight, ArrowLeft } from 'lucide-react'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

type PreviewRow = {
  row_number: number
  status: string
  errors: string[]
  data: Record<string, string>
  existing_id?: number
  existing_name?: string
}

type PreviewResult = {
  session_id: string
  filename: string
  headers: string[]
  available_fields: string[]
  column_mapping: Record<string, string>
  suggestions: { file_column: string; mapped_to: string; confidence: string }[]
  unmapped_columns: string[]
  rows: PreviewRow[]
  summary: { total: number; valid: number; errors: number; duplicates?: number }
}

interface CustomerImportModalProps {
  open: boolean
  onClose: () => void
}

export function CustomerImportModal({ open, onClose }: CustomerImportModalProps) {
  const { t } = useTranslation()
  const { formatInteger } = useFormatNumber()
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [step, setStep] = useState<1 | 2 | 3>(1)
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState<PreviewResult | null>(null)
  const [mapping, setMapping] = useState<Record<string, string>>({})
  const [duplicateStrategy, setDuplicateStrategy] = useState('skip')
  const [createLeads, setCreateLeads] = useState(false)
  const [result, setResult] = useState<{ created: number; updated: number; skipped: number; failed: number } | null>(null)

  const reset = () => {
    setStep(1)
    setPreview(null)
    setMapping({})
    setResult(null)
    setDuplicateStrategy('skip')
    setCreateLeads(false)
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  const downloadTemplate = async (format: 'xlsx' | 'csv') => {
    const res = await api.get(`/customers/import/template?format=${format}`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `customer_import_template.${format}`
    a.click()
    URL.revokeObjectURL(url)
  }

  const uploadFile = async (file: File) => {
    setLoading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      if (Object.keys(mapping).length) {
        fd.append('column_mapping', JSON.stringify(mapping))
      }
      const { data } = await api.post<PreviewResult>('/customers/import/preview', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setPreview(data)
      setMapping(data.column_mapping)
      setStep(2)
    } finally {
      setLoading(false)
    }
  }

  const remapAndRepreview = async (file?: File) => {
    const f = file ?? fileRef.current?.files?.[0]
    if (!f) return
    await uploadFile(f)
  }

  const confirmImport = async () => {
    if (!preview) return
    setLoading(true)
    try {
      const { data } = await api.post('/customers/import/confirm', {
        session_id: preview.session_id,
        rows: preview.rows,
        duplicate_strategy: duplicateStrategy,
        create_leads: createLeads,
      })
      setResult(data)
      setStep(3)
      qc.invalidateQueries({ queryKey: ['customers'] })
    } finally {
      setLoading(false)
    }
  }

  const statusIcon = (status: string) => {
    if (status === 'valid') return <CheckCircle className="h-4 w-4 text-emerald-600" />
    if (status === 'duplicate') return <AlertTriangle className="h-4 w-4 text-amber-600" />
    return <XCircle className="h-4 w-4 text-red-600" />
  }

  return (
    <Modal open={open} onClose={handleClose} title={t('bulk_import_customers')} className="max-w-3xl">
      {step === 1 && (
        <div className="space-y-5">
          <p className="text-sm text-slate-600">{t('bulk_import_help')}</p>
          <div className="rounded-xl border border-dashed border-primary-300 bg-primary-50/50 p-6 text-center">
            <Upload className="mx-auto mb-3 h-10 w-10 text-primary-600" />
            <p className="mb-3 text-sm font-medium text-slate-800">{t('upload_customer_file')}</p>
            <p className="mb-4 text-xs text-slate-500">{t('supported_formats')}</p>
            <input
              ref={fileRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) uploadFile(f)
              }}
            />
            <Button loading={loading} onClick={() => fileRef.current?.click()}>
              {t('choose_file')}
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => downloadTemplate('xlsx')}>
              <Download className="me-2 h-4 w-4" />{t('download_template_xlsx')}
            </Button>
            <Button variant="secondary" onClick={() => downloadTemplate('csv')}>
              <Download className="me-2 h-4 w-4" />{t('download_template_csv')}
            </Button>
          </div>
        </div>
      )}

      {step === 2 && preview && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm text-slate-600">
              <span className="font-medium">{preview.filename}</span> — {formatInteger(preview.summary.total)} {t('rows')}
            </p>
            <div className="flex gap-2 text-xs">
              <span className="rounded-full bg-emerald-50 px-2 py-1 text-emerald-700">{formatInteger(preview.summary.valid)} {t('valid')}</span>
              <span className="rounded-full bg-amber-50 px-2 py-1 text-amber-700">{formatInteger(preview.summary.duplicates)} {t('duplicates')}</span>
              <span className="rounded-full bg-red-50 px-2 py-1 text-red-700">{formatInteger(preview.summary.errors)} {t('errors')}</span>
            </div>
          </div>

          <div>
            <p className="mb-2 text-sm font-medium text-slate-900">{t('column_mapping')}</p>
            <p className="mb-3 text-xs text-slate-500">{t('column_mapping_help')}</p>
            <div className="max-h-40 space-y-2 overflow-y-auto rounded-lg border border-slate-200 p-3">
              {preview.headers.map((header) => (
                <div key={header} className="flex items-center gap-2 text-sm">
                  <span className="w-1/3 truncate font-medium text-slate-700" title={header}>{header}</span>
                  <ArrowRight className="h-3 w-3 shrink-0 text-slate-400" />
                  <select
                    className="input-field flex-1 py-1 text-xs"
                    value={mapping[header] ?? ''}
                    onChange={(e) => {
                      const next = { ...mapping }
                      if (e.target.value) next[header] = e.target.value
                      else delete next[header]
                      setMapping(next)
                    }}
                  >
                    <option value="">{t('ignore_column')}</option>
                    {preview.available_fields.map((f) => (
                      <option key={f} value={f}>{f.replace(/_/g, ' ')}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
            <Button
              variant="secondary"
              className="mt-2"
              onClick={() => remapAndRepreview()}
              disabled={loading}
            >
              {t('apply_mapping')}
            </Button>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium">{t('duplicate_strategy')}</label>
              <select className="input-field" value={duplicateStrategy} onChange={(e) => setDuplicateStrategy(e.target.value)}>
                <option value="skip">{t('duplicate_skip')}</option>
                <option value="update">{t('duplicate_update')}</option>
                <option value="create">{t('duplicate_create')}</option>
              </select>
            </div>
            <label className="flex items-center gap-2 self-end text-sm">
              <input type="checkbox" checked={createLeads} onChange={(e) => setCreateLeads(e.target.checked)} />
              {t('create_leads_on_import')}
            </label>
          </div>

          <div className="max-h-48 overflow-y-auto rounded-lg border border-slate-200">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-slate-50">
                <tr className="text-slate-500">
                  <th className="p-2 text-start">#</th>
                  <th className="p-2 text-start">{t('status')}</th>
                  <th className="p-2 text-start">{t('customers')}</th>
                  <th className="p-2 text-start">Mobile</th>
                  <th className="p-2 text-start">{t('city')}</th>
                </tr>
              </thead>
              <tbody>
                {preview.rows.slice(0, 50).map((r) => (
                  <tr key={r.row_number} className="border-t border-slate-100">
                    <td className="p-2">{formatInteger(r.row_number)}</td>
                    <td className="p-2">
                      <span className={cn('inline-flex items-center gap-1', r.status === 'valid' && 'text-emerald-700', r.status === 'duplicate' && 'text-amber-700', r.status === 'error' && 'text-red-700')}>
                        {statusIcon(r.status)} {r.status}
                      </span>
                    </td>
                    <td className="p-2">{r.data.full_name_en || r.data.full_name_ar || '-'}</td>
                    <td className="p-2">{r.data.mobile || '-'}</td>
                    <td className="p-2">{r.data.city || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {preview.rows.length > 50 && (
              <p className="p-2 text-xs text-slate-500">{t('showing_first_rows', { count: 50, formatParams: { count: { number: 50 } } })}</p>
            )}
          </div>

          <div className="flex gap-3">
            <Button onClick={confirmImport} loading={loading} disabled={preview.summary.valid === 0 && !(preview.summary.duplicates && duplicateStrategy !== 'skip')}>
              {t('import_valid_rows')}
            </Button>
            <Button variant="secondary" onClick={() => setStep(1)}>
              <ArrowLeft className="me-2 h-4 w-4" />{t('back')}
            </Button>
          </div>
        </div>
      )}

      {step === 3 && result && (
        <div className="space-y-4 text-center">
          <CheckCircle className="mx-auto h-12 w-12 text-emerald-600" />
          <h3 className="text-lg font-semibold text-slate-900">{t('import_complete')}</h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-lg bg-emerald-50 p-3">
              <p className="text-2xl font-bold text-emerald-800">{formatInteger(result.created)}</p>
              <p className="text-xs text-emerald-700">{t('created')}</p>
            </div>
            <div className="rounded-lg bg-blue-50 p-3">
              <p className="text-2xl font-bold text-blue-800">{formatInteger(result.updated)}</p>
              <p className="text-xs text-blue-700">{t('updated')}</p>
            </div>
            <div className="rounded-lg bg-amber-50 p-3">
              <p className="text-2xl font-bold text-amber-800">{formatInteger(result.skipped)}</p>
              <p className="text-xs text-amber-700">{t('skipped')}</p>
            </div>
            <div className="rounded-lg bg-red-50 p-3">
              <p className="text-2xl font-bold text-red-800">{formatInteger(result.failed)}</p>
              <p className="text-xs text-red-700">{t('failed')}</p>
            </div>
          </div>
          <Button onClick={handleClose}>{t('done')}</Button>
        </div>
      )}
    </Modal>
  )
}
