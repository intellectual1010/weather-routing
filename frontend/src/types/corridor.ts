import type { CheckpointRisk, Weather } from "./routing";

export interface ForecastHour {
  offset: number;
  time: string;
  weather: Weather | null;
  risk: CheckpointRisk;
}

export interface CorridorPoint {
  index: number;
  latitude: number;
  longitude: number;
  progress_percent: number;
  hours: ForecastHour[];
}

export interface CorridorForecast {
  reference_time: string;
  sample_count: number;
  hour_count: number;
  points: CorridorPoint[];
}