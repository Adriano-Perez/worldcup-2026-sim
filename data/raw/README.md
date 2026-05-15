# `data/raw/`

## International results (martj42)

Downloaded **2026-05-14** from the upstream project:

- **Source:** [github.com/martj42/international_results](https://github.com/martj42/international_results)  
- **Files:**
  - `results.csv` — match results (date, teams, scores, tournament, neutral, etc.)
  - `shootouts.csv` — shootout metadata where applicable
  - `goalscorers.csv` — goal-level rows (player names, minute, etc.)

**License / usage:** follow the **license and README in the upstream repository** (do not assume beyond what they publish). For a portfolio, also **cite the source** in your model write-up.

Next step: add an ETL script under `ml/` (or `scripts/`) that reads these CSVs and writes `data/processed/matches.parquet` with stable team IDs.
