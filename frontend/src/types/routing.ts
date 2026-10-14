
export type RiskLevel =
  | "low"
  | "moderate"
  | "high"
  | "severe"
  | "no_travel"
  | "unknown";

export interface Location {
  name: string;
  coordinates: [number, number];
  latitude?: number;
  longitude?: number;
}

export interface Weather {
  wind_mph: number;
  rain_in_hr: number;
  snow_in_hr: number;
  forecast_time: string;
  source: string;
}

export interface CheckpointRisk {
  level: RiskLevel;
  score: number | null;
  reason: string;
  factors: Record<string, RiskLevel>;
}

export interface Checkpoint {
  id: string;
  index: number;
  mile_marker: number;
  latitude: number;
  longitude: number;
  coordinates: [number, number];
  eta: string;
  elapsed_minutes: number;
  progress_percent: number;
  represented_miles: number;
  weather: Weather | null;
  risk: CheckpointRisk;
}

export interface RiskSummary {
  low_miles: number;
  moderate_miles: number;
  high_miles: number;
  severe_miles: number;
  no_travel_miles: number;
  unknown_miles: number;
  average_risk: number | null;
  highest_risk: RiskLevel;
  forecast_complete: boolean;
  safe_to_recommend: boolean;
}

export interface RouteOption {
  id: string;
  name: string;
  distance_miles: number;
  distance_meters: number;
  duration_seconds: number;
  duration_minutes: number;
  duration_hours: number;
  geometry: {
    type: "LineString";
    coordinates: [number, number][];
  };
  provider: string;
  profile: string;
  checkpoints: Checkpoint[];
  checkpoint_count: number;
  risk_summary: RiskSummary;
}

export interface TripRequest {
  origin: string;
  destination: string;
  departure_time: string;
  load_weight: number;
  checkpoint_interval: 10 | 25 | 50;
}

export interface RouteResponse {
  origin: Location;
  destination: Location;
  departure_time: string;
  load_weight: number;
  checkpoint_interval: number;
  routing_provider: string;
  weather_provider: string;
  routes: RouteOption[];
  route_count: number;
  has_three_routes: boolean;
  message: string | null;
  recommended_route_id: string | null;
  recommendation_status: string;
  recommendation_reason: string;
}
