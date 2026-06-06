import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'

interface ResetPasswordModalProps {
  open: boolean
  onClose: () => void
  userId: number | null
  userEmail: string
  onSaved?: () => void
}

export function ResetPasswordModal({ open, onClose, userId, userEmail, onSaved }: ResetPasswordModalProps) {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!userId) return
    if (password.length < 6) {
      setError(t('password_min_length'))
      return
    }
    if (password !== confirm) {
      setError(t('passwords_mismatch'))
      return
    }
    setError('')
    setLoading(true)
    try {
      await api.post(`/users/${userId}/reset-password`, { new_password: password })
      setPassword('')
      setConfirm('')
      onSaved?.()
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('reset_password')}>
      <form onSubmit={submit} className="space-y-4">
        <p className="text-sm text-slate-600">{t('reset_password_for')}: <strong>{userEmail}</strong></p>
        <Input label={t('new_password')} type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <Input label={t('confirm_password')} type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="flex gap-3">
          <Button type="submit" loading={loading}>{t('reset_password')}</Button>
          <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
        </div>
      </form>
    </Modal>
  )
}
