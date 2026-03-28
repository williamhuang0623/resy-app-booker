export type DateStatus = "draft" | "monitoring" | "booked" | "failed" | "cancelled";

export interface HitlistRestaurant {
  id: number;
  venue_id: string;
  name: string;
  location: string;
  cuisine: string;
  resy_url_token: string;
  added_at: string;
}

export interface DateEvent {
  id: number;
  restaurant_id: number;
  restaurant: HitlistRestaurant;
  desired_date_start: string;
  desired_date_end: string;
  desired_time_start: string;
  desired_time_end: string;
  party_size: number;
  status: DateStatus;
  reservation_id: string | null;
  booked_slot: string | null;
  booked_at: string | null;
  resy_notify_id: string | null;
  notes: string;
  created_at: string;
}

export interface VenueResult {
  venue_id: string;
  name: string;
  location: string;
  cuisine: string;
  resy_url_token: string;
}

export interface CreateDatePayload {
  restaurant_id: number;
  desired_date_start: string;
  desired_date_end: string;
  desired_time_start: string;
  desired_time_end: string;
  party_size: number;
  notes: string;
}
