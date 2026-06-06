import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'

interface ChangePasswordModalProps {
  open: boolean
  onClose: () => void
}

export function ChangePasswordModal({ open, onClose }: ChangePasswordModalProps) {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [current, setCurrent] = useState('')
  const [newPass, setNewPass] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (newPass.length < 8) {
      setError(t('password_min_8'))
      return
    }
    if (newPass !== confirm) {
      setError(t('passwords_mismatch'))
      return
    }
    setError('')
    setLoading(true)
    try {
      await api.post('/auth/change-password', { current_password: current, new_password: newPass })
      setSuccess(true)
      setCurrent('')
      setNewPass('')
      setConfirm('')
    } catch {
      setError(t('wrong_current_password'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('change_password')}>
      {success ? (
        <div className="text-center">
          <p className="mb-4 text-emerald-700">{t('password_changed')}</p>
          <Button onClick={onClose}>{t('done')}</Button>
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          <Input label={t('current_password')} type="password" value={current} onChange={(e) => setCurrent(e.target.value)} required />
          <Input label={t('new_password')} type="password" value={newPass} onChange={(e) => setNewPass(e.target.value)} required />
          <Input label={t('confirm_password')} type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex gap-3">
            <Button type="submit" loading={loading}>{t('save')}</Button>
            <Button type="button" variant="secondary" onClick={onClose}>{t('cancel')}</Button>
          </div>
        </form>
      )}
    </Modal>
  )
}
