import { Card, CardHeader } from '@/components/ui/Card'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import { useTranslation } from 'react-i18next'

interface PipelineChartProps {
  pipeline: Record<string, number>
}

const stageLabels: Record<string, { ar: string; en: string }> = {
  new: { ar: 'جديد', en: 'New' },
  contacted: { ar: 'تم التواصل', en: 'Contacted' },
  interested: { ar: 'مهتم', en: 'Interested' },
  site_visit: { ar: 'زيارة موقع', en: 'Site Visit' },
  negotiation: { ar: 'تفاوض', en: 'Negotiation' },
  reservation: { ar: 'حجز', en: 'Reservation' },
  contract_signed: { ar: 'عقد موقع', en: 'Contract Signed' },
  lost: { ar: 'مفقود', en: 'Lost' },
}

export function PipelineChart({ pipeline }: PipelineChartProps) {
  const { t, i18n } = useTranslation()
  const { formatInteger } = useFormatNumber()
  const max = Math.max(...Object.values(pipeline), 1)

  return (
    <Card>
      <CardHeader title={t('leads')} subtitle={t('overview')} />
      <div className="space-y-3">
        {Object.entries(pipeline).map(([stage, count]) => {
          const label = i18n.language === 'ar' ? stageLabels[stage]?.ar : stageLabels[stage]?.en
          const pct = (count / max) * 100
          return (
            <div key={stage}>
              <div className="mb-1 flex justify-between text-sm">
                <span className="text-slate-600">{label || stage}</span>
                <span className="font-medium text-slate-900">{formatInteger(count)}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                <div className="h-full rounded-full bg-primary-600 transition-all" style={{ width: `${pct}%` }} />
              </div>
            </div>
          )
        })}
      </div>
    </Card>
  )
}
