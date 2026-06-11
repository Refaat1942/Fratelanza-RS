import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { RefreshCw, TrendingUp, Plus, Trash2 } from 'lucide-react'
import { Card, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'

interface PricingRule {
  id: number
  project_id: number | null
  name_en: string
  name_ar: string
  trigger_type: string
  threshold_percent: number
  adjustment_percent: number
  is_active: boolean
}

interface PricingPreview {
  sales_volume_percent: number
  construction_progress_percent: number
  sales_adjustment_percent: number
  construction_adjustment_percent: number
  total_adjustment_percent: number
  units_updated?: number
}

interface DynamicPricingPanelProps {
  projectId: number | null
  projectName?: string
}

const EMPTY_RULE = {
  name_en: '',
  name_ar: '',
  trigger_type: 'sales_volume',
  threshold_percent: '10',
  adjustment_percent: '5',
}

export function DynamicPricingPanel({ projectId, projectName }: DynamicPricingPanelProps) {
  const { t, i18n } = useTranslation()
  const { localizeDigits } = useFormatNumber()
  const qc = useQueryClient()
  const [form, setForm] = useState(EMPTY_RULE)

  const { data: rules = [], isLoading } = useQuery({
    queryKey: ['pricing-rules', projectId],
    queryFn: async () => {
      const params = projectId ? `?project_id=${projectId}` : ''
      return (await api.get<PricingRule[]>(`/pricing/rules${params}`)).data
    },
  })

  const { data: preview, refetch: refetchPreview } = useQuery({
    queryKey: ['pricing-preview', projectId],
    queryFn: async () =>
      (await api.get<PricingPreview>(`/pricing/preview?project_id=${projectId}`)).data,
    enabled: !!projectId,
  })

  const createRule = useMutation({
    mutationFn: async () =>
      api.post('/pricing/rules', {
        project_id: projectId,
        name_en: form.name_en,
        name_ar: form.name_ar,
        trigger_type: form.trigger_type,
        threshold_percent: Number(form.threshold_percent),
        adjustment_percent: Number(form.adjustment_percent),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pricing-rules'] })
      refetchPreview()
      setForm(EMPTY_RULE)
    },
  })

  const deleteRule = useMutation({
    mutationFn: async (id: number) => api.delete(`/pricing/rules/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pricing-rules'] })
      refetchPreview()
    },
  })

  const recalculate = useMutation({
    mutationFn: async () =>
      api.post<PricingPreview>(`/pricing/recalculate?project_id=${projectId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['units-board'] })
      qc.invalidateQueries({ queryKey: ['units-lookup'] })
      qc.invalidateQueries({ queryKey: ['pricing-preview'] })
    },
  })

  if (!projectId) {
    return (
      <EmptyState
        title={t('pricing_select_project')}
        description={t('pricing_select_project_help')}
      />
    )
  }

  if (isLoading) return <LoadingState />

  const triggerLabel = (type: string) =>
    type === 'construction_progress' ? t('pricing_trigger_construction') : t('pricing_trigger_sales')

  return (
    <div className="space-y-6">
      <p className="text-sm text-slate-500">{t('pricing_engine_help')}</p>

      {preview && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="!p-4">
            <p className="text-xs text-slate-500">{t('pricing_sales_volume')}</p>
            <p className="text-2xl font-bold text-slate-900">
              {localizeDigits(String(preview.sales_volume_percent))}%
            </p>
            <p className="mt-1 text-sm text-emerald-700">
              +{localizeDigits(String(preview.sales_adjustment_percent))}% {t('pricing_adjustment')}
            </p>
          </Card>
          <Card className="!p-4">
            <p className="text-xs text-slate-500">{t('pricing_construction_progress')}</p>
            <p className="text-2xl font-bold text-slate-900">
              {localizeDigits(String(preview.construction_progress_percent))}%
            </p>
            <p className="mt-1 text-sm text-emerald-700">
              +{localizeDigits(String(preview.construction_adjustment_percent))}% {t('pricing_adjustment')}
            </p>
          </Card>
          <Card className="!p-4 sm:col-span-2">
            <p className="text-xs text-slate-500">{t('pricing_total_adjustment')}</p>
            <p className="flex items-center gap-2 text-2xl font-bold text-primary-800">
              <TrendingUp className="h-6 w-6" />
              +{localizeDigits(String(preview.total_adjustment_percent))}%
            </p>
            <p className="mt-2 text-sm text-slate-600">{t('pricing_total_adjustment_help')}</p>
          </Card>
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <Button onClick={() => recalculate.mutate()} loading={recalculate.isPending}>
          <RefreshCw className="me-2 h-4 w-4" />
          {t('pricing_recalculate')}
        </Button>
        {recalculate.data?.data?.units_updated != null && (
          <span className="self-center text-sm text-slate-600">
            {t('pricing_units_updated', { count: recalculate.data.data.units_updated })}
          </span>
        )}
      </div>

      <Card>
        <CardHeader
          title={t('pricing_rules')}
          subtitle={projectName ? `${t('projects')}: ${projectName}` : undefined}
        />
        {rules.length === 0 ? (
          <EmptyState title={t('pricing_no_rules')} description={t('pricing_no_rules_help')} />
        ) : (
          <ul className="space-y-2">
            {rules.map((rule) => (
              <li
                key={rule.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-100 bg-slate-50/80 px-4 py-3"
              >
                <div>
                  <p className="font-medium text-slate-900">
                    {i18n.language === 'ar' ? rule.name_ar : rule.name_en}
                  </p>
                  <p className="text-sm text-slate-500">
                    {triggerLabel(rule.trigger_type)} ≥ {localizeDigits(String(rule.threshold_percent))}%
                    → +{localizeDigits(String(rule.adjustment_percent))}%
                  </p>
                </div>
                <Button
                  variant="ghost"
                  className="!text-red-600"
                  onClick={() => deleteRule.mutate(rule.id)}
                  loading={deleteRule.isPending}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card>
        <CardHeader title={t('pricing_add_rule')} subtitle={t('pricing_add_rule_help')} />
        <div className="grid gap-4 md:grid-cols-2">
          <Input
            label={t('name_en')}
            value={form.name_en}
            onChange={(e) => setForm({ ...form, name_en: e.target.value })}
          />
          <Input
            label={t('name_ar')}
            value={form.name_ar}
            onChange={(e) => setForm({ ...form, name_ar: e.target.value })}
          />
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">{t('pricing_trigger')}</label>
            <select
              className="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm"
              value={form.trigger_type}
              onChange={(e) => setForm({ ...form, trigger_type: e.target.value })}
            >
              <option value="sales_volume">{t('pricing_trigger_sales')}</option>
              <option value="construction_progress">{t('pricing_trigger_construction')}</option>
            </select>
          </div>
          <Input
            label={t('pricing_threshold')}
            type="number"
            min={0}
            max={100}
            value={form.threshold_percent}
            onChange={(e) => setForm({ ...form, threshold_percent: e.target.value })}
          />
          <Input
            label={t('pricing_adjustment_pct')}
            type="number"
            min={0}
            max={100}
            value={form.adjustment_percent}
            onChange={(e) => setForm({ ...form, adjustment_percent: e.target.value })}
          />
        </div>
        <Button
          className="mt-4"
          onClick={() => createRule.mutate()}
          loading={createRule.isPending}
          disabled={!form.name_en || !form.name_ar}
        >
          <Plus className="me-2 h-4 w-4" />
          {t('pricing_add_rule')}
        </Button>
      </Card>
    </div>
  )
}
