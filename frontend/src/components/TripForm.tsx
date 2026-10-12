
import { useState } from "react";
import type { FormEvent } from "react";
import { LoaderCircle, MapPin, Truck } from "lucide-react";
import type { TripRequest } from "../types/routing";

interface Props {
  loading: boolean;
  onSubmit: (trip: TripRequest) => void;
}

function initialDeparture(): string {
  const date = new Date(Date.now() + 60 * 60 * 1000);
  const local = new Date(
    date.getTime() - date.getTimezoneOffset() * 60000
  );
  return local.toISOString().slice(0, 16);
}

export default function TripForm({ loading, onSubmit }: Props) {
  const [origin, setOrigin] = useState("Chicago, Illinois");
  const [destination, setDestination] = useState("Atlanta, Georgia");
  const [departure, setDeparture] = useState(initialDeparture);
  const [weight, setWeight] = useState(42000);
  const [interval, setInterval] = useState<10 | 25 | 50>(25);

  const inputClass =
    "w-full rounded-lg border border-slate-200 px-3 py-2.5 " +
    "text-sm text-slate-800 focus:outline-none focus:ring-2 " +
    "focus:ring-cyan-500";

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const date = new Date(departure);

    if (Number.isNaN(date.getTime())) return;

    onSubmit({
      origin: origin.trim(),
      destination: destination.trim(),
      departure_time: date.toISOString(),
      load_weight: weight,
      checkpoint_interval: interval,
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-xl border border-slate-200 p-5 space-y-4"
    >
      <div className="flex items-center gap-2">
        <Truck className="h-5 w-5 text-cyan-600" />
        <h2 className="text-lg font-bold">Plan Your Trip</h2>
      </div>

      <div>
        <label htmlFor="origin" className="block text-sm font-medium mb-1">
          Origin
        </label>
        <div className="relative">
          <MapPin className="absolute left-3 top-3 h-4 w-4 text-green-600" />
          <input
            id="origin"
            className={`${inputClass} pl-9`}
            value={origin}
            maxLength={255}
            onChange={(e) => setOrigin(e.target.value)}
            placeholder="City, State"
            required
          />
        </div>
      </div>

      <div>
        <label htmlFor="destination" className="block text-sm font-medium mb-1">
          Destination
        </label>
        <div className="relative">
          <MapPin className="absolute left-3 top-3 h-4 w-4 text-red-600" />
          <input
            id="destination"
            className={`${inputClass} pl-9`}
            value={destination}
            maxLength={255}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="City, State"
            required
          />
        </div>
      </div>

      <div>
        <label htmlFor="departure" className="block text-sm font-medium mb-1">
          Departure Date & Time
        </label>
        <input
          id="departure"
          type="datetime-local"
          className={inputClass}
          value={departure}
          min={initialDeparture().slice(0, 10) + "T00:00"}
          onChange={(e) => setDeparture(e.target.value)}
          required
        />
        <p className="text-xs text-slate-500 mt-1">
          Uses your browser's local timezone.
        </p>
      </div>

      <div>
        <label htmlFor="weight" className="block text-sm font-medium mb-1">
          Load Weight (lb)
        </label>
        <input
          id="weight"
          type="number"
          min={0}
          max={100000}
          step={1}
          className={inputClass}
          value={weight}
          onChange={(e) => setWeight(Number(e.target.value))}
          required
        />
      </div>

      <fieldset>
        <legend className="block text-sm font-medium mb-2">
          Weather Checkpoint Interval
        </legend>
        <div className="grid grid-cols-3 gap-2">
          {([10, 25, 50] as const).map((value) => (
            <button
              key={value}
              type="button"
              aria-pressed={interval === value}
              onClick={() => setInterval(value)}
              className={`rounded-lg border py-2 text-sm font-medium ${
                interval === value
                  ? "border-cyan-600 bg-cyan-50 text-cyan-700"
                  : "border-slate-200 hover:bg-slate-50"
              }`}
            >
              {value} mi
            </button>
          ))}
        </div>
      </fieldset>

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-cyan-700 hover:bg-cyan-800
                   disabled:opacity-60 text-white font-semibold py-3
                   flex justify-center items-center gap-2"
      >
        {loading ? (
          <>
            <LoaderCircle className="w-4 h-4 animate-spin" />
            Analyzing weather...
          </>
        ) : (
          "Find Safest Routes"
        )}
      </button>
    </form>
  );
}
