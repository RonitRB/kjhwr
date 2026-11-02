export function formatValue(value: number | null | undefined, unit = ''): string {
  if (value == null || !Number.isFinite(value)) return 'N/A';
  return `${value.toLocaleString(undefined, { maximumFractionDigits: 1 })}${unit}`;
}
