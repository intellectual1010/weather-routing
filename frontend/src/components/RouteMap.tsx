
import { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Polyline,
  CircleMarker,
  Popup,
  useMap,
} from "react-leaflet";
import L from "leaflet";

import "leaflet/dist/leaflet.css";

import type { RouteOption, Location } from "../types/routing";
import {
  riskColors,
  riskLabels,
  routeColors,
  formatDateTime,
} from "../utils/risk";

import WeatherCorridor from "./WeatherCorridor";
import type { CorridorForecast } from "../types/corridor";
import MapLoadingOverlay from "./MapLoadingOverlay";

interface Props {
  routes: RouteOption[];
  selectedRouteId: string | null;
  origin?: Location;
  destination?: Location;
  onSelectRoute: (id: string) => void;
  corridorForecast?: CorridorForecast | null;
  forecastHour?: number;
  showCorridor?: boolean;
  loading?: boolean;
  loadingType?: "routes" | "weather";
}

function toLatLngs(route: RouteOption): L.LatLngTuple[] {
  return route.geometry.coordinates.map(
    ([longitude, latitude]) => [latitude, longitude]
  );
}

function FitRoute({ route }: { route?: RouteOption }) {
  const map = useMap();

  useEffect(() => {
    if (!route || route.geometry.coordinates.length < 2) return;

    const bounds = L.latLngBounds(toLatLngs(route));
    map.fitBounds(bounds, {
      padding: [35, 35],
      maxZoom: 12,
      animate: true,
    });
  }, [map, route]);

  return null;
}

function LocationMarker({
  location,
  color,
  title,
}: {
  location: Location;
  color: string;
  title: string;
}) {
  return (
    <CircleMarker
      center={[location.latitude, location.longitude]}
      radius={9}
      pathOptions={{
        color: "#ffffff",
        fillColor: color,
        fillOpacity: 1,
        weight: 3,
      }}
    >
      <Popup>
        <strong>{title}</strong>
        <p>{location.name}</p>
      </Popup>
    </CircleMarker>
  );
}

function MapInteractionLock({ locked }: { locked: boolean }) {
  const map = useMap();

  useEffect(() => {
    const handlers = [
      map.dragging,
      map.touchZoom,
      map.doubleClickZoom,
      map.scrollWheelZoom,
      map.boxZoom,
      map.keyboard,
    ];

    if (locked) {
      handlers.forEach((handler) => handler.disable());
    } else {
      handlers.forEach((handler) => handler.enable());
    }

    return () => {
      handlers.forEach((handler) => handler.enable());
    };
  }, [map, locked]);

  return null;
}

export default function RouteMap({
  routes,
  selectedRouteId,
  origin,
  destination,
  onSelectRoute,
  corridorForecast = null,
  forecastHour = 0,
  showCorridor = false,
  loading = false,
  loadingType = "routes",
}: Props) {
  const selectedRoute = routes.find(
    (route) => route.id === selectedRouteId
  );

  // Draw non-selected routes first; selected route appears on top.
  const orderedRoutes = [
    ...routes.filter((r) => r.id !== selectedRouteId),
    ...routes.filter((r) => r.id === selectedRouteId),
  ];

  return (
    <div
      className="relative rounded-xl overflow-hidden
                border border-slate-200"
      aria-busy={loading}
    >
      <MapContainer
        center={[39.5, -98.35]}
        zoom={4}
        scrollWheelZoom
        className="h-[520px] w-full z-0"
      >
        <MapInteractionLock locked={loading} />
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />

        <FitRoute route={selectedRoute} />

        {orderedRoutes.map((route) => {
          const index = routes.findIndex((r) => r.id === route.id);
          const selected = selectedRouteId === route.id;

          return (
            <>
              <Polyline
                key={route.id}
                positions={toLatLngs(route)}
                eventHandlers={{
                  click: () => onSelectRoute(route.id),
                }}
                pathOptions={{
                  color: routeColors[index % routeColors.length],
                  weight: selected ? 7 : 4,
                  opacity: selected ? 0.95 : 0.45,
                }}
              />
              {showCorridor && corridorForecast && (
                <WeatherCorridor
                  data={corridorForecast}
                  hour={forecastHour}
                />
              )}
            </>
          );
        })}

        {!showCorridor && selectedRoute?.checkpoints.map((point) => (
          <CircleMarker
            key={point.id}
            center={[point.latitude, point.longitude]}
            radius={6}
            pathOptions={{
              color: "#ffffff",
              weight: 1.5,
              fillColor: riskColors[point.risk.level],
              fillOpacity: 0.95,
            }}
          >
            <Popup minWidth={220}>
              <div className="space-y-2 text-sm">
                <strong className="text-base">
                  Checkpoint {point.index + 1}
                </strong>

                <div>
                  <strong>Mile:</strong>{" "}
                  {point.mile_marker.toFixed(1)}
                </div>

                <div>
                  <strong>ETA:</strong>{" "}
                  {formatDateTime(point.eta)}
                </div>

                <div>
                  <strong>Risk:</strong>{" "}
                  <span
                    style={{
                      color: riskColors[point.risk.level],
                      fontWeight: 700,
                    }}
                  >
                    {riskLabels[point.risk.level]}
                  </span>
                </div>

                {point.weather ? (
                  <>
                    <div>
                      <strong>Wind:</strong>{" "}
                      {point.weather.wind_mph.toFixed(1)} mph
                    </div>

                    <div>
                      <strong>Rain:</strong>{" "}
                      {point.weather.rain_in_hr.toFixed(2)} in/hr
                    </div>

                    <div>
                      <strong>Snow:</strong>{" "}
                      {point.weather.snow_in_hr.toFixed(2)} in/hr
                    </div>
                  </>
                ) : (
                  <div className="text-amber-700">
                    Forecast unavailable.
                  </div>
                )}

                <p className="text-xs text-slate-500">
                  {point.risk.reason}
                </p>
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {origin && (
          <LocationMarker
            location={origin}
            color="#16a34a"
            title="Origin"
          />
        )}

        {destination && (
          <LocationMarker
            location={destination}
            color="#dc2626"
            title="Destination"
          />
        )}
      </MapContainer>
      {loading && (
        <MapLoadingOverlay type={loadingType} />
      )}
    </div>
  );
}
