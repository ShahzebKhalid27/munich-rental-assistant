import Link from "next/link";
import Navbar from "@/components/Navbar";

export const dynamic = "force-dynamic";

export default function Home() {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      <Navbar />

      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 text-white">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAgTCAwIDEwIEwgMTAgMTAgWiIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDUpIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-30" />
        <div className="relative mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-medium text-white/80 backdrop-blur-sm">
              🚀 Für Studierende in München
            </div>
            <h1 className="mb-4 text-5xl font-bold tracking-tight leading-tight sm:text-6xl">
              Deine Traum-WG.<br />
              <span className="text-blue-200">Automatisch gefunden.</span>
            </h1>
            <p className="mb-8 max-w-xl text-lg text-blue-100 leading-relaxed">
              Munich Rental Assistant scannt WG-Gesucht und andere Portale rund um die Uhr —
              filtert Spam raus, zeigt dir nur das Beste und benachrichtigt dich sofort,
              wenn etwas Passendes auftaucht.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link
                href="/dashboard"
                className="rounded-xl bg-white px-6 py-3.5 text-base font-semibold text-blue-700 shadow-lg hover:bg-blue-50 transition-all hover:shadow-xl hover:-translate-y-0.5"
              >
                Kostenlos starten →
              </Link>
              <Link
                href="/docs"
                className="rounded-xl border border-white/30 bg-white/10 px-6 py-3.5 text-base font-semibold text-white backdrop-blur-sm hover:bg-white/20 transition-all"
              >
                So funktioniert's
              </Link>
            </div>
          </div>
        </div>

        {/* Mock screenshot */}
        <div className="relative mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
          <div className="rounded-2xl border border-white/20 bg-white/10 backdrop-blur-xl p-3 shadow-2xl">
            <div className="overflow-hidden rounded-xl bg-gray-900">
              <div className="flex items-center gap-1.5 border-b border-white/10 px-4 py-3">
                <div className="h-3 w-3 rounded-full bg-red-500/80" />
                <div className="h-3 w-3 rounded-full bg-yellow-500/80" />
                <div className="h-3 w-3 rounded-full bg-green-500/80" />
              </div>
              <div className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="h-4 w-48 rounded bg-white/10" />
                    <div className="h-3 w-32 rounded bg-white/5" />
                  </div>
                  <div className="h-8 w-28 rounded-lg bg-blue-500/60" />
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {[0, 1, 2].map((i) => (
                    <div key={i} className="space-y-2 rounded-xl bg-white/5 p-3">
                      <div className="h-24 rounded-lg bg-white/10" />
                      <div className="h-3 w-20 rounded bg-white/10" />
                      <div className="h-3 w-14 rounded bg-white/5" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="bg-gray-50 dark:bg-gray-900 py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-14 text-center">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">
              Alles, was du für deine WG-Suche brauchst
            </h2>
            <p className="mt-3 text-gray-500 dark:text-gray-400 max-w-2xl mx-auto">
              Kein stundenlanges Scrollen durch Spam-Inserate. Wir machen das für dich.
            </p>
          </div>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                icon: "🔍",
                title: "Intelligente Suche",
                desc: "Filtere nach Preis, Größe, Viertel und WG-Typ. Nie wieder unpassende Ergebnisse.",
              },
              {
                icon: "🛡️",
                title: "Spam-Filter",
                desc: "Vorkasse-Scams und Fake-Inserate werden automatisch erkannt und aussortiert.",
              },
              {
                icon: "🔔",
                title: "Sofort-Benachrichtigung",
                desc: " Aktiviere Suchaufträge und erhalte eine Nachricht, sobald etwas Passendes auftaucht.",
              },
              {
                icon: "⚡",
                title: "Speed-to-Lead",
                desc: "Die besten WG-Zimmer in München sind in Sekunden weg — wir sind schneller.",
              },
              {
                icon: "📄",
                title: "Dokumente-Manager",
                desc: "Lade deine Unterlagen hoch und verschicke Bewerbungen mit einem Klick.",
              },
              {
                icon: "🌙",
                title: "Dark Mode",
                desc: "Angenehmes Design für Abend- und Nachtsitzungen beim Wohnungssuchen.",
              },
            ].map(({ icon, title, desc }) => (
              <div
                key={title}
                className="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-800 p-6 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="mb-4 text-3xl">{icon}</div>
                <h3 className="mb-2 font-semibold text-gray-900 dark:text-white text-base">{title}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-white dark:bg-gray-950 py-20">
        <div className="mx-auto max-w-3xl px-4 text-center sm:px-6">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight mb-4">
            Bereit für dein neues Zuhause?
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mb-8 text-lg">
            Kostenloses Konto erstellen — in 30 Sekunden einsatzbereit.
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-8 py-4 text-lg font-semibold text-white shadow-lg hover:bg-blue-700 hover:shadow-xl transition-all hover:-translate-y-0.5"
          >
            Jetzt kostenlos starten
            <span>→</span>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 py-8">
        <div className="mx-auto max-w-7xl px-4 flex items-center justify-between text-sm text-gray-400">
          <span>© 2026 Munich Rental Assistant</span>
          <div className="flex gap-6">
            <Link href="/docs" className="hover:text-gray-600 dark:hover:text-gray-300">API</Link>
            <Link href="/docs" className="hover:text-gray-600 dark:hover:text-gray-300">Datenschutz</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
