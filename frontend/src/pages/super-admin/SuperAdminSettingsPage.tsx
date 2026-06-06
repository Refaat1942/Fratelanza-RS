import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Database, Settings, BarChart3 } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useFormatNumber } from '@/hooks/useFormatNumber'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

type Tab = 'settings' | 'backup' | 'stats'

interface SystemSetting {
  key: string
  value: string
  description_ar?: string
  description_en?: string
}

export function SuperAdminSettingsPage() {
  const { t, i18n } = useTranslation()
  const { formatInteger } = useFormatNumber()
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('settings')
  const [backupMsg, setBackupMsg] = useState('')
  const [edits, setEdits] = useState<Record<string, string>>({})

  const { data: settings = [], isLoading } = useQuery({
    queryKey: ['system-settings'],
    queryFn: async () => (await api.get<SystemSetting[]>('/super-admin/settings')).data,
    enabled: tab === 'settings',
  })

  const { data: stats } = useQuery({
    queryKey: ['system-stats'],
    queryFn: async () => (await api.get<Record<string, number>>('/super-admin/system-stats')).data,
    enabled: tab === 'stats',
  })

  const saveSetting = useMutation({
    mutationFn: async ({ key, value }: { key: string; value: string }) => {
      await api.put(`/super-admin/settings/${key}`, { value })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['system-settings'] }),
  })

  const runBackup = async () => {
    setBackupMsg(t('loading'))
    try {
      const { data } = await api.post<{ success: boolean; message: string; file?: string }>('/super-admin/backup')
      setBackupMsg(data.success ? `${t('backup_success')}: ${data.file ?? ''}` : data.message)
    } catch {
      setBackupMsg(t('backup_failed'))
    }
  }

  const tabs: { id: Tab; icon: typeof Settings; label: string }[] = [
    { id: 'settings', icon: Settings, label: t('platform_settings') },
    { id: 'backup', icon: Database, label: t('database_backup') },
    { id: 'stats', icon: BarChart3, label: t('platform_stats') },
  ]

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-900">{t('settings')}</h1>
      <div className="mb-6 flex gap-2">
        {tabs.map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={cn(
              'flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium',
              tab === id ? 'bg-primary-700 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200',
            )}
          >
            <Icon className="h-4 w-4" />{label}
          </button>
        ))}
      </div>

      {tab === 'settings' && (
        <Card>
          <p className="mb-4 text-sm text-slate-600">{t('platform_settings_help')}</p>
          {isLoading ? (
            <p className="text-slate-500">{t('loading')}</p>
          ) : settings.length === 0 ? (
            <p className="text-slate-500">{t('no_settings')}</p>
          ) : (
            <div className="space-y-4">
              {settings.map((s) => (
                <div key={s.key} className="flex flex-wrap items-end gap-3 border-b border-slate-100 pb-4">
                  <div className="min-w-[200px] flex-1">
                    <p className="text-sm font-medium text-slate-900">{s.key}</p>
                    <p className="text-xs text-slate-500">
                      {i18n.language === 'ar' ? s.description_ar : s.description_en}
                    </p>
                  </div>
                  <Input
                    className="max-w-md flex-1"
                    value={edits[s.key] ?? s.value ?? ''}
                    onChange={(e) => setEdits({ ...edits, [s.key]: e.target.value })}
                  />
                  <Button
                    variant="secondary"
                    loading={saveSetting.isPending}
                    onClick={() => saveSetting.mutate({ key: s.key, value: edits[s.key] ?? s.value ?? '' })}
                  >
                    {t('save')}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {tab === 'backup' && (
        <Card>
          <h3 className="mb-2 font-semibold text-slate-900">{t('database_backup')}</h3>
          <p className="mb-4 text-sm text-slate-600">{t('database_backup_help')}</p>
          <Button onClick={runBackup}>
            <Database className="me-2 h-4 w-4" />{t('run_backup')}
          </Button>
          {backupMsg && <p className="mt-4 text-sm text-slate-600">{backupMsg}</p>}
        </Card>
      )}

      {tab === 'stats' && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {stats && Object.entries(stats).map(([key, val]) => (
            <Card key={key}>
              <p className="text-sm capitalize text-slate-500">{key.replace(/_/g, ' ')}</p>
              <p className="text-2xl font-bold text-slate-900">{formatInteger(val)}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
