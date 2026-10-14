
import { CheckCircle2, Clock3, Route as RouteIcon } from "lucide-react";
import type { RouteOption, RiskLevel } from "../types/routing";
import {
  riskColors,
  riskLabels,
  formatDuration,
} from "../utils/risk";

interface Props {
  route: RouteOption;
  selected: boolean;
  recommended: boolean;
  color: string;
  onClick: () => void;
  disabled?: boolean;
}

const segments: { level: RiskLevel; key: keyof RouteOption["risk_summary"] }[] = [
  { level: "low", key: "low_miles" },
  { level: "moderate", key: "moderate_miles" },
  { level: "high", key: "high_miles" },
  { level: "severe", key: "severe_miles" },
  { level: "no_travel", key: "no_travel_miles" },
  { level: "unknown", key: "unknown_miles" },
];

export default function RouteCard({
  route, selected, recommended, color, onClick, disabled
}: Props) {
  const summary = route.risk_summary;

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={selected}
      className={`w-full text-left rounded-xl border-2 bg-white p-4
        hover:shadow-md transition ${
          selected ? "border-cyan-600 shadow-sm" : "border-slate-200"
        }`}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span
            className="h-3 w-3 rounded-full"
            style={{ backgroundColor: color }}
          />
          <span className="font-semibold">{route.name}</span>
        </div>
        {recommended && (
          <span className="flex items-center gap-1 text-xs font-semibold
                           rounded-full bg-green-100 text-green-700 px-2 py-1">
            <CheckCircle2 size={13} /> Recommended
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 mt-3">
        <div className="flex items-center gap-2 text-sm">
          <RouteIcon size={15} className="text-slate-400" />
          <span>{route.distance_miles.toFixed(1)} mi</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Clock3 size={15} className="text-slate-400" />
          <span>{formatDuration(route.duration_hours)}</span>
        </div>
      </div>

      <div className="mt-3 flex h-2.5 rounded-full overflow-hidden bg-slate-100">
        {segments.map(({ level, key }) => {
          const miles = Number(summary[key] ?? 0);
          return (
            <div
              key={level}
              title={`${riskLabels[level]}: ${miles.toFixed(1)} mi`}
              style={{
                width: `${(miles / Math.max(route.distance_miles, 1)) * 100}%`,
                backgroundColor: riskColors[level],
              }}
            />
          );
        })}
      </div>

      <div className="grid grid-cols-3 gap-2 mt-3 text-xs">
        <div>
          <p className="text-slate-500">High</p>
          <p className="font-semibold">{summary.high_miles.toFixed(1)} mi</p>
        </div>
        <div>
          <p className="text-slate-500">Severe</p>
          <p className="font-semibold">{summary.severe_miles.toFixed(1)} mi</p>
        </div>
        <div>
          <p className="text-slate-500">No Travel</p>
          <p className="font-semibold">{summary.no_travel_miles.toFixed(1)} mi</p>
        </div>
      </div>

      <p className="mt-3 text-xs text-slate-500">
        {route.checkpoint_count} checkpoints ·{" "}
        Risk: {riskLabels[summary.highest_risk]}
      </p>

      {!summary.forecast_complete && (
        <p className="mt-2 text-xs text-amber-700">
          Some forecast data is unavailable.
        </p>
      )}
    </button>
  );
}
