import pandas as pd

# Show all columns in the national team performances file
national_perf = pd.read_csv("data/football-datasets/player_national_performances/player_national_performances.csv")
print("player_national_performances.csv columns:")
print(list(national_perf.columns))
