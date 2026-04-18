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
  onScrape: (source: "wg_gesucht" | "immoscout24") => void;
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

const SCRAPE_SOURCES = [
  { value: "wg_gesucht", label: "WG-Gesucht", desc: "WG-Zimmer & möblierte Wohnungen" },
  { value: "immoscout24", label: "ImmoScout24", desc: "Wohnungen & Häuser" },
] as const;

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
  const [scrapeSource, setScrapeSource] = useState<"wg_gesucht" | "immoscout24">("wg_gesucht");

  const update = (key: keyof FilterState, value: string | boolean) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <aside className="w-64 flex-shrink-0 space-y-5">
      {/* ── Filter ── */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 shadow-sm">
        <h2 className="mb-4 text-base font-semibold text-gray-900 dark:text-white">🔍 Filter</h2>

        {/* WG Only */}
        <div className="mb-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.wg_only}
              onChange={(e) => update("wg_only", e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Nur WG-Zimmer</span>
          </label>
        </div>

        {/* District */}
        <div className="mb-4">
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Stadtviertel</label>
          <select
            value={filters.district}
            onChange={(e) => update("district", e.target.value)}
            className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">Alle Viertel</option>
            {MUNICH_DISTRICTS.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        {/* Price Range */}
        <div className="mb-4">
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Kaltmiete (€)</label>
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Min"
              value={filters.min_price}
              onChange={(e) => update("min_price", e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <input
              type="number"
              placeholder="Max"
              value={filters.max_price}
              onChange={(e) => update("max_price", e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Size Range */}
        <div className="mb-4">
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Fläche (m²)</label>
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Min"
              value={filters.min_size}
              onChange={(e) => update("min_size", e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <input
              type="number"
              placeholder="Max"
              value={filters.max_size}
              onChange={(e) => update("max_size", e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Apply */}
        <button
          onClick={() => onApply(filters)}
          className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
        >
          Anwenden
        </button>
      </div>

      {/* ── Portal-Scraping ── */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 shadow-sm">
        <h3 className="mb-3 text-sm font-semibold text-gray-800 dark:text-white">📡 Portal scannen</h3>

        {/* Source selector */}
        <div className="mb-3 space-y-1.5">
          {SCRAPE_SOURCES.map(({ value, label, desc }) => (
            <label
              key={value}
              className={`flex items-start gap-2.5 rounded-lg border p-2.5 cursor-pointer transition-colors ${
                scrapeSource === value
                  ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                  : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
              }`}
            >
              <input
                type="radio"
                name="scrapeSource"
                value={value}
                checked={scrapeSource === value}
                onChange={() => setScrapeSource(value)}
                className="mt-0.5 h-3.5 w-3.5 accent-blue-600"
              />
              <div>
                <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">{label}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{desc}</p>
              </div>
            </label>
          ))}
        </div>

        <button
          onClick={() => onScrape(scrapeSource)}
          disabled={isScraping}
          className={`w-full rounded-lg px-4 py-2 text-sm font-semibold transition-colors ${
            isScraping
              ? "bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed"
              : "bg-emerald-600 text-white hover:bg-emerald-700"
          }`}
        >
          {isScraping ? "⏳ Läuft..." : "▶️ Jetzt scannen"}
        </button>
      </div>
    </aside>
  );
}
