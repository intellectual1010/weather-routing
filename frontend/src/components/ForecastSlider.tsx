
import { Clock3, CloudSun } from "lucide-react";
import { formatDateTime } from "../utils/risk";

interface Props {
  hour: number;
  onChange: (value: number) => void;
  referenceTime: string;
  disabled?: boolean;
}

export default function ForecastSlider({
  hour,
  onChange,
  referenceTime,
  disabled = false,
}: Props) {
  const selectedTime = new Date(
    new Date(referenceTime).getTime() +
      hour * 60 * 60 * 1000
  );

  return (
    <section className="bg-white rounded-xl border
                        border-slate-200 p-5 shadow-sm">
      <div className="flex flex-wrap justify-between
                      items-center gap-3">
        <div className="flex items-center gap-2">
          <CloudSun className="text-cyan-700" size={22} />
          <div>
            <h3 className="font-bold text-lg">
              Weather Corridor Forecast
            </h3>
            <p className="text-xs text-slate-500">
              Compare weather conditions across the route
            </p>
          </div>
        </div>

        <span className="rounded-lg bg-cyan-50
                         text-cyan-700 font-bold px-3 py-2">
          +{hour}h
        </span>
      </div>

      <div className="mt-5">
        <input
          type="range"
          min={0}
          max={48}
          step={1}
          value={hour}
          onChange={(e) => onChange(Number(e.target.value))}
          disabled={disabled}
          aria-label="Forecast offset in hours"
          className="w-full accent-cyan-700"
        />

        <div className="flex justify-between mt-1
                        text-xs text-slate-500">
          <span>0h</span>
          <span>12h</span>
          <span>24h</span>
          <span>36h</span>
          <span>48h</span>
        </div>
      </div>

      <div className="flex items-center gap-2 mt-4
                      text-sm text-slate-600">
        <Clock3 size={16} />
        Forecast: {formatDateTime(selectedTime.toISOString())}
      </div>

      <p className="text-xs text-slate-400 mt-3">
        This slider shows weather at a selected forecast
        hour. Route recommendations still use arrival-time
        forecasts for each checkpoint.
      </p>
    </section>
  );
}
