export type KPI = {
  key: string;
  label: string;
  value: string;
  change?: string;
};

export type PipelineStage = {
  key: string;
  label: string;
  count: number;
  color: string;
};

export type UnitRow = {
  unitCode: string;
  project: string;
  status: "available" | "reserved" | "contracted" | "sold" | "delivered" | "blocked";
  price: string;
};
