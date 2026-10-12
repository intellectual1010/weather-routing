
import type { RiskLevel } from "../types/routing";

export const riskColors: Record<RiskLevel, string> = {
  low: "#16a34a",
  moderate: "#eab308",
  high: "#f97316",
  severe: "#dc2626",
  no_travel: "#7f1d1d",
  unknown: "#64748b",
};

export const riskLabels: Record<RiskLevel, string> = {
  low: "Low",
  moderate: "Moderate",
  high: "High",
  severe: "Severe",
  no_travel: "No Travel",
  unknown: "Unknown",
};

export const routeColors = [
  "#2563eb",
  "#8b5cf6",
  "#0891b2",
];

export function formatDuration(hours: number): string {
  const minutes = Math.round(hours * 60);
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}h ${m}m`;
}

export function formatDateTime(value: string): string {
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  });
}
