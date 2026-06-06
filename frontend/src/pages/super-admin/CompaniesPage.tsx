import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Building2, SlidersHorizontal } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { CompanyFormModal } from '@/components/forms/CompanyFormModal'
import { CompanyModulesModal } from '@/components/forms/CompanyModulesModal'
import api from '@/lib/api'
import type { Company, Paginated } from '@/types'

export function CompaniesPage() {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [modulesCompany, setModulesCompany] = useState<Company | null>(null)
  const { data, isLoading } = useQuery({
    queryKey: ['companies'],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Company>>('/super-admin/companies')
      return data
    },
  })

  const suspendCompany = useMutation({
    mutationFn: async (id: number) => {
      await api.post(`/super-admin/companies/${id}/suspend`)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['companies'] }),
  })

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{t('companies')}</h1>
        <Button onClick={() => setOpen(true)}>
          <Building2 className="me-2 h-4 w-4" />
          {t('add_company')}
        </Button>
      </div>
      <Card>
        {isLoading ? (
          <p className="text-slate-500">{t('loading')}</p>
        ) : data?.items.length === 0 ? (
          <p className="text-slate-500">{t('no_data')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th className="pb-3 text-start font-medium">#</th>
                  <th className="pb-3 text-start font-medium">{t('companies')}</th>
                  <th className="pb-3 text-start font-medium">{t('status')}</th>
                  <th className="pb-3 text-start font-medium">Code</th>
                  <th className="pb-3 text-start font-medium">{t('actions')}</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((company) => (
                  <tr key={company.id} className="border-b border-slate-100">
                    <td className="py-3">{company.id}</td>
                    <td className="py-3 font-medium">
                      {i18n.language === 'ar' ? company.name_ar : company.name_en}
                    </td>
                    <td className="py-3">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                        company.status === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
                      }`}>
                        {company.status}
                      </span>
                    </td>
                    <td className="py-3 text-slate-500">{company.code}</td>
                    <td className="py-3">
                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="secondary"
                          onClick={() => setModulesCompany(company)}
                        >
                          <SlidersHorizontal className="me-1 h-4 w-4" />
                          {t('manage_modules')}
                        </Button>
                        {company.status === 'active' && (
                          <Button
                            variant="secondary"
                            loading={suspendCompany.isPending}
                            onClick={() => suspendCompany.mutate(company.id)}
                          >
                            {t('suspend')}
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      <CompanyFormModal open={open} onClose={() => { setOpen(false); qc.invalidateQueries({ queryKey: ['companies'] }) }} />
      {modulesCompany && (
        <CompanyModulesModal
          open={!!modulesCompany}
          companyId={modulesCompany.id}
          companyName={i18n.language === 'ar' ? modulesCompany.name_ar : modulesCompany.name_en}
          onClose={() => setModulesCompany(null)}
        />
      )}
    </div>
  )
}
