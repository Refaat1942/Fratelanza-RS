function isUnlimited(value: number | null | undefined): boolean {
  return value != null && value <= 0
}

export function formatPlanLimit(
  value: number | null | undefined,
  unlimitedLabel: string,
): string {
  if (isUnlimited(value)) return unlimitedLabel
  return String(value ?? 0)
}
