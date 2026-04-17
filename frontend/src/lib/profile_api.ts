export interface SearchProfileResponse {
  id: number;
  user_id: number;
  name: string;
  city: string;
  price_max: number | null;
  price_min: number | null;
  size_min_sqm: number | null;
  size_max_sqm: number | null;
  wg_type: string | null;
  preferred_districts: string | null;
  commute_lat: number | null;
  commute_lng: number | null;
  commute_max_minutes: number | null;
  auto_apply_enabled: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
