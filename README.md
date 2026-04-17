# Munich Rental Assistant 🏠

> Autonomer Immobilien-Assistent für München — für Studierende und alle, die schnell an gute Wohnungen kommen wollen.

## Was ist das?

Eine Webapp, die:

1. **Scannt** WG-Gesucht, ImmoScout24, eBay-Kleinanzeigen und lokale Portale (Phase 1)
2. **Analysiert** Preise, erkennt Spam/Scams und bewertet Lage (Phase 2)
3. **Bewirbt sich automatisch** — sobald ein passendes Inserat auftaucht (Phase 3)

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, FastAPI, SQLAlchemy 2.0 |
| **Database** | PostgreSQL (Docker) / SQLite (dev) |
| **Task Queue** | Redis + RQ |
| **Scraping** | httpx + BeautifulSoup (human-like behavior) |
| **Frontend** | Next.js (React, TypeScript) *(coming soon)* |
| **Auth** | JWT placeholder *(coming soon)* |
| **Billing** | Stripe *(coming soon)* |

## Quick Start

### 1. Backend

```bash
cd backend

# Virtual environment
python3 -m venv .venv && source .venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Env-Datei anlegen
cp .env.example .env   # (DB-URL etc. anpassen)

# Datenbank erstellen + starten
docker compose -f ../infra/docker-compose.yml up -d db redis

# Server starten
uvicorn app.main:app --reload --port 8000
```

**Wichtigste Endpoints:**

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/health` | Health-Check |
| `GET` | `/api/v1/listings` | Alle Inserate (mit Filtern) |
| `POST` | `/api/v1/listings/scrape` | Scrape-Job starten |
| `POST` | `/api/v1/users` | Account erstellen |
| `POST` | `/api/v1/users/me/profiles` | Suchprofil erstellen |

**Beispiel: Scraping starten:**
```bash
curl -X POST "http://localhost:8000/api/v1/listings/scrape?city=München&max_price=1000&pages=2"
```

**Beispiel: Inserate abrufen:**
```bash
curl "http://localhost:8000/api/v1/listings?max_price=900&wg_only=true"
```

### 2. Frontend *(in Bearbeitung)*

```bash
cd frontend
npx create-next-app@latest . --typescript --eslint --tailwind

# Nach Installation:
npm run dev
```

### 3. Docker Compose (alles auf einmal)

```bash
cd infra
docker compose up --build
```

## Projektstruktur

```
munich-rental-assistant/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── listings.py    ← Listings CRUD + scrape trigger
│   │   │       ├── users.py       ← User + SearchProfile CRUD
│   │   │       └── router.py
│   │   ├── core/
│   │   │   └── config.py          ← Settings (DB, Redis, media)
│   │   ├── models/
│   │   │   ├── listing.py         ← Listing, ListingImage
│   │   │   └── user.py            ← User, SearchProfile
│   │   ├── services/
│   │   │   ├── media.py           ← Bild-Pfad/URL-Logik
│   │   │   └── scraping/
│   │   │       └── wg_gesucht.py  ← Anti-Ban WG-Gesucht Scraper
│   │   ├── db.py                  ← SQLAlchemy session
│   │   └── main.py                ← FastAPI app factory
│   └── requirements.txt
├── frontend/                      ← Next.js (coming soon)
├── infra/
│   └── docker-compose.yml         ← api + postgres + redis
└── README.md
```

## Phase-Roadmap

- [x] **Phase 0:** Repo-Struktur, Backend-Skeleton, DB-Modelle
- [x] **Phase 1:** WG-Gesucht Scraper + Listings-API + Filter
- [ ] **Phase 1b:** Commute-Intelligence (ÖPNV/Lage)
- [ ] **Phase 2:** Spam-/Scam-Detection, Price-Benchmark, Document-Lab, SCHUFA
- [ ] **Phase 3:** Auto-Apply (1-Click / Email), ML-Text-Optimierung

## GitHub Workflow

```
main  ← stabil, nur reviewed merges
develop  ← feature-integration
feature/<name>  ← individuelle Features
```

Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`)

## Security Hinweise

- Passwörter aktuell als Plaintext in DB → **bald Hashing mit bcrypt**
- Auth aktuell nur Mock/User-ID=1 → **JWT-Integration in Phase 2**
- Scraper: Respektiert Rate-Limits, keine harten Brute-Force-Zugriffe
- Alle sensiblen Daten (Dokumente, SCHUFA): verschlüsselt + Ablauflink

---

Bei Fragen / Issues → ShahzebKhalid27
