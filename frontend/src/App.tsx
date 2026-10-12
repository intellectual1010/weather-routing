
import { useEffect, useState, useRef } from "react";
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

import ForecastSlider from "./components/ForecastSlider";
import { fetchCorridorForecast } from "./services/weather";
import type { CorridorForecast } from "./types/corridor";

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

  const [forecastHour, setForecastHour] = useState(0);
  const [showCorridor, setShowCorridor] = useState(false);

  const [corridorForecast, setCorridorForecast] =
    useState<CorridorForecast | null>(null);

  const [corridorLoading, setCorridorLoading] = useState(false);
  const [corridorError, setCorridorError] =
    useState<string | null>(null);

  const corridorCache = useRef(
    new Map<string, {
      data: CorridorForecast;
      fetchedAt: number;
    }>()
  );

  useEffect(() => {
    checkBackendHealth()
      .then(() => setConnected(true))
      .catch(() => setConnected(false));
  }, []);


  useEffect(() => {
    if (!result || !selectedRouteId || !showCorridor) {
      setCorridorForecast(null);
      setCorridorLoading(false);
      return;
    }

    const route = result.routes.find(
      (item) => item.id === selectedRouteId
    );

    if (!route) return;

    const coordinates = route.geometry.coordinates;
    const cacheKey = [
      result.origin.name,
      result.destination.name,
      route.id,
      result.load_weight,
      result.departure_time,
    ].join("|");

    const cached = corridorCache.current.get(cacheKey);
    const maxAgeMs = 15 * 60 * 1000;

    if (cached && Date.now() - cached.fetchedAt < maxAgeMs) {
      setCorridorForecast(cached.data);
      setCorridorLoading(false);
      setCorridorError(null);
      return;
    }

    let cancelled = false;

    setCorridorForecast(null);
    setCorridorLoading(true);
    setCorridorError(null);

    fetchCorridorForecast(
      coordinates,
      result.load_weight
    )
      .then((data) => {
        if (cancelled) return;

        corridorCache.current.set(cacheKey, {
          data,
          fetchedAt: Date.now(),
        });

        setCorridorForecast(data);
      })
      .catch((error) => {
        if (cancelled) return;
        setCorridorError(getApiError(error));
      })
      .finally(() => {
        if (!cancelled) setCorridorLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [result, selectedRouteId, showCorridor]);

  async function handleAnalyze(trip: TripRequest) {
    setLoading(true);
    setShowCorridor(false);
    setForecastHour(0);
    setCorridorForecast(null);
    setCorridorError(null);
    corridorCache.current.clear();
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
                Weather Routing
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

              {result && (
                <div className="flex flex-wrap items-center gap-2 mb-4">
                  <button
                    type="button"
                    onClick={() => setShowCorridor(false)}
                    className={`rounded-lg px-4 py-2 text-sm font-medium ${
                      !showCorridor
                        ? "bg-cyan-700 text-white"
                        : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    ETA Checkpoint Risks
                  </button>

                  <button
                    type="button"
                    onClick={() => setShowCorridor(true)}
                    className={`rounded-lg px-4 py-2 text-sm font-medium ${
                      showCorridor
                        ? "bg-cyan-700 text-white"
                        : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    48h Weather Heatmap
                  </button>
                </div>
              )}

              <RouteMap
                routes={result?.routes ?? []}
                selectedRouteId={selectedRouteId}
                origin={result?.origin}
                destination={result?.destination}
                onSelectRoute={setSelectedRouteId}
                corridorForecast={corridorForecast}
                forecastHour={forecastHour}
                showCorridor={showCorridor}
              />

              <div className="mt-4">
                <RiskLegend />
              </div>
            </section>

            {result && showCorridor && (
              <div className="space-y-3">
                {corridorLoading && (
                  <div
                    role="status"
                    className="rounded-xl border bg-white p-4 text-sm
                              text-slate-600"
                  >
                    Loading 48-hour corridor weather...
                  </div>
                )}

                {corridorError && (
                  <div
                    role="alert"
                    className="rounded-xl border border-red-200
                              bg-red-50 p-4 text-sm text-red-700"
                  >
                    {corridorError}
                  </div>
                )}

                {corridorForecast && (
                  <ForecastSlider
                    hour={forecastHour}
                    onChange={setForecastHour}
                    referenceTime={corridorForecast.reference_time}
                  />
                )}
              </div>
            )}

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
