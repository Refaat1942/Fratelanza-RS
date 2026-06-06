import {
  BarChart3,
  Bot,
  Building2,
  CircleDollarSign,
  Construction,
  Headphones,
  Landmark,
  ShieldCheck,
  Users
} from "lucide-react";
import type { ReactNode } from "react";

import type { Locale } from "../i18n/dictionary";

type Props = {
  locale: Locale;
  translate: (key: string) => string;
  onToggleLocale: () => void;
  children: ReactNode;
};

const navItems = [
  { key: "dashboard", icon: BarChart3 },
  { key: "crm", icon: Users },
  { key: "inventory", icon: Building2 },
  { key: "collections", icon: CircleDollarSign },
  { key: "construction", icon: Construction },
  { key: "finance", icon: Landmark },
  { key: "customerService", icon: Headphones },
  { key: "aiInsights", icon: Bot }
];

export function AppShell({ locale, translate, onToggleLocale, children }: Props) {
  return (
    <div className="min-h-screen bg-slate-100">
      <aside className="fixed inset-y-0 hidden w-72 border-e border-white/10 bg-slate-950 p-6 text-white lg:block">
        <div className="rounded-3xl bg-white/10 p-5">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-gold text-slate-950">
            <ShieldCheck />
          </div>
          <h1 className="text-xl font-black leading-tight">{translate("appName")}</h1>
          <p className="mt-2 text-sm text-slate-300">{translate("subtitle")}</p>
        </div>

        <nav className="mt-8 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <a
                key={item.key}
                href={`#${item.key}`}
                className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold text-slate-300 transition hover:bg-white/10 hover:text-white"
              >
                <Icon className="h-5 w-5" />
                {translate(item.key)}
              </a>
            );
          })}
        </nav>
      </aside>

      <main className="lg:ps-72">
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/85 px-5 py-4 backdrop-blur">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm font-bold text-brand-emerald">{translate("superAdmin")}</p>
              <h2 className="text-2xl font-black text-slate-950">{translate("dashboard")}</h2>
            </div>
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">
                {translate("tenantIsolation")}
              </span>
              <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-700">
                {translate("rbac")}
              </span>
              <button
                onClick={onToggleLocale}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-900"
              >
                {translate("switchLanguage")} ({locale.toUpperCase()})
              </button>
            </div>
          </div>
        </header>

        <div className="p-5 lg:p-8">{children}</div>
      </main>
    </div>
  );
}
