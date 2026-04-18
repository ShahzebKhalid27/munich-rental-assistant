"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchListings, triggerScrape, type Listing, type FilterState } from "@/lib/api";
import ListingCard from "@/components/ListingCard";
import FilterSidebar from "@/components/FilterSidebar";
import ListingDetailModal from "@/components/ListingDetailModal";

export default function ListingGrid() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [scrapeLoading, setScrapeLoading] = useState(false);
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);
  const [filters, setFilters] = useState<FilterState>({
    city: "München",
    district: "",
    min_price: "",
    max_price: "",
    min_size: "",
    max_size: "",
    wg_only: false,
  });

  const loadListings = useCallback(async (f: FilterState) => {
    setLoading(true);
    try {
      const data = await fetchListings({
        city: f.city || undefined,
        district: f.district || undefined,
        min_price: f.min_price ? parseFloat(f.min_price) : undefined,
        max_price: f.max_price ? parseFloat(f.max_price) : undefined,
        min_size: f.min_size ? parseFloat(f.min_size) : undefined,
        max_size: f.max_size ? parseFloat(f.max_size) : undefined,
        wg_only: f.wg_only || undefined,
      });
      setListings(data.results);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to load listings:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    void loadListings(filters);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleFilterApply = (newFilters: FilterState) => {
    setFilters(newFilters);
    void loadListings(newFilters);
  };

  const handleScrape = async (source: "wg_gesucht" | "immoscout24") => {
    setScrapeLoading(true);
    try {
      await triggerScrape({
        source: source,
        city: filters.city,
        district: filters.district || undefined,
        max_price: filters.max_price ? parseFloat(filters.max_price) : undefined,
        min_size_sqm: filters.min_size ? parseFloat(filters.min_size) : undefined,
        pages: 2,
      });
      // Refresh after background job finishes
      setTimeout(() => {
        void loadListings(filters);
      }, 8000);
    } catch (err) {
      console.error("Scrape failed:", err);
    } finally {
      setScrapeLoading(false);
    }
  };

  return (
    <>
      {/* Detail modal */}
      {selectedListing && (
        <ListingDetailModal
          listing={selectedListing}
          onClose={() => setSelectedListing(null)}
        />
      )}

      <div className="flex gap-6">
        {/* Sidebar */}
        <FilterSidebar
          onApply={handleFilterApply}
          onScrape={handleScrape}
          isScraping={scrapeLoading}
        />

        {/* Main content */}
        <main className="flex-1 min-w-0">
          {/* Results header */}
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                {loading ? "Lädt..." : `${total} Inserate`}
              </h2>
              {!loading && total > 0 && (
                <p className="text-sm text-gray-500">
                  {filters.district ? `📍 ${filters.district}` : "Alle Stadtteile"}
                  {filters.max_price ? ` · bis ${filters.max_price} €` : ""}
                  {filters.wg_only ? " · nur WG-Zimmer" : ""}
                  {filters.min_size ? ` · ab ${filters.min_size} m²` : ""}
                </p>
              )}
            </div>

            {scrapeLoading && (
              <span className="flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-sm text-emerald-700">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75 animate-ping"></span>
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
                </span>
                Scraping läuft...
              </span>
            )}
          </div>

          {/* Loading skeleton */}
          {loading && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="animate-pulse rounded-xl border border-gray-200 bg-gray-50">
                  <div className="h-48 bg-gray-200 rounded-t-xl" />
                  <div className="p-4 space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-3/4" />
                    <div className="h-3 bg-gray-200 rounded w-1/2" />
                    <div className="h-3 bg-gray-200 rounded w-5/6" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Empty state */}
          {!loading && listings.length === 0 && (
            <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-gray-200 py-24 text-center">
              <span className="mb-3 text-4xl">🏠</span>
              <h3 className="text-lg font-semibold text-gray-700">Keine Inserate gefunden</h3>
              <p className="mt-1 text-sm text-gray-400 max-w-xs">
                Versuche andere Filter oder starte einen neuen Scan über das Portal-Scraping.
              </p>
            </div>
          )}

          {/* Listing grid */}
          {!loading && listings.length > 0 && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {listings.map((listing) => (
                <button
                  key={listing.id}
                  onClick={() => setSelectedListing(listing)}
                  className="cursor-pointer text-left w-full bg-transparent border-none p-0"
                >
                  <ListingCard listing={listing} />
                </button>
              ))}
            </div>
          )}

          {/* Pagination placeholder */}
          {!loading && total > 20 && (
            <div className="mt-6 flex justify-center">
              <p className="text-sm text-gray-400">
                Zeige 20 von {total} — Pagination coming soon
              </p>
            </div>
          )}
        </main>
      </div>
    </>
  );
}
