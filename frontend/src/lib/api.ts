const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Listing {
  id: number;
  external_id: string | null;
  source: string;
  title: string;
  description: string;
  price_total: number | null;
  price_cold: number | null;
  size_sqm: number | null;
  address: string | null;
  city: string | null;
  district: string | null;
  latitude: number | null;
  longitude: number | null;
  available_from: string | null;
  image_urls: string[];
  created_at: string;
  url?: string;
}

export interface ListingsResponse {
  results: Listing[];
  total: number;
  offset: number;
  limit: number;
}

export interface Filters {
  city?: string;
  district?: string;
  min_price?: number;
  max_price?: number;
  min_size?: number;
  max_size?: number;
  wg_only?: boolean;
  limit?: number;
  offset?: number;
}

export interface FilterState {
  city: string;
  district: string;
  min_price: string;
  max_price: string;
  min_size: string;
  max_size: string;
  wg_only: boolean;
}

export async function fetchListings(filters: Filters = {}): Promise<ListingsResponse> {
  const params = new URLSearchParams();
  if (filters.city) params.set("city", filters.city);
  if (filters.district) params.set("district", filters.district);
  if (filters.min_price != null) params.set("min_price", String(filters.min_price));
  if (filters.max_price != null) params.set("max_price", String(filters.max_price));
  if (filters.min_size != null) params.set("min_size", String(filters.min_size));
  if (filters.max_size != null) params.set("max_size", String(filters.max_size));
  if (filters.wg_only) params.set("wg_only", "true");
  if (filters.limit != null) params.set("limit", String(filters.limit));
  if (filters.offset != null) params.set("offset", String(filters.offset));

  const res = await fetch(`${API_BASE}/api/v1/listings/${params ? "?" + params : ""}`, {
    next: { revalidate: 30 }, // ISR: revalidate every 30s
  });

  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function triggerScrape(params: {
  source?: "wg_gesucht" | "immoscout24";
  city?: string;
  district?: string;
  max_price?: number;
  min_size_sqm?: number;
  pages?: number;
}): Promise<{ status: string; message: string }> {
  const searchParams = new URLSearchParams();
  if (params.source) searchParams.set("source", params.source);
  if (params.city) searchParams.set("city", params.city);
  if (params.district) searchParams.set("district", params.district);
  if (params.max_price != null) searchParams.set("max_price", String(params.max_price));
  if (params.min_size_sqm != null) searchParams.set("min_size_sqm", String(params.min_size_sqm));
  if (params.pages != null) searchParams.set("pages", String(params.pages));

  const res = await fetch(
    `${API_BASE}/api/v1/listings/scrape?${searchParams}`,
    { method: "POST" },
  );

  if (!res.ok) throw new Error(`Scrape API error: ${res.status}`);
  return res.json();
}
