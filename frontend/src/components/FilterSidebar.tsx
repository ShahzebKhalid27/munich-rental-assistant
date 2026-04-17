"use client";

import { useState } from "react";

export interface FilterState {
  city: string;
  district: string;
  min_price: string;
  max_price: string;
  min_size: string;
  max_size: string;
  wg_only: boolean;
}

interface FilterSidebarProps {
  onApply: (filters: FilterState) => void;
  onScrape: () => void;
  isScraping: boolean;
}

const MUNICH_DISTRICTS = [
  "Allach", "Altstadt", "Au", "Bogenhausen", "Bockhorn",
  "Feldmoching", "Friedenheim", "Giesing", "Hackenviertel",
  "Haderner Stern", "Haidhausen", "Isarvorstadt", "Laim",
  "Lehel", "Maxvorstadt", "Moosach", "Neuhausen",
  "Nymphenburg", "Obermenzing", "Obergiesing", "Pasing",
  "Ramersdorf", "Schwabing", "Schwanthalerhöhe", "Sendling",
  "Thalkirchen", "Theresienstraße", "Untergiesing", "Untermenzing",
  "Westpark",
];

export default function FilterSidebar({ onApply, onScrape, isScraping }: FilterSidebarProps) {
  const [filters, setFilters] = useState<FilterState>({
    city: "München",
    district: "",
    min_price: "",
    max_price: "",
    min_size: "",
    max_size: "",
    wg_only: false,
  });

  const update = (key: keyof FilterState, value: string | boolean) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleApply = () => {
    onApply(filters);
  };

  return (
    <aside className="w-64 flex-shrink-0 space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <h2 className="mb-4 text-base font-semibold text-gray-900">🔍 Filter</h2>

        {/* WG Only */}
        <div className="mb-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.wg_only}
              onChange={(e) => update("wg_only", e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm font-medium text-gray-700">Nur WG-Zimmer</span>
          </label>
        </div>

        {/* District */}
        <div className="mb-4">
          <label className="block text-xs font-medium text-gray-600 mb-1">Stadtviertel</label>
          <select
            value={filters.district}
            onChange={(e) => update("district", e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">Alle Viertel</option>
            {MUNICH_DISTRICTS.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        {/* Price Range */}
        <div className="mb-4">
          <label className="block text-xs font-medium text-gray-600 mb-1">Kaltmiete (€)</label>
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Min"
              value={filters.min_price}
              onChange={(e) => update("min_price", e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <input
              type="number"
              placeholder="Max"
              value={filters.max_price}
              onChange={(e) => update("max_price", e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Size Range */}
        <div className="mb-4">
          <label className="block text-xs font-medium text-gray-600 mb-1">Fläche (m²)</label>
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Min"
              value={filters.min_size}
              onChange={(e) => update("min_size", e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <input
              type="number"
              placeholder="Max"
              value={filters.max_size}
              onChange={(e) => update("max_size", e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Apply button */}
        <button
          onClick={handleApply}
          className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
        >
          Anwenden
        </button>
      </div>

      {/* Scrape trigger */}
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <h3 className="mb-2 text-sm font-semibold text-gray-800">📡 Portal-Scraping</h3>
        <p className="mb-3 text-xs text-gray-500">
          WG-Gesucht neu scannen und Inserate aktualisieren.
        </p>
        <button
          onClick={onScrape}
          disabled={isScraping}
          className={`w-full rounded-lg px-4 py-2 text-sm font-semibold transition-colors ${
            isScraping
              ? "bg-gray-300 text-gray-500 cursor-not-allowed"
              : "bg-emerald-600 text-white hover:bg-emerald-700"
          }`}
        >
          {isScraping ? "⏳ Läuft..." : "▶️ Jetzt scannen"}
        </button>
      </div>
    </aside>
  );
}
