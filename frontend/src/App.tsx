import { useEffect, useState } from "react";
import {
  CloudSun,
  MapPinned,
  Truck,
  Wifi,
  WifiOff,
} from "lucide-react";
import { checkBackendHealth } from "./services/api";

export default function App() {
  const [connected, setConnected] = useState<boolean | null>(null);

  useEffect(() => {
    checkBackendHealth()
      .then(() => setConnected(true))
      .catch(() => setConnected(false));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-slate-950 text-white px-8 py-5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Truck className="w-8 h-8 text-cyan-400" />

            <div>
              <h1 className="text-xl font-bold">
                Spotter Weather Routing
              </h1>

              <p className="text-xs text-slate-400">
                Intelligent Truck Route Planning
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-sm">
            {connected ? (
              <>
                <Wifi className="w-4 h-4 text-green-400" />
                <span>API Connected</span>
              </>
            ) : connected === false ? (
              <>
                <WifiOff className="w-4 h-4 text-red-400" />
                <span>API Disconnected</span>
              </>
            ) : (
              <span>Connecting...</span>
            )}
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto p-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-slate-900">
            Weather-Aware Route Planner
          </h2>

          <p className="mt-2 text-slate-500">
            Find safer trucking routes using real-time weather
            forecasts, road conditions, and load information.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <MapPinned className="w-9 h-9 text-blue-600 mb-4" />

            <h3 className="font-semibold text-lg">
              Route Optimization
            </h3>

            <p className="text-sm text-slate-500 mt-2">
              Compare up to three route alternatives based on
              travel time and weather risk.
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-sm border p-6">
            <CloudSun className="w-9 h-9 text-orange-500 mb-4" />

            <h3 className="font-semibold text-lg">
              Weather Intelligence
            </h3>

            <p className="text-sm text-slate-500 mt-2">
              Analyze forecast conditions at route checkpoints
              using estimated arrival times.
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-sm border p-6">
            <Truck className="w-9 h-9 text-cyan-600 mb-4" />

            <h3 className="font-semibold text-lg">
              Load-Aware Safety
            </h3>

            <p className="text-sm text-slate-500 mt-2">
              Evaluate wind, rain, and snow risk based on your
              vehicle's cargo weight.
            </p>
          </div>
        </div>

        <div className="bg-white rounded-xl border shadow-sm mt-8 p-12 text-center">
          <MapPinned className="w-12 h-12 text-slate-300 mx-auto" />

          <h3 className="text-xl font-semibold mt-4">
            Route Planner
          </h3>

          <p className="text-slate-500 mt-2">
            The interactive route planner will appear here.
          </p>

          <span className="inline-block mt-4 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg text-sm">
            Next: Routing API Integration
          </span>
        </div>
      </main>
    </div>
  );
}