import type { KPI } from "../types/platform";

type Props = {
  kpi: KPI;
  label: string;
};

export function KpiCard({ kpi, label }: Props) {
  const positive = !kpi.change?.startsWith("-");

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <div className="mt-3 flex items-end justify-between gap-4">
        <strong className="text-2xl font-bold text-slate-950">{kpi.value}</strong>
        {kpi.change ? (
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              positive ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
            }`}
          >
            {kpi.change}
          </span>
        ) : null}
      </div>
    </div>
  );
}
