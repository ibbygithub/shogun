export interface ItineraryLeg {
  id: number;
  leg_type: string;
  city: string | null;
  date_start: string | null;
  date_end: string | null;
  title: string;
  description: string | null;
  address_en: string | null;
  address_ja: string | null;
  confirmation_number: string | null;
  notes: string | null;
  status: string | null;
}

export interface Poi {
  id: number;
  city: string | null;
  name_en: string;
  name_ja: string | null;
  category: string | null;
  tags: string[] | null;
  description: string | null;
  crowd_notes: string | null;
  best_time: string | null;
  map_url: string | null;
  source: string | null;
  // Added by API enrichment (Agent A) — may be null until enriched
  lat?: number | null;
  lng?: number | null;
}

export interface WishlistItem {
  id: number;
  requested_by: number;
  city: string | null;
  description: string;
  ai_research: string | null;
  status: "pending" | "approved" | "rejected";
  reviewed_by: number | null;
  reviewed_at: string | null;
  itinerary_note: string | null;
  created_utc: string;
}

export interface WeatherCurrent {
  temperature_2m: number;
  weather_code: number;
  wind_speed_10m: number;
}

export interface WeatherDay {
  date: string;
  weather_code: number;
  temperature_max: number;
  temperature_min: number;
  precipitation_sum: number;
}

export interface WeatherResponse {
  city: string;
  current: WeatherCurrent;
  forecast_3day: WeatherDay[];
}

export interface BlossomEntry {
  city: string;
  spot: string;
  status: "not_started" | "early" | "peak" | "late" | "finished";
  peak_date: string;
  notes: string | null;
}

export interface Reminder {
  type: string;
  icon: string;
  text: string;
}

export interface RemindersResponse {
  date_reminders: Reminder[];
  global_reminders: Reminder[];
}

export interface DashboardStatus {
  current_city: string | null;
  trip_day: number | null;
  total_days: number;
  departure_date: string;
  shogun_health: string;
  pending_wishlist_count: number;
}

export interface ServiceHealth {
  name: string;
  status: string;
  latency_ms: number | null;
  last_check: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: number | null;
}

export interface UpcomingLeg {
  leg: number;
  title: string;
  city: string | null;
  date: string;
  notes: string | null;
}

export interface CalendarData {
  date: string;
  event: string | null;
  note: string | null;
  is_holiday: boolean;
  error?: string;
  // Pre-trip fields returned when no active itinerary leg today
  days_until_trip?: number;
  upcoming_legs?: UpcomingLeg[];
}

export interface BudgetItem {
  id: number;
  trip_date: string | null;
  category: string;
  description: string;
  amount_jpy: number;
  created_utc: string;
}
