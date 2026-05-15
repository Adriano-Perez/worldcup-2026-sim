# `ml/`

Training code, feature engineering, evaluation, and exported model artifacts (paths ignored in `.gitignore` where noted).

## Quickstart (ETL)

From repo root (after `python3 -m venv .venv && source .venv/bin/activate`):

```bash
pip install -r requirements.txt
python ml/etl_results_to_parquet.py
```

Writes `data/processed/matches.parquet`.
