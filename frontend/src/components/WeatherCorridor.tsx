
import { memo } from "react";
import {
  CircleMarker,
  Popup,
} from "react-leaflet";

import type { CorridorForecast } from "../types/corridor";

import {
  riskColors,
  riskLabels,
  formatDateTime,
} from "../utils/risk";

interface Props {
  data: CorridorForecast;
  hour: number;
}

function WeatherCorridorComponent({ data, hour }: Props) {
  return (
    <>
      {data.points.map((point) => {
        const forecast = point.hours[hour];

        if (!forecast) return null;

        const color = riskColors[forecast.risk.level];
        const center: [number, number] = [
          point.latitude,
          point.longitude,
        ];

        return (
          <CircleMarker
            key={point.index}
            center={center}
            radius={16}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity: 0.14,
              opacity: 0.25,
              weight: 1,
            }}
          >
            <CircleMarker
              center={center}
              radius={6}
              pathOptions={{
                color: "#ffffff",
                fillColor: color,
                fillOpacity: 0.95,
                weight: 1,
              }}
            >
              <Popup minWidth={210}>
                <div className="space-y-2 text-sm">
                  <strong>
                    Corridor Point {point.index + 1}
                  </strong>

                  <p>
                    Route progress:{" "}
                    {point.progress_percent.toFixed(1)}%
                  </p>

                  <p>
                    Forecast: {formatDateTime(forecast.time)}
                  </p>

                  <p>
                    Risk:{" "}
                    <strong style={{ color }}>
                      {riskLabels[forecast.risk.level]}
                    </strong>
                  </p>

                  {forecast.weather ? (
                    <>
                      <p>
                        Wind:{" "}
                        {forecast.weather.wind_mph.toFixed(1)} mph
                      </p>
                      <p>
                        Rain:{" "}
                        {forecast.weather.rain_in_hr.toFixed(2)} in/hr
                      </p>
                      <p>
                        Snow:{" "}
                        {forecast.weather.snow_in_hr.toFixed(2)} in/hr
                      </p>
                    </>
                  ) : (
                    <p>Forecast unavailable</p>
                  )}

                  <p className="text-xs text-slate-500">
                    {forecast.risk.reason}
                  </p>
                </div>
              </Popup>
            </CircleMarker>
          </CircleMarker>
        );
      })}
    </>
  );
}

export default memo(WeatherCorridorComponent);
