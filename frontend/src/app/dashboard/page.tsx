"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import Navbar from "@/components/Navbar";
import ListingGrid from "@/components/ListingGrid";

export const dynamic = "force-dynamic";

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
          <p className="text-sm text-gray-500 dark:text-gray-400">Lädt...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <div className="mx-auto max-w-7xl px-4 py-6">
        {/* Header */}
        <div className="mb-6 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-5 text-white shadow-lg">
          <h1 className="text-2xl font-bold leading-tight">
            👋 Willkommen zurück, {user.full_name?.split(" ")[0] ?? user.email.split("@")[0]}
          </h1>
          <p className="mt-1 text-sm text-blue-100">
            Wir zeigen dir die aktuellsten WG-Zimmer in München — nicht älter als 10 Tage.
          </p>
        </div>

        {/* Dashboard */}
        <ListingGrid />
      </div>
    </div>
  );
}
