import Navbar from "@/components/Navbar";

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="mx-auto max-w-3xl px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">📋 API Dokumentation</h1>
        <p className="text-gray-500 mb-8">Munich Rental Assistant — Backend API v1</p>

        <div className="space-y-8">

          {/* Listings */}
          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">🏠 Listings</h2>
            <div className="space-y-4">

              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-bold text-emerald-700">GET</span>
                  <code className="text-sm text-gray-800">/api/v1/listings</code>
                </div>
                <p className="text-sm text-gray-600 mb-3">Holt alle Inserate mit optionalen Filtern.</p>
                <table className="w-full text-xs text-gray-600">
                  <thead>
                    <tr className="border-b border-gray-100"><th className="pb-2 text-left">Parameter</th><th className="pb-2 text-left">Typ</th><th className="pb-2 text-left">Beschreibung</th></tr>
                  </thead>
                  <tbody className="space-y-1">
                    <tr><td className="pr-4 font-mono text-xs">city</td><td>string</td><td>Stadt (Standard: München)</td></tr>
                    <tr><td className="pr-4 font-mono text-xs">district</td><td>string</td><td>Stadtviertel</td></tr>
                    <tr><td className="pr-4 font-mono text-xs">min_price</td><td>number</td><td>Min. Preis (€)</td></tr>
                    <tr><td className="pr-4 font-mono text-xs">max_price</td><td>number</td><td>Max. Preis (€)</td></tr>
                    <tr><td className="pr-4 font-mono text-xs">min_size</td><td>number</td><td>Min. Größe (m²)</td></tr>
                    <tr><td className="pr-4 font-mono text-xs">wg_only</td><td>bool</td><td>Nur WG-Zimmer</td></tr>
                    <tr><td className="pr-4 font-mono text-xs">limit</td><td>number</td><td>Max. Ergebnisse (Standard: 20)</td></tr>
                    <tr><td className="pr-4 font-mono text-xs">offset</td><td>number</td><td>Seiten-Offset</td></tr>
                  </tbody>
                </table>
                <p className="mt-3 text-xs text-gray-500">
                  <strong>Beispiel:</strong>{" "}
                  <code className="rounded bg-gray-100 px-1.5 py-0.5 font-mono">
                    /api/v1/listings?max_price=800&wg_only=true&district=Maxvorstadt
                  </code>
                </p>
              </div>

              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-bold text-blue-700">POST</span>
                  <code className="text-sm text-gray-800">/api/v1/listings/scrape</code>
                </div>
                <p className="text-sm text-gray-600">Startet einen Hintergrund-Scrape-Job (WG-Gesucht).</p>
                <p className="mt-2 text-xs text-gray-500">
                  Parameter: <code className="font-mono">city</code>, <code className="font-mono">max_price</code>, <code className="font-mono">pages</code> (1–10)
                </p>
              </div>

              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-bold text-emerald-700">GET</span>
                  <code className="text-sm text-gray-800">/api/v1/listings/match/{"{profile_id}"}</code>
                </div>
                <p className="text-sm text-gray-600">Top-Matches für ein Suchprofil (Matching Engine).</p>
                <p className="mt-2 text-xs text-gray-500">
                  Mit <code className="font-mono">?use_llm=true</code> → LLM-gestütztes Scoring (langsamer, genauer)
                </p>
              </div>

            </div>
          </section>

          {/* Users */}
          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">👤 User & Profile</h2>
            <div className="space-y-4">

              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-bold text-blue-700">POST</span>
                  <code className="text-sm text-gray-800">/api/v1/users</code>
                </div>
                <p className="text-sm text-gray-600">Neuen Account registrieren.</p>
                <p className="mt-2 text-xs text-gray-500">
                  Body: <code className="font-mono">{"{ email, password, full_name }"}</code>
                </p>
              </div>

              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-bold text-blue-700">POST</span>
                  <code className="text-sm text-gray-800">/api/v1/users/me/profiles</code>
                </div>
                <p className="text-sm text-gray-600">Suchprofil erstellen.</p>
                <p className="mt-2 text-xs text-gray-500">
                  Body: <code className="font-mono">{"{ name, city, price_max, size_min_sqm, wg_type, preferred_districts }"}</code>
                </p>
              </div>

              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-bold text-emerald-700">GET</span>
                  <code className="text-sm text-gray-800">/api/v1/users/me/profiles</code>
                </div>
                <p className="text-sm text-gray-600">Alle aktiven Suchprofile des aktuellen Users.</p>
              </div>

            </div>
          </section>

          {/* Health */}
          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">❤ Health</h2>
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-bold text-emerald-700">GET</span>
                <code className="text-sm text-gray-800">/health</code>
              </div>
              <p className="text-sm text-gray-600">Health-Check — gibt <code className="font-mono">{"{ status: 'ok' }"}</code> zurück.</p>
            </div>
          </section>

          {/* Coming soon */}
          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">🚧 Coming Soon</h2>
            <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-5">
              <ul className="space-y-2 text-sm text-gray-600">
                <li>🔐 JWT Auth — Login/Logout mit Token</li>
                <li>🔍 Matching-API mit LLM — echte Intelligenz</li>
                <li>📄 Document Lab — Anschreiben & CV generieren</li>
                <li>📍 Commute Intelligence — ÖPNV-Pendelzeit</li>
                <li>🛡️ Privacy Shield — Wasserzeichen, Metadaten-Entfernung</li>
                <li>🤖 Auto-Apply — automatische Bewerbungen</li>
              </ul>
            </div>
          </section>

        </div>
      </div>
    </div>
  );
}
