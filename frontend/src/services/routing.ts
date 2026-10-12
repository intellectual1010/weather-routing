
import axios from "axios";
import { api } from "./api";

import type {
  RouteResponse,
  TripRequest,
} from "../types/routing";

export async function analyzeRoutes(
  trip: TripRequest,
  signal?: AbortSignal
): Promise<RouteResponse> {
  const response = await api.post<RouteResponse>(
    "/routes/",
    trip,
    { signal, timeout: 120000 }
  );

  return response.data;
}

export function getApiError(error: unknown): string {
  if (axios.isCancel(error)) {
    return "Request cancelled.";
  }

  if (axios.isAxiosError(error)) {
    const details = error.response?.data;

    if (typeof details?.error === "string") {
      return details.error;
    }

    if (details && typeof details === "object") {
      const first = Object.entries(details)[0];

      if (first) {
        const value = first[1];
        return `${first[0]}: ${
          Array.isArray(value)
            ? value.join(", ")
            : String(value)
        }`;
      }
    }

    if (error.code === "ECONNABORTED") {
      return "Route analysis timed out. Please try again.";
    }

    return error.message || "Unable to analyze routes.";
  }

  return "An unexpected error occurred.";
}
