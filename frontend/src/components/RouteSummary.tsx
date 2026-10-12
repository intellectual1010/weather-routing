
import {
  AlertTriangle,
  CheckCircle2,
  ShieldCheck,
} from "lucide-react";

import type { RouteResponse } from "../types/routing";
import { formatDuration } from "../utils/risk";

interface Props {
  data: RouteResponse;
}

export default function RouteSummary({ data }: Props) {
  const recommended = data.routes.find(
    (route) => route.id === data.recommended_route_id
  );

  if (!recommended) {
    return (
      <div
        role="alert"
        className="rounded-xl border border-amber-300
                   bg-amber-50 p-5"
      >
        <div className="flex items-center gap-2 text-amber-800">
          <AlertTriangle size={20} />
          <h3 className="font-bold">
            No Route Can Be Recommended
          </h3>
        </div>

        <p className="text-sm text-amber-800 mt-2">
          {data.recommendation_reason}
        </p>

        <p className="text-xs text-amber-700 mt-2">
          Review route risks and forecast coverage before travel.
        </p>
      </div>
    );
  }

  const risk = recommended.risk_summary;

  return (
    <div className="rounded-xl border border-green-200 bg-green-50 p-5">
      <div className="flex flex-wrap justify-between gap-3">
        <div className="flex items-center gap-2 text-green-800">
          <ShieldCheck size={24} />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide">
              Recommended Route
            </p>
            <h3 className="text-xl font-bold">
              {recommended.name}
            </h3>
          </div>
        </div>

        <div className="flex items-center gap-1 text-green-700 text-sm">
          <CheckCircle2 size={17} />
          Best ranked available option
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
        {[
          {
            label: "Distance",
            value: `${recommended.distance_miles.toFixed(1)} mi`,
          },
          {
            label: "Travel Time",
            value: formatDuration(recommended.duration_hours),
          },
          {
            label: "Severe Miles",
            value: `${risk.severe_miles.toFixed(1)} mi`,
          },
          {
            label: "High Miles",
            value: `${risk.high_miles.toFixed(1)} mi`,
          },
        ].map((item) => (
          <div
            key={item.label}
            className="bg-white rounded-lg p-3"
          >
            <p className="text-xs text-slate-500">
              {item.label}
            </p>
            <p className="text-lg font-bold mt-1">
              {item.value}
            </p>
          </div>
        ))}
      </div>

      <p className="text-xs text-green-900 mt-4">
        {data.recommendation_reason}
      </p>
    </div>
  );
}
