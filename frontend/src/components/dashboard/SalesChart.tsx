import { Card, CardHeader } from '@/components/ui/Card'
import { useTranslation } from 'react-i18next'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface SalesChartProps {
  data: { label: string; value: number }[]
}

export function SalesChart({ data }: SalesChartProps) {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader title={t('total_sales')} />
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="label" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Bar dataKey="value" fill="#0159a1" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  )
}
