"""Evaluate the trained model against test/train data."""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


MODEL_PATH = Path("ml") / "worldcup_model.pkl"

def create_target(df: pd.DataFrame) -> pd.Series:
    home = df["home_score"]
    away = df["away_score"]
    target = pd.Series(1, index=df.index)
    target[home > away] = 2
    target[away > home] = 0
    return target


def main():
    if not MODEL_PATH.exists():
        raise SystemExit(f"Missing model: {MODEL_PATH}")

    model = joblib.load(MODEL_PATH)
    feature_names = list(getattr(model, "_feature_names_list", []))

    train_pq = Path("data") / "processed" / "train_with_features.parquet"
    test_pq = Path("data") / "processed" / "test_with_features.parquet"

    for name, path in [("Train", train_pq), ("Test", test_pq)]:
        if not path.exists():
            continue

        df = pd.read_parquet(path)
        
        if "neutral" not in df.columns:
            df["neutral"] = False
        if "is_home" not in df.columns:
            df["is_home"] = ~df["neutral"]
        if "year" not in df.columns:
            df["year"] = 2023
        
        for f in feature_names:
            if f not in df.columns:
                df[f] = 0

        X = df[feature_names].copy()
        for col in X.columns:
            if X[col].dtype == 'datetime64[ns]':
                X[col] = X[col].apply(lambda x: x.year if pd.notna(x) else 2023)
            elif X[col].dtype == 'bool':
                X[col] = X[col].astype(int)
        X = X.apply(pd.to_numeric, errors='coerce').fillna(0)

        y_true = create_target(df)
        y_pred = model.predict(X)
        acc = accuracy_score(y_true, y_pred)
        
        print(f"\n{'='*50}")
        print(f"{name} Data ({len(df):,} matches)")
        print(f"Accuracy: {acc:.4f} ({acc*100:.2f}%)")
        print(classification_report(y_true, y_pred, target_names=["away_win", "draw", "home_win"], zero_division=0))
        
        cm = confusion_matrix(y_true, y_pred)
        print(f"            Pred Away  Pred Draw  Pred Home")
        print(f"True Away:     {cm[0][0]:5d}      {cm[0][1]:5d}      {cm[0][2]:5d}")
        print(f"True Draw:     {cm[1][0]:5d}      {cm[1][1]:5d}      {cm[1][2]:5d}")
        print(f"True Home:     {cm[2][0]:5d}      {cm[2][1]:5d}      {cm[2][2]:5d}")

        draws = y_true == 1
        if draws.sum() > 0:
            draw_acc = (y_pred[draws] == 1).mean()
            print(f"Draw accuracy: {draw_acc:.2%} ({draws.sum()} draws)")


if __name__ == "__main__":
    main()