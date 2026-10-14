
import { useEffect, useState } from "react";
import { CloudSun, LoaderCircle, Clock3 } from "lucide-react";

type LoadingType = "routes" | "weather";

interface Props {
  type: LoadingType;
}

export default function MapLoadingOverlay({ type }: Props) {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    setSeconds(0);

    const timer = window.setInterval(() => {
      setSeconds((previous) => previous + 1);
    }, 1000);

    return () => window.clearInterval(timer);
  }, [type]);

  const isRoutes = type === "routes";

  const title = isRoutes
    ? "Analyzing Truck Routes"
    : "Loading Weather Heatmap";

  const message = isRoutes
    ? "Calculating road routes, checkpoint forecasts, and safety risks."
    : "Retrieving hourly weather forecasts along the selected route.";

  const minutes = String(Math.floor(seconds / 60)).padStart(2, "0");
  const remainingSeconds = String(seconds % 60).padStart(2, "0");

  return (
    <div
      className="absolute inset-0 z-[1000] flex items-center
                 justify-center bg-slate-900/35 backdrop-blur-[2px]
                 rounded-lg cursor-wait"
      role="status"
      aria-live="polite"
      aria-label={title}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl border
                   border-slate-200 px-7 py-8 text-center
                   w-[min(90%,360px)]"
      >
        <div className="relative w-16 h-16 mx-auto mb-4">
          <LoaderCircle
            className="w-16 h-16 text-cyan-600 animate-spin"
            strokeWidth={2.5}
          />

          <CloudSun
            className="absolute left-5 top-5 w-6 h-6
                       text-cyan-700"
          />
        </div>

        <h3 className="text-lg font-bold text-slate-900">
          {title}
        </h3>

        <p className="mt-2 text-sm text-slate-600">
          {message}
        </p>

        <div className="mt-5 flex items-center justify-center
                        gap-2 text-sm text-slate-500">
          <Clock3 size={16} />
          <span>
            Elapsed: {minutes}:{remainingSeconds}
          </span>
        </div>

        <p className="mt-3 text-xs text-slate-400">
          {seconds >= 30
            ? "Still processing. This may take a little longer."
            : "Please wait while we analyze your trip."}
        </p>
      </div>
    </div>
  );
}
