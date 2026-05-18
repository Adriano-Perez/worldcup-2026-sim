import kagglehub
import pandas as pd

# Download the latest version of the football-datasets dataset from Kaggle
path = kagglehub.dataset_download("xfkzujqjvx97n/football-datasets")

print("Path to dataset files:", path)

# Example: Load players and appearances CSVs (update filenames as needed)
try:
    players = pd.read_csv(f"{path}/players.csv")
    appearances = pd.read_csv(f"{path}/appearances.csv")
    print("Players sample:")
    print(players.head())
    print("Appearances sample:")
    print(appearances.head())
except Exception as e:
    print("Error loading CSV files:", e)
