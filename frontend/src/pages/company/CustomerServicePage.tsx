import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Headphones, Plus, MessageSquare } from 'lucide-react'
import { DataTable } from '@/components/ui/DataTable'
import { RowActions } from '@/components/ui/RowActions'
import { PageHeader } from '@/components/ui/PageHeader'
import { ReportLinkButton } from '@/components/ui/ReportLinkButton'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useListData } from '@/hooks/useListData'
import { confirmDelete, useDeleteEntity } from '@/hooks/useDeleteEntity'
import { TicketFormModal } from '@/components/forms/ModuleFormModals'
import api from '@/lib/api'

function useCrudModal() {
  const [open, setOpen] = useState(false)
  const [editRow, setEditRow] = useState<Record<string, unknown> | null>(null)
  return {
    open,
    editRow,
    openCreate: () => { setEditRow(null); setOpen(true) },
    openEdit: (row: Record<string, unknown>) => { setEditRow(row); setOpen(true) },
    close: () => { setOpen(false); setEditRow(null) },
  }
}

export function CustomerServicePage() {
  const { t } = useTranslation()
  const modal = useCrudModal()
  const deleteTicket = useDeleteEntity('/tickets', ['tickets'])
  const { items, isLoading, refetch } = useListData<Record<string, unknown>>('tickets', '/tickets')
  const [commentsOpen, setCommentsOpen] = useState(false)
  const [activeTicket, setActiveTicket] = useState<Record<string, unknown> | null>(null)
  const [comments, setComments] = useState<Record<string, unknown>[]>([])
  const [newComment, setNewComment] = useState('')
  const [commentLoading, setCommentLoading] = useState(false)

  const openComments = async (row: Record<string, unknown>) => {
    setActiveTicket(row)
    setCommentsOpen(true)
    const { data } = await api.get(`/tickets/${row.id}/comments`)
    setComments(data)
  }

  useEffect(() => {
    if (!commentsOpen) {
      setComments([])
      setNewComment('')
      setActiveTicket(null)
    }
  }, [commentsOpen])

  const addComment = async () => {
    if (!activeTicket || !newComment.trim()) return
    setCommentLoading(true)
    try {
      await api.post(`/tickets/${activeTicket.id}/comments`, { comment: newComment.trim() })
      const { data } = await api.get(`/tickets/${activeTicket.id}/comments`)
      setComments(data)
      setNewComment('')
    } finally {
      setCommentLoading(false)
    }
  }

  return (
    <div>
      <PageHeader
        title={t('customer_service')}
        subtitle={t('customer_service_help')}
        icon={Headphones}
        accentIndex={7}
        actions={
          <>
            <ReportLinkButton reportKey="tickets" />
            <Button onClick={modal.openCreate}><Plus className="me-2 h-4 w-4" />{t('add_ticket')}</Button>
          </>
        }
      />

      <DataTable
        title={t('customer_service')}
        loading={isLoading}
        exportFilename="tickets"
        data={items}
        columns={[
          { key: 'ticket_number', label: '#' },
          { key: 'subject', label: t('subject') },
          { key: 'customer_name', label: t('customers') },
          { key: 'category', label: t('category') },
          { key: 'priority', label: t('priority') },
          { key: 'status', label: t('status') },
        ]}
        rowActions={(row) => (
          <RowActions
            onEdit={() => modal.openEdit(row)}
            onDelete={() => confirmDelete(t) && deleteTicket.mutate(row.id as number, { onSuccess: () => refetch() })}
            extra={
              <Button variant="ghost" className="!px-2 !py-1.5" onClick={() => openComments(row)} title={t('comments')}>
                <MessageSquare className="h-4 w-4 text-primary-600" />
              </Button>
            }
          />
        )}
      />

      <TicketFormModal open={modal.open} onClose={() => { modal.close(); refetch() }} editRow={modal.editRow} />

      <Modal open={commentsOpen} onClose={() => setCommentsOpen(false)} title={t('ticket_comments')} className="max-w-lg">
        <p className="mb-4 text-sm text-slate-600">{String(activeTicket?.subject ?? '')}</p>
        <div className="mb-4 max-h-48 space-y-2 overflow-y-auto">
          {comments.length === 0 ? (
            <p className="text-sm text-slate-500">{t('no_comments')}</p>
          ) : (
            comments.map((c) => (
              <div key={String(c.id)} className="rounded-lg bg-slate-50 p-3 text-sm">
                <p className="font-medium text-slate-800">{String(c.user_name)}</p>
                <p className="text-slate-700">{String(c.comment)}</p>
              </div>
            ))
          )}
        </div>
        <div className="flex gap-2">
          <Input value={newComment} onChange={(e) => setNewComment(e.target.value)} placeholder={t('add_comment_placeholder')} />
          <Button onClick={addComment} loading={commentLoading}>{t('add')}</Button>
        </div>
      </Modal>
    </div>
  )
}
