import type { UnitRow } from "../types/platform";

type Props = {
  units: UnitRow[];
  translate: (key: string) => string;
};

const statusClass: Record<UnitRow["status"], string> = {
  available: "bg-emerald-50 text-emerald-700",
  reserved: "bg-amber-50 text-amber-700",
  contracted: "bg-indigo-50 text-indigo-700",
  sold: "bg-slate-100 text-slate-700",
  delivered: "bg-blue-50 text-blue-700",
  blocked: "bg-rose-50 text-rose-700"
};

export function InventoryTable({ units, translate }: Props) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-950">{translate("inventory")}</h2>
        <button className="rounded-xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
          Export
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500">
              <th className="py-3 text-start">{translate("unitCode")}</th>
              <th className="py-3 text-start">{translate("project")}</th>
              <th className="py-3 text-start">{translate("status")}</th>
              <th className="py-3 text-start">{translate("price")}</th>
            </tr>
          </thead>
          <tbody>
            {units.map((unit) => (
              <tr key={unit.unitCode} className="border-b border-slate-100 last:border-0">
                <td className="py-4 font-semibold text-slate-900">{unit.unitCode}</td>
                <td className="py-4 text-slate-600">{unit.project}</td>
                <td className="py-4">
                  <span className={`rounded-full px-3 py-1 text-xs font-bold ${statusClass[unit.status]}`}>
                    {unit.status}
                  </span>
                </td>
                <td className="py-4 font-semibold text-slate-900">{unit.price}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
