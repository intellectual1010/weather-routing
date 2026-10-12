
import { riskColors, riskLabels } from "../utils/risk";
import type { RiskLevel } from "../types/routing";

const levels: RiskLevel[] = [
  "low",
  "moderate",
  "high",
  "severe",
  "no_travel",
  "unknown",
];

export default function RiskLegend() {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-2">
      {levels.map((level) => (
        <div key={level} className="flex items-center gap-1.5">
          <span
            className="h-3 w-3 rounded-full"
            style={{ backgroundColor: riskColors[level] }}
          />
          <span className="text-xs text-slate-600">
            {riskLabels[level]}
          </span>
        </div>
      ))}
    </div>
  );
}
