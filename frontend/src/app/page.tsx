import Navbar from "@/components/Navbar";
import ListingGrid from "@/components/ListingGrid";

export const dynamic = "force-dynamic"; // always fetch fresh data

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="mx-auto max-w-7xl px-4 py-6">
        {/* Hero */}
        <div className="mb-6 rounded-2xl bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-5 text-white shadow-lg">
          <h1 className="text-2xl font-bold leading-tight">
            Munich Rental Assistant
          </h1>
          <p className="mt-1 text-sm text-blue-100">
            WG-Zimmer & Wohnungen in München — automatisch gescannt, intelligent gefiltert.
          </p>
        </div>

        {/* Dashboard */}
        <ListingGrid />
      </div>
    </div>
  );
}
