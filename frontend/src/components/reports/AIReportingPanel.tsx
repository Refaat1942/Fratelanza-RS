import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Bot, Sparkles, TrendingUp, BarChart3, FileText } from 'lucide-react'
import { Card, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { LoadingState } from '@/components/ui/LoadingState'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

interface SummaryResult {
  summary: string
  provider: string
  language: string
  generated_at: string
}

interface AIReportingPanelProps {
  activeReportKey?: string | null
  activeReportName?: string
}

export function AIReportingPanel({ activeReportKey, activeReportName }: AIReportingPanelProps) {
  const { t, i18n } = useTranslation()
  const [activeSummary, setActiveSummary] = useState<SummaryResult | null>(null)
  const [summaryType, setSummaryType] = useState<string | null>(null)

  const language = i18n.language.startsWith('ar') ? 'ar' : 'en'

  const { data: providerInfo } = useQuery({
    queryKey: ['ai-provider'],
    queryFn: async () => (await api.get<{ provider: string }>('/reports/ai/provider')).data,
  })

  const performance = useMutation({
    mutationFn: async () =>
      (await api.post<SummaryResult>('/reports/ai/performance-summary', { language })).data,
    onSuccess: (data) => {
      setActiveSummary(data)
      setSummaryType('performance')
    },
  })

  const trends = useMutation({
    mutationFn: async () =>
      (await api.post<SummaryResult>('/reports/ai/market-trends', { language })).data,
    onSuccess: (data) => {
      setActiveSummary(data)
      setSummaryType('trends')
    },
  })

  const reportAnalysis = useMutation({
    mutationFn: async (reportKey: string) =>
      (await api.post<SummaryResult & { report_key: string }>('/reports/ai/analyze-report', {
        report_key: reportKey,
        language,
      })).data,
    onSuccess: (data) => {
      setActiveSummary(data)
      setSummaryType('report')
    },
  })

  const loading =
    performance.isPending || trends.isPending || reportAnalysis.isPending

  const providerLabel =
    providerInfo?.provider === 'local'
      ? t('ai_provider_local')
      : providerInfo?.provider === 'openai'
        ? 'OpenAI'
        : providerInfo?.provider === 'gemini'
          ? 'Google Gemini'
          : t('ai_provider_local')

  return (
    <Card className="mb-6 border-primary-100 bg-gradient-to-br from-primary-50/80 to-white">
      <CardHeader
        title={t('ai_reporting_title')}
        subtitle={t('ai_reporting_subtitle')}
      />
      <div className="mb-4 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <Bot className="h-4 w-4 text-primary-600" />
        <span>
          {t('ai_provider')}: <strong className="text-slate-700">{providerLabel}</strong>
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button
          variant="secondary"
          loading={performance.isPending}
          onClick={() => performance.mutate()}
        >
          <BarChart3 className="me-2 h-4 w-4" />
          {t('ai_performance_summary')}
        </Button>
        <Button
          variant="secondary"
          loading={trends.isPending}
          onClick={() => trends.mutate()}
        >
          <TrendingUp className="me-2 h-4 w-4" />
          {t('ai_market_trends')}
        </Button>
        {activeReportKey && (
          <Button
            variant="secondary"
            loading={reportAnalysis.isPending}
            onClick={() => reportAnalysis.mutate(activeReportKey)}
          >
            <FileText className="me-2 h-4 w-4" />
            {t('ai_analyze_report', { name: activeReportName ?? activeReportKey })}
          </Button>
        )}
      </div>

      {loading && (
        <div className="mt-4">
          <LoadingState />
        </div>
      )}

      {activeSummary && !loading && (
        <div className="mt-4 rounded-xl border border-primary-100 bg-white p-4 shadow-sm">
          <div className="mb-3 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-sm font-semibold text-primary-800">
              <Sparkles className="h-4 w-4" />
              {summaryType === 'performance' && t('ai_performance_summary')}
              {summaryType === 'trends' && t('ai_market_trends')}
              {summaryType === 'report' && t('ai_report_analysis')}
            </div>
            <span
              className={cn(
                'rounded-full px-2 py-0.5 text-xs font-medium',
                activeSummary.provider === 'local'
                  ? 'bg-slate-100 text-slate-600'
                  : 'bg-emerald-100 text-emerald-700',
              )}
            >
              {activeSummary.provider}
            </span>
          </div>
          <div className="prose prose-sm max-w-none whitespace-pre-wrap text-slate-700">
            {activeSummary.summary}
          </div>
        </div>
      )}
    </Card>
  )
}
