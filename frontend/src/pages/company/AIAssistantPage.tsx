import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Bot, Send } from 'lucide-react'
import api from '@/lib/api'

export function AIAssistantPage() {
  const { t } = useTranslation()
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string }[]>([])
  const [loading, setLoading] = useState(false)

  const sendMessage = async () => {
    if (!message.trim()) return
    const userMsg = message
    setMessage('')
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }])
    setLoading(true)
    try {
      const { data } = await api.post('/ai/chat', { message: userMsg })
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }])
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Error connecting to AI service.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-900">{t('ai_assistant')}</h1>
      <Card className="flex h-[calc(100vh-220px)] flex-col">
        <div className="flex-1 space-y-4 overflow-y-auto">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <Bot className="mb-4 h-12 w-12" />
              <p>اسألني عن المبيعات، التحصيلات، أو أي شيء في المنصة</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[70%] rounded-xl px-4 py-2.5 text-sm ${
                  msg.role === 'user'
                    ? 'bg-primary-700 text-white'
                    : 'bg-slate-100 text-slate-800'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex gap-2 border-t border-slate-200 pt-4">
          <Input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="اكتب رسالتك..."
            className="flex-1"
          />
          <Button onClick={sendMessage} loading={loading}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </Card>
    </div>
  )
}
