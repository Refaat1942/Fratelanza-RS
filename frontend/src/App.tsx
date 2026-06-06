import { useMemo, useState } from "react";

import { InventoryTable } from "./components/InventoryTable";
import { KpiCard } from "./components/KpiCard";
import { PipelineBoard } from "./components/PipelineBoard";
import { dictionaries, direction, type Locale } from "./i18n/dictionary";
import { AppShell } from "./layouts/AppShell";
import { demoKpis, demoPipeline, demoUnits } from "./services/api";

function App() {
  const [locale, setLocale] = useState<Locale>("ar");
  const dictionary = dictionaries[locale];

  const translate = useMemo(() => {
    return (key: string) => dictionary[key] ?? key;
  }, [dictionary]);

  const toggleLocale = () => setLocale((current) => (current === "ar" ? "en" : "ar"));

  return (
    <div lang={locale} dir={direction(locale)}>
      <AppShell locale={locale} translate={translate} onToggleLocale={toggleLocale}>
        <section className="mb-8 overflow-hidden rounded-[2rem] bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 p-8 text-white shadow-soft">
          <div className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
            <div>
              <p className="text-sm font-bold uppercase tracking-[0.3em] text-brand-gold">
                FRATELANZA SaaS
              </p>
              <h1 className="mt-4 max-w-3xl text-4xl font-black leading-tight lg:text-5xl">
                {translate("appName")}
              </h1>
              <p className="mt-4 max-w-2xl text-lg text-slate-300">{translate("subtitle")}</p>
            </div>
            <div className="grid gap-3 rounded-3xl bg-white/10 p-5">
              {[translate("bilingual"), translate("tenantIsolation"), translate("rbac")].map((item) => (
                <div key={item} className="rounded-2xl bg-white/10 px-4 py-3 text-sm font-semibold">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mb-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {demoKpis.map((kpi) => (
            <KpiCard key={kpi.key} kpi={kpi} label={translate(kpi.label)} />
          ))}
        </section>

        <div className="grid gap-8">
          <PipelineBoard stages={demoPipeline} translate={translate} />
          <InventoryTable units={demoUnits} translate={translate} />

          <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
            <h2 className="text-lg font-bold text-slate-950">{translate("nextActions")}</h2>
            <div className="mt-5 grid gap-4 md:grid-cols-3">
              {[
                "Connect FastAPI dashboard endpoint",
                "Add contract template builder",
                "Enable WhatsApp and SMS notification adapters"
              ].map((action) => (
                <div key={action} className="rounded-2xl bg-slate-50 p-4 text-sm font-semibold text-slate-700">
                  {action}
                </div>
              ))}
            </div>
          </section>
        </div>
      </AppShell>
    </div>
  );
}

export default App;
