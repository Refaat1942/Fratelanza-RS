import type { PipelineStage } from "../types/platform";

type Props = {
  stages: PipelineStage[];
  translate: (key: string) => string;
};

export function PipelineBoard({ stages, translate }: Props) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-950">{translate("crm")}</h2>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
          AI lead scoring ready
        </span>
      </div>
      <div className="grid gap-4 md:grid-cols-5">
        {stages.map((stage) => (
          <div key={stage.key} className="rounded-2xl bg-slate-50 p-4">
            <div className={`mb-4 h-1.5 rounded-full ${stage.color}`} />
            <p className="text-sm font-semibold text-slate-600">{translate(stage.label)}</p>
            <strong className="mt-3 block text-3xl text-slate-950">{stage.count}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
