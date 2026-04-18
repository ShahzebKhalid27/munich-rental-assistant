"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { useAuth } from "@/lib/auth";
import type { SearchProfileResponse } from "@/lib/profile_api";

interface CreateProfileForm {
  name: string;
  price_max: string;
  size_min: string;
  wg_type: string;
  preferred_districts: string;
}

const WG_TYPES = [
  { value: "", label: "Alle" },
  { value: "wg", label: "WG-Zimmer" },
  { value: "studio", label: "Studio / 1-Zimmer" },
  { value: "apartment", label: "Wohnung" },
];

const SAMPLE_DISTRICTS = [
  "Maxvorstadt", "Schwabing", "Au", "Haidhausen", "Bogenhausen",
  "Neuhausen", "Giesing", "Sendling", "Pasing", "Laim",
];

export default function ProfilePage() {
  const { user, token, loading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [user, authLoading, router]);

  const [profiles, setProfiles] = useState<SearchProfileResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<CreateProfileForm>({
    name: "",
    price_max: "",
    size_min: "",
    wg_type: "",
    preferred_districts: "",
  });
  const [saving, setSaving] = useState(false);

  async function loadProfiles() {
    if (!token) return;
    try {
      const res = await fetch("http://localhost:8000/api/v1/users/me/profiles", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setProfiles(Array.isArray(data) ? data : []);
    } catch {
      setProfiles([]);
    }
  }

  useEffect(() => {
    if (token) {
      void loadProfiles().then(() => setLoading(false));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const body: Record<string, string | number> = {
        name: form.name,
        city: "München",
      };
      if (form.price_max) body.price_max = Number(form.price_max);
      if (form.size_min) body.size_min_sqm = Number(form.size_min);
      if (form.wg_type) body.wg_type = form.wg_type;
      if (form.preferred_districts) {
        const districts = form.preferred_districts.split(",").map((d) => d.trim()).filter(Boolean);
        body.preferred_districts = JSON.stringify(districts);
      }

      const res = await fetch("http://localhost:8000/api/v1/users/me/profiles", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await loadProfiles();
      setShowForm(false);
      setForm({ name: "", price_max: "", size_min: "", wg_type: "", preferred_districts: "" });
    } catch {
      setError("Profil konnte nicht erstellt werden.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="mx-auto max-w-3xl px-4 py-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Deine Suchprofile</h1>
            <p className="text-sm text-gray-500 mt-1">
              Definiere Filter, die automatisch zu neuen Inseraten passen.
            </p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
          >
            {showForm ? "Abbrechen" : "+ Neues Profil"}
          </button>
        </div>

        {/* Create form */}
        {showForm && (
          <form
            onSubmit={handleCreate}
            className="mb-6 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm space-y-4"
          >
            <h2 className="font-semibold text-gray-800">Neues Suchprofil erstellen</h2>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Profilname</label>
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="z.B. WG bis 800€ in Maxvorstadt"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Max. Preis (€)</label>
                <input
                  type="number"
                  value={form.price_max}
                  onChange={(e) => setForm({ ...form, price_max: e.target.value })}
                  placeholder="800"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Min. Größe (m²)</label>
                <input
                  type="number"
                  value={form.size_min}
                  onChange={(e) => setForm({ ...form, size_min: e.target.value })}
                  placeholder="20"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Art</label>
              <select
                value={form.wg_type}
                onChange={(e) => setForm({ ...form, wg_type: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              >
                {WG_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Bevorzugte Viertel{" "}
                <span className="text-gray-400">(kommagetrennt)</span>
              </label>
              <input
                value={form.preferred_districts}
                onChange={(e) => setForm({ ...form, preferred_districts: e.target.value })}
                placeholder="Maxvorstadt, Schwabing, Haidhausen"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              />
              <div className="mt-1.5 flex flex-wrap gap-1">
                {SAMPLE_DISTRICTS.slice(0, 5).map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => {
                      const current = form.preferred_districts
                        ? form.preferred_districts.split(",").map((x) => x.trim()).filter(Boolean)
                        : [];
                      if (!current.includes(d)) {
                        setForm({ ...form, preferred_districts: [...current, d].join(", ") });
                      }
                    }}
                    className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600 hover:bg-gray-200 transition-colors"
                  >
                    + {d}
                  </button>
                ))}
              </div>
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <button
              type="submit"
              disabled={saving}
              className="w-full rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {saving ? "Speichert..." : "Profil erstellen"}
            </button>
          </form>
        )}

        {/* Profile list */}
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 2 }).map((_, i) => (
              <div key={i} className="animate-pulse rounded-xl border border-gray-200 bg-white p-5 h-28" />
            ))}
          </div>
        ) : profiles.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-gray-200 py-20 text-center">
            <span className="mb-3 text-4xl">🔍</span>
            <h3 className="text-lg font-semibold text-gray-700">Noch kein Suchprofil</h3>
            <p className="mt-1 text-sm text-gray-400 max-w-xs">
              Erstelle dein erstes Profil, um automatisch passende Inserate zu sehen.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {profiles.map((p) => (
              <div key={p.id} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{p.name}</h3>
                    <p className="text-sm text-gray-500 mt-0.5">
                      {p.price_max ? `bis ${p.price_max} €` : "Kein Preislimit"}
                      {p.size_min_sqm ? ` · ab ${p.size_min_sqm} m²` : ""}
                      {p.wg_type ? ` · ${p.wg_type}` : ""}
                    </p>
                    {p.preferred_districts && (
                      <p className="text-xs text-gray-400 mt-1">
                        📍 {JSON.parse(p.preferred_districts).join(", ")}
                      </p>
                    )}
                  </div>
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    p.is_active
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-gray-100 text-gray-500"
                  }`}>
                    {p.is_active ? "Aktiv" : "Inaktiv"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
