
import { api } from "./api";
import type { CorridorForecast } from "../types/corridor";

export async function fetchCorridorForecast(
  coordinates: [number, number][],
  loadWeight: number
): Promise<CorridorForecast> {
  const response = await api.post<CorridorForecast>(
    "/weather/corridor/",
    {
      coordinates,
      load_weight: loadWeight,
    },
    { timeout: 120000 }
  );

  return response.data;
}
