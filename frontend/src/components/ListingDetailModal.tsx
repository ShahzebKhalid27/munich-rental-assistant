"use client";

import { useEffect, useState } from "react";
import type { Listing } from "@/lib/api";

interface ListingDetailModalProps {
  listing: Listing;
  onClose: () => void;
}

export default function ListingDetailModal({ listing, onClose }: ListingDetailModalProps) {
  const [imgIndex, setImgIndex] = useState(0);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const images = listing.image_urls?.length ? listing.image_urls : [];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white shadow-2xl">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors"
        >
          ✕
        </button>

        {/* Image carousel */}
        {images.length > 0 ? (
          <div className="relative h-64 bg-gray-100">
            <img
              src={images[imgIndex]}
              alt={listing.title}
              className="h-full w-full object-cover"
              onError={() => {/* fallback handled by placeholder */}}
            />
            {images.length > 1 && (
              <>
                <button
                  onClick={() => setImgIndex((i) => Math.max(0, i - 1))}
                  className="absolute left-2 top-1/2 -translate-y-1/2 rounded-full bg-black/50 px-2 py-1 text-white hover:bg-black/70"
                >
                  ‹
                </button>
                <button
                  onClick={() => setImgIndex((i) => Math.min(images.length - 1, i + 1))}
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-black/50 px-2 py-1 text-white hover:bg-black/70"
                >
                  ›
                </button>
                <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1.5">
                  {images.map((_, i) => (
                    <button
                      key={i}
                      onClick={() => setImgIndex(i)}
                      className={`h-1.5 w-1.5 rounded-full transition-colors ${i === imgIndex ? "bg-white" : "bg-white/50"}`}
                    />
                  ))}
                </div>
              </>
            )}
          </div>
        ) : (
          <div className="flex h-48 w-full items-center justify-center bg-gray-100 text-gray-400 text-sm">
            Kein Bild verfügbar
          </div>
        )}

        {/* Content */}
        <div className="p-6">
          {/* Price + Size */}
          <div className="mb-2 flex items-baseline justify-between">
            <span className="text-3xl font-bold text-gray-900">
              {listing.price_total != null ? `${listing.price_total.toLocaleString("de-DE")} €` : "Preis auf Anfrage"}
            </span>
            {listing.size_sqm && (
              <span className="text-base text-gray-500">{listing.size_sqm} m²</span>
            )}
          </div>

          {/* Title + Source */}
          <div className="mb-4 flex items-start justify-between gap-3">
            <h2 className="text-lg font-semibold text-gray-800 leading-tight">{listing.title}</h2>
            <span className="flex-shrink-0 rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700">
              {listing.source === "wg_gesucht" ? "WG-Gesucht" : listing.source}
            </span>
          </div>

          {/* Location + Available */}
          <div className="mb-4 space-y-1">
            {listing.district && (
              <p className="text-sm text-gray-600">📍 {listing.district}{listing.city ? `, ${listing.city}` : ""}</p>
            )}
            {listing.available_from && (
              <p className="text-sm text-emerald-600 font-medium">
                ✅ Verfugbar: {listing.available_from ? `ab ${new Date(listing.available_from).toLocaleDateString("de-DE")}` : "sofort"}
              </p>
            )}
          </div>

          {/* Description */}
          {listing.description && (
            <div className="mb-5">
              <h3 className="mb-1.5 text-sm font-semibold text-gray-700">Beschreibung</h3>
              <p className="text-sm text-gray-600 whitespace-pre-wrap leading-relaxed">
                {listing.description}
              </p>
            </div>
          )}

          {/* External link */}
          {listing.url && (
            <a
              href={listing.url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
            >
              Auf {listing.source === "wg_gesucht" ? "WG-Gesucht" : "Portal"} ansehen
              <span className="text-xs opacity-70">↗</span>
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
