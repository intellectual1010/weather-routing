# Weather Routing

A full-stack weather-aware road-route planning application built for the Spotter AI Full Stack Developer assessment.

**Live demo:** https://weather-routing-omega.vercel.app/  
**Backend:** https://weather-routing.onrender.com/api/health/  
**GitHub:** https://github.com/intellectual1010/weather-routing

## Overview

The application compares available driving routes using forecast weather at sampled checkpoints, an estimated arrival time for each checkpoint, cargo load weight, and route travel duration. It also displays a 0–48-hour weather-risk corridor visualization.

> **Important:** This is a planning prototype, not a certified truck navigation or road-safety system. The current Mapbox `driving` profile does not enforce commercial-vehicle height, axle, bridge, or weight restrictions. Risk estimates are sampled approximations, not guarantees of safe travel.

## Tech stack

- **Frontend:** React, TypeScript, Vite, Tailwind CSS, React-Leaflet, Leaflet
- **Backend:** Python, Django, Django REST Framework
- **Directions:** Mapbox Directions API (`driving` profile)
- **Geocoding:** OpenRouteService
- **Forecasts:** Open-Meteo hourly weather forecast
- **Hosting:** Vercel (frontend), Render (backend)

## Features

- Enter origin, destination, departure date/time, and load weight in pounds.
- Request up to three **distinct routes** returned by the routing provider. The provider may return fewer, which the UI reports transparently.
- Sample route geometry at 10-, 25-, or 50-mile intervals, including origin and destination.
- Estimate checkpoint arrival times and retrieve hourly weather near those ETAs.
- Classify wind, rain, and snow risk and apply load-sensitive wind overrides.
- Estimate miles in each risk category and rank eligible routes.
- Display routes, selected-route checkpoints, ETA/weather popups, and comparison summaries on a Leaflet map.
- Display a 0–48-hour forecast corridor overlay. The time slider visualizes conditions at a chosen forecast hour; **route ranking remains based on checkpoint ETA forecasts**.
- Treat missing forecast information as `unknown`, not as low risk.

## Weather risk rules

| Risk | Wind (mph) | Rain (in/hr) | Snow (in/hr) |
|---|---:|---:|---:|
| Low | <25 | <0.10 | <0.5 |
| Moderate | 25–<35 | 0.10–<0.25 | 0.5–<1.0 |
| High | 35–<45 | 0.25–<0.50 | 1.0–<2.0 |
| Severe | 45–<55 | 0.50–1.00 | 2.0–3.0 |
| No Travel | >=55 | >1.00 | >3.0 |

**Load overrides:** Wind >=55 mph is No Travel for any load. Wind from 45 to <55 mph with load >30,000 lb is No Travel. Wind from 35 to <45 mph with load >40,000 lb is Severe. The checkpoint's overall risk is the highest resulting weather-factor risk.

## Route recommendation

Among routes with complete weather coverage and no sampled No Travel segment, rank in this order:

1. Fewest Severe miles
2. Fewest High miles
3. Lowest mileage-weighted average risk
4. Shortest travel time

If no eligible route exists, return no recommendation and explain why. Risk mileage is estimated using the road distance represented by each checkpoint.

## Architecture

```text
React / TypeScript (Vercel)
   |
   | REST requests
   v
Django REST Framework (Render)
   |-- OpenRouteService -> geocoding
   |-- Mapbox Directions -> road route geometries, distances, duration
   |-- Checkpoint service -> mile markers, ETA
   |-- Open-Meteo -> hourly forecast near checkpoint ETA
   |-- Risk + recommendation services
   `-- Corridor forecast service -> 0–48-hour map overlay
```

## Local setup (Ubuntu / Linux)

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # If the template exists; otherwise create .env manually
python manage.py migrate
python manage.py runserver
```

Backend environment variables (in `backend/.env`):

```dotenv
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=replace_with_a_generated_secret
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ORS_API_KEY=your_ors_key
MAPBOX_ACCESS_TOKEN=your_mapbox_token
DJANGO_HSTS_SECONDS=0
```

Generate a Django secret key with:

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

Then:

```bash
npm run dev
```

Open http://localhost:5173/.

## API endpoints

- `GET /api/health/` — backend health check.
- `GET /api/geocode/?q=Chicago` — geocode a location name.
- `POST /api/routes/` — retrieve available routes with checkpoints, weather, risk summaries, and recommendation.
- `POST /api/weather/corridor/` — obtain 49 hourly forecasts for sampled locations along a supplied route geometry.

Example routing request:

```json
{
  "origin": "Chicago, Illinois",
  "destination": "Atlanta, Georgia",
  "departure_time": "2026-10-15T13:00:00Z",
  "load_weight": 42000,
  "checkpoint_interval": 25
}
```

**Note:** Use an actual future departure within the weather forecast window for live testing. The timestamp above is an example and may no longer be in the future.

## Tests

```bash
cd backend
source venv/bin/activate
python manage.py check
python manage.py test routing -v 2

cd ../frontend
npm run build
```

Manually verify (a) the returned route count, (b) checkpoint spacing and increasing ETAs, (c) threshold boundaries and load overrides, (d) that risk-mile totals approximately match route miles, (e) the recommendation priority order, and (f) the slider's 0h and 48h states.

## Deployment

- **Render:** Set the service root directory to `backend`, build command to `./build.sh`, start command to `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`, and configure secret environment variables. Set `DJANGO_ALLOWED_HOSTS` to the backend hostname and `CORS_ALLOWED_ORIGINS` to the exact frontend origin without a trailing slash.
- **Vercel:** Set root directory to `frontend`, framework to Vite, and `VITE_API_BASE_URL=https://weather-routing.onrender.com/api`. Redeploy after changing Vite environment variables.

Never commit `.env` files or API credentials.

## Known limitations / future enhancements

- The routing provider may return one or two alternatives rather than three; these are reported instead of being duplicated or invented.
- The Mapbox `driving` profile is general-purpose road routing, not guaranteed HGV/truck-compliant directions.
- Checkpoint ETA is derived proportionally from route distance/duration and does not account for mandatory rest breaks or time-varying traffic.
- Weather forecasts are hourly and sampled spatially; weather boundaries between checkpoints may be missed. The corridor layer uses sampled point halos rather than a continuous raster field.
- The trip form interprets user-entered departure time in the browser's timezone; selecting the origin's timezone would improve accuracy for remote dispatchers.
- Open-Meteo availability, forecast horizon, provider request limits, and public hosting cold starts may affect long-distance demonstrations.
- Local-memory caching is process-local; a shared cache would improve multi-worker production behavior.
