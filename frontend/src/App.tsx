
import { useEffect, useState } from "react";
import {
  AlertTriangle,
  CloudSun,
  MapPinned,
  Truck,
  Wifi,
  WifiOff,
} from "lucide-react";

import TripForm from "./components/TripForm";
import RouteMap from "./components/RouteMap";
import RouteCard from "./components/RouteCard";
import RouteSummary from "./components/RouteSummary";
import RiskLegend from "./components/RiskLegend";

import { checkBackendHealth } from "./services/api";
import { analyzeRoutes, getApiError } from "./services/routing";
import { routeColors } from "./utils/risk";

import type {
  RouteResponse,
  TripRequest,
} from "./types/routing";

export default function App() {
  const [connected, setConnected] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [result, setResult] = useState<RouteResponse | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);

  useEffect(() => {
    checkBackendHealth()
      .then(() => setConnected(true))
      .catch(() => setConnected(false));
  }, []);

  async function handleAnalyze(trip: TripRequest) {
    setLoading(true);
    setError(null);
    setResult(null);
    setSelectedRouteId(null);

    try {
      const data = await analyzeRoutes(trip);

      setResult(data);

      const selected =
        data.recommended_route_id ?? data.routes[0]?.id ?? null;

      setSelectedRouteId(selected);
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="bg-slate-950 text-white shadow-sm">
        <div className="max-w-[1600px] mx-auto px-5 py-4
                        flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="bg-cyan-500/15 p-2.5 rounded-lg">
              <Truck className="h-7 w-7 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold">
                Spotter Weather Routing
              </h1>
              <p className="text-xs text-slate-400">
                Weather-Aware Truck Route Planning
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs">
            {connected === true ? (
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
              <span>Checking API...</span>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto p-4 md:p-6">
        <div className="mb-6">
          <div className="flex items-center gap-2">
            <CloudSun className="text-cyan-700" size={26} />
            <h2 className="text-2xl font-bold">
              Weather-Aware Route Planner
            </h2>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Compare routes using forecast weather, cargo weight,
            and estimated arrival times.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[350px_minmax(0,1fr)]
                        gap-5 items-start">
          {/* Left panel */}
          <aside className="space-y-5">
            <TripForm
              loading={loading}
              onSubmit={handleAnalyze}
            />

            {error && (
              <div
                role="alert"
                className="bg-red-50 border border-red-200
                           rounded-xl p-4 text-sm text-red-800"
              >
                <div className="flex items-center gap-2 font-semibold">
                  <AlertTriangle size={18} />
                  Route Analysis Failed
                </div>
                <p className="mt-2">{error}</p>
              </div>
            )}

            {result && (
              <section className="space-y-3">
                <h3 className="font-bold text-lg">
                  Route Alternatives ({result.route_count})
                </h3>

                {result.message && (
                  <p className="text-xs bg-amber-50 border border-amber-200
                                rounded-lg p-3 text-amber-800">
                    {result.message}
                  </p>
                )}

                {result.routes.map((route, index) => (
                  <RouteCard
                    key={route.id}
                    route={route}
                    selected={selectedRouteId === route.id}
                    recommended={
                      result.recommended_route_id === route.id
                    }
                    color={routeColors[index % routeColors.length]}
                    onClick={() => setSelectedRouteId(route.id)}
                  />
                ))}
              </section>
            )}
          </aside>

          {/* Main content */}
          <div className="space-y-5 min-w-0">
            {result && <RouteSummary data={result} />}

            <section className="bg-white border border-slate-200
                                rounded-xl p-4 shadow-sm">
              <div className="flex flex-wrap items-center
                              justify-between gap-3 mb-4">
                <div className="flex items-center gap-2">
                  <MapPinned size={20} className="text-cyan-700" />
                  <h3 className="font-bold text-lg">
                    Interactive Route Map
                  </h3>
                </div>

                {result && (
                  <span className="text-xs text-slate-500">
                    {result.route_count} route(s) available
                  </span>
                )}
              </div>

              <RouteMap
                routes={result?.routes ?? []}
                selectedRouteId={selectedRouteId}
                origin={result?.origin}
                destination={result?.destination}
                onSelectRoute={setSelectedRouteId}
              />

              <div className="mt-4">
                <RiskLegend />
              </div>
            </section>

            {!result && (
              <div className="bg-white border border-slate-200
                              rounded-xl p-6 text-center">
                <CloudSun className="h-10 w-10 text-cyan-600 mx-auto" />
                <h3 className="font-semibold text-lg mt-3">
                  Start Your Route Analysis
                </h3>
                <p className="text-sm text-slate-500 mt-2">
                  Enter your trip details and analyze routes to
                  view weather risks at individual checkpoints.
                </p>
              </div>
            )}

            <div className="text-xs text-slate-500 text-center pb-4">
              Route geometry is based on general driving directions.
              Weather forecasts and risk scores are planning
              estimates, not guaranteed road safety conditions.
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
