
import { api } from "./api";
import type { CorridorForecast } from "../types/corridor";

const MAX_COORDINATES = 2000;

/**
 * Reduce the number of route coordinates sent to the
 * corridor weather API.
 *
 * Preserves the first and last point.
 * Used for weather visualization, not road navigation.
 */
export function simplifyRouteCoordinates(
  coordinates: [number, number][],
  maxPoints: number = MAX_COORDINATES
): [number, number][] {
  if (coordinates.length <= maxPoints) {
    return coordinates;
  }

  if (maxPoints < 2) {
    throw new Error("At least two coordinates are required.");
  }

  const result: [number, number][] = [];

  for (let i = 0; i < maxPoints; i++) {
    const index = Math.round(
      (i * (coordinates.length - 1)) / (maxPoints - 1)
    );

    result.push(coordinates[index]);
  }

  return result;
}

/**
 * Fetch 0–48 hour weather forecasts along the route.
 */
export async function fetchCorridorForecast(
  coordinates: [number, number][],
  loadWeight: number
): Promise<CorridorForecast> {
  const simplified = simplifyRouteCoordinates(coordinates);

  const response = await api.post<CorridorForecast>(
    "/weather/corridor/",
    {
      coordinates: simplified,
      load_weight: loadWeight,
    },
    {
      timeout: 120000,
    }
  );

  return response.data;
}
