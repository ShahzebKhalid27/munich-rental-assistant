import Image from "next/image";
import type { Listing } from "@/lib/api";

interface ListingCardProps {
  listing: Listing;
}

function formatPrice(price: number | null): string {
  if (price == null) return "Preis auf Anfrage";
  return `${price.toLocaleString("de-DE")} €`;
}

function formatSize(size: number | null): string {
  if (size == null) return "";
  return `${size.toFixed(1)} m²`;
}

function timeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 60) return `vor ${diffMin} Min`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `vor ${diffH} h`;
  const diffD = Math.floor(diffH / 24);
  return `vor ${diffD} T`;
}

const SOURCE_LABELS: Record<string, string> = {
  wg_gesucht: "WG-Gesucht",
  immoscout24: "ImmoScout",
  ebay_kleinanzeigen: "eBay KL",
};

export default function ListingCard({ listing }: ListingCardProps) {
  const imgSrc =
    listing.image_urls && listing.image_urls[0]
      ? listing.image_urls[0]
      : "https://placehold.co/600x400/png?text=Kein+Bild";

  const sourceLabel = SOURCE_LABELS[listing.source] ?? listing.source;

  return (
    <div className="group relative flex flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm transition-all hover:shadow-md">
      {/* Image */}
      <div className="relative h-48 w-full overflow-hidden bg-gray-100">
        <Image
          src={imgSrc}
          alt={listing.title}
          fill
          className="object-cover transition-transform duration-300 group-hover:scale-105"
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          unoptimized={!listing.image_urls?.[0]?.startsWith("http")}
        />
        <span className="absolute left-3 top-3 rounded-full bg-black/60 px-2 py-0.5 text-xs font-medium text-white">
          {sourceLabel}
        </span>
        {listing.available_from && (
          <span className="absolute bottom-3 left-3 rounded-full bg-emerald-500/90 px-2 py-0.5 text-xs font-medium text-white">
            Verfügbar
          </span>
        )}
      </div>

      {/* Content */}
      <div className="flex flex-1 flex-col p-4">
        {/* Price + Size */}
        <div className="mb-1 flex items-baseline justify-between">
          <span className="text-xl font-bold text-gray-900">
            {formatPrice(listing.price_total)}
          </span>
          {listing.size_sqm && (
            <span className="text-sm text-gray-500">{formatSize(listing.size_sqm)}</span>
          )}
        </div>

        {/* Title */}
        <h3 className="mb-1 line-clamp-2 text-sm font-semibold text-gray-800">
          {listing.title}
        </h3>

        {/* Location */}
        {listing.district && (
          <p className="mb-2 text-xs text-gray-500">
            📍 {listing.district}
            {listing.city ? `, ${listing.city}` : ""}
          </p>
        )}

        {/* Description snippet */}
        {listing.description && (
          <p className="mb-3 line-clamp-2 text-xs text-gray-600">
            {listing.description}
          </p>
        )}

        {/* Footer */}
        <div className="mt-auto flex items-center justify-between border-t border-gray-100 pt-3">
          <span className="text-xs text-gray-400">
            {timeAgo(listing.created_at)}
          </span>
          {listing.external_id && (
            <span className="font-mono text-xs text-gray-300">#{listing.external_id}</span>
          )}
        </div>
      </div>
    </div>
  );
}
