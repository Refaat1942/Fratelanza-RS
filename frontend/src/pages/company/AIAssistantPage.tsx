import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { PageHeader } from '@/components/ui/PageHeader'
import { Bot, Send, Sparkles } from 'lucide-react'
import api from '@/lib/api'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  provider?: string
}

export function AIAssistantPage() {
  const { t, i18n } = useTranslation()
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])

  const language = i18n.language.startsWith('ar') ? 'ar' : 'en'

  const { data: providerInfo } = useQuery({
    queryKey: ['ai-provider'],
    queryFn: async () => (await api.get<{ provider: string }>('/reports/ai/provider')).data,
  })

  const chat = useMutation({
    mutationFn: async (text: string) =>
      (
        await api.post<{ response: string; provider: string }>('/reports/ai/chat', {
          message: text,
          language,
        })
      ).data,
  })

  const quickSummary = useMutation({
    mutationFn: async () =>
      (await api.post<{ summary: string; provider: string }>('/reports/ai/performance-summary', { language }))
        .data,
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.summary, provider: data.provider },
      ])
    },
  })

  const sendMessage = async () => {
    if (!message.trim() || chat.isPending) return
    const userMsg = message.trim()
    setMessage('')
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }])
    try {
      const data = await chat.mutateAsync(userMsg)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.response, provider: data.provider },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: t('ai_error'), provider: 'local' },
      ])
    }
  }

  return (
    <div>
      <PageHeader
        title={t('ai_assistant')}
        subtitle={t('ai_assistant_subtitle')}
        icon={Bot}
        accentIndex={5}
        actions={
          <Button variant="secondary" loading={quickSummary.isPending} onClick={() => quickSummary.mutate()}>
            <Sparkles className="me-2 h-4 w-4" />
            {t('ai_performance_summary')}
          </Button>
        }
      />

      <p className="mb-4 text-sm text-slate-500">
        {t('ai_provider')}: {providerInfo?.provider ?? '…'}
      </p>

      <Card className="flex h-[calc(100vh-280px)] flex-col">
        <div className="flex-1 space-y-4 overflow-y-auto p-1">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <Bot className="mb-4 h-12 w-12" />
              <p className="max-w-md text-center">{t('ai_assistant_empty')}</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[85%] rounded-xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'bg-primary-700 text-white'
                    : 'bg-slate-100 text-slate-800'
                }`}
              >
                {msg.content}
                {msg.provider && msg.role === 'assistant' && (
                  <p className="mt-2 text-xs opacity-60">{msg.provider}</p>
                )}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex gap-2 border-t border-slate-200 pt-4">
          <Input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder={t('ai_input_placeholder')}
            className="flex-1"
          />
          <Button onClick={sendMessage} loading={chat.isPending}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </Card>
    </div>
  )
}
