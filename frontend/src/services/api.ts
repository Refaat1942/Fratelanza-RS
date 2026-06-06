import type { KPI, PipelineStage, UnitRow } from "../types/platform";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export async function apiGet<T>(path: string, token?: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    }
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const demoKpis: KPI[] = [
  { key: "sales", label: "totalSales", value: "EGP 248M", change: "+18%" },
  { key: "collected", label: "collected", value: "EGP 91M", change: "+9%" },
  { key: "overdue", label: "overdue", value: "EGP 14.2M", change: "-4%" },
  { key: "units", label: "availableUnits", value: "318", change: "+22" }
];

export const demoPipeline: PipelineStage[] = [
  { key: "newLead", label: "newLead", count: 128, color: "bg-sky-500" },
  { key: "contacted", label: "contacted", count: 86, color: "bg-indigo-500" },
  { key: "siteVisit", label: "siteVisit", count: 42, color: "bg-amber-500" },
  { key: "negotiation", label: "negotiation", count: 31, color: "bg-orange-500" },
  { key: "reservation", label: "reservation", count: 17, color: "bg-emerald-500" }
];

export const demoUnits: UnitRow[] = [
  { unitCode: "FRA-NC-A-1204", project: "New Cairo Residence", status: "available", price: "8,750,000" },
  { unitCode: "FRA-ZD-V-018", project: "Zayed Villas", status: "reserved", price: "18,200,000" },
  { unitCode: "FRA-NS-C-301", project: "North Coast", status: "contracted", price: "11,400,000" },
  { unitCode: "FRA-BH-O-0902", project: "Business Hub", status: "available", price: "6,950,000" }
];
