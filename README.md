# worldcup-2026-sim

2026 World Cup **match probabilities** (ML) + **Monte Carlo** tournament simulation + a **website** with:

- **Pre‑Bracket**: frozen snapshot before kickoff (baseline predictions).
- **Live**: enter real scores; re-simulate only remaining matches; public read, admin + editor logins.

Stack (planned): Next.js + Python/FastAPI + DB. Details will grow as the repo grows.

## Repository layout

| Path | Purpose |
|------|---------|
| `ml/` | Training, features, evaluation, model artifacts |
| `data/raw/` | Original downloads |
| `data/processed/` | Cleaned tables (e.g. `matches.parquet`) |
| `packages/rules/` | FIFA rules engine (standings + bracket routing), no ML |
| `apps/api/` | FastAPI service |
| `apps/web/` | Next.js frontend |
| `docs/` | Official doc links + methodology notes |