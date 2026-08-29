# ⚽ 2026 FIFA World Cup Prediction Simulator

A full **2026 FIFA World Cup tournament simulation** using machine learning to predict match probabilities, group-stage results, standings, knockout advancement, and the World Cup champion.

The project simulates the entire tournament:

**Group Stage → Round of 32 → Round of 16 → Quarterfinals → Semifinals → Final**

---

## 🚀 Quick Start

### Clone the Repository

```bash
git clone https://github.com/Adriano-Perez/worldcup-2026-sim.git
cd worldcup-2026-sim
```

### Install Dependencies

```bash
pip install joblib numpy pandas
```

### Run the Full Tournament Simulation

```bash
python ml/simulate_tournament.py
```

### Run Individual Stages

```bash
# Group stage only — 72 matches
python ml/predict_group_stage.py

# Knockout stage only
python ml/generate_knockout.py
```

---

# 🧠 How It Works

## Prediction Pipeline

```text
Team Data + FIFA Rankings + Squad Values + Historical Matches
                          ↓
                  XGBoost ML Models
                          ↓
                  Match Probabilities
                          ↓
             Monte Carlo Simulation
                   (100K per match)
                          ↓
              Group Stage Predictions
                    (72 matches)
                          ↓
             Group Standings + Rankings
                          ↓
       Round of 32 → R16 → QF → SF → Final
                          ↓
                  🏆 World Cup Champion
```

The system combines historical and team-level data with machine learning models to generate match probabilities.

Those probabilities are then used to simulate individual matches and advance teams through the tournament bracket.

---

## 🎯 Match Prediction

Each match prediction produces:

* Predicted winner
* Predicted scoreline
* Home win probability
* Draw probability
* Away win probability
* Monte Carlo simulation result

### Example

```text
Match: Mexico vs South Africa
Neutral: True
Stage: group

Prob South Africa win: 0.076
Prob Draw:             0.204
Prob Mexico win:       0.720

Monte Carlo winner: Mexico

Most likely score after 100,000 simulations:
Mexico 4 - 1 South Africa
```

---

# 🤖 Machine Learning Models

The project uses multiple trained models for different parts of the tournament.

| Model                            | Used For       | Features                                                               | Training Data                                    |
| -------------------------------- | -------------- | ---------------------------------------------------------------------- | ------------------------------------------------ |
| `worldcup_model.pkl`             | Group Stage    | FIFA rankings, squad values, venue, form                               | International matches with tournament weightings |
| `worldcup_model_knockout.pkl`    | Knockout Stage | Core features + knockout experience, streak, finals/semifinals history | Tournament knockout matches                      |
| `worldcup_model_competitive.pkl` | Fallback       | Core features                                                          | Competitive matches only                         |

### Primary Model

The main prediction model uses **XGBoost** to estimate the probability of each match outcome.

---

# 🏋️ Training Pipeline

Training can be run with:

```bash
cd ml/data_prep
python train_predictive_model.py
```

The training pipeline incorporates:

* Historical international matches
* Multiple tournament datasets
* FIFA rankings
* Squad market values
* Key player availability
* Team historical performance
* Competition weighting
* Draw class balancing

### Competition Weighting

More important competitions receive greater weight during training:

```text
World Cup       → 10x
Euro / Copa     → 8x
Qualifiers      → 6x
Friendlies      → 1x
```

This gives major competitive matches greater influence on the model than friendlies.

---

# 🏆 Knockout Stage Adjustments

The knockout prediction system applies additional adjustments to account for differences between group-stage and knockout matches.

### Neutral Venue

Knockout matches are treated as neutral-site games, removing traditional home-field advantage.

### Head-to-Head

Recent competitive head-to-head results can be incorporated when the FIFA ranking gap is below 150 points.

### FIFA Ranking Gap

A stronger FIFA ranking advantage can provide an additional edge when the ranking difference exceeds 20 points.

### No Draws

Knockout matches cannot end in a draw.

If the model produces a draw, the match is resolved using the knockout winner-selection logic, including penalties when required.

### Group Winner Bonus

Group winners receive a slight advantage over teams advancing as group runners-up.

---

# 🌎 Tournament Format

The simulation follows the expanded 2026 World Cup structure:

* **48 teams**
* **12 groups**
* Groups **A–L**
* **4 teams per group**
* Top **2 teams** from each group advance
* **8 best third-place teams** advance
* **32 teams** enter the knockout stage
* Round of 32
* Round of 16
* Quarterfinals
* Semifinals
* Final

---

# 🥉 Third-Place Qualification

After the group stage, all third-place teams are ranked.

The simulation uses:

1. Points
2. Goal difference
3. Goals scored

The top eight third-place teams advance to the Round of 32.

---

# 📊 Simulation Results

## Group Stage

The model generates predictions for all **72 group-stage matches**.

### Group A — Predicted Standings

| Rank | Team                | MP |  W |  D |  L | GF | GA | GD |   Pts |
| ---: | ------------------- | -: | -: | -: | -: | -: | -: | -: | ----: |
|    1 | 🇲🇽 Mexico         |  3 |  3 |  0 |  0 |  9 |  2 | +7 | **9** |
|    2 | 🇰🇷 South Korea    |  3 |  1 |  1 |  1 |  2 |  3 | -1 | **4** |
|    3 | 🇿🇦 South Africa   |  3 |  0 |  2 |  1 |  2 |  5 | -3 | **2** |
|    4 | 🇨🇿 Czech Republic |  3 |  0 |  1 |  2 |  1 |  4 | -3 | **1** |

### Example Group Stage Predictions

```text
🇲🇽 Mexico 4–1 South Africa 🇿🇦
🇰🇷 South Korea 1–0 Czech Republic 🇨🇿
🇲🇽 Mexico 2–0 South Korea 🇰🇷
🇿🇦 South Africa 0–0 Czech Republic 🇨🇿
🇲🇽 Mexico 3–1 Czech Republic 🇨🇿
```

---

# 🔥 Knockout Stage

## Round of 32

Selected predicted results:

```text
🇰🇷 South Korea 2–1 Canada 🇨🇦
🇧🇷 Brazil 2–0 Japan 🇯🇵
🇩🇪 Germany 2–1 South Africa 🇿🇦
🇳🇱 Netherlands 2–1 Morocco 🇲🇦
🇫🇷 France 1–0 Paraguay 🇵🇾
🇲🇽 Mexico 3–0 Ivory Coast 🇨🇮
🏴󠁧󠁢󠁥󠁮󠁧󠁿 England 2–0 Saudi Arabia 🇸🇦
🇧🇪 Belgium 3–1 Algeria 🇩🇿
🇺🇸 United States 2–0 Qatar 🇶🇦
🇪🇸 Spain 2–1 Austria 🇦🇹
🇦🇷 Argentina 2–0 Uruguay 🇺🇾
🇵🇹 Portugal 2–1 DR Congo 🇨🇩
```

---

# 🏅 Quarterfinals

The simulation predicted the following four teams to reach the quarterfinals:

🇫🇷 **France**
🇪🇸 **Spain**
🏴󠁧󠁢󠁥󠁮󠁧󠁿 **England**
🇦🇷 **Argentina**

### Predicted Quarterfinal Results

```text
🇳🇱 Netherlands 0–1 France 🇫🇷
🇧🇪 Belgium 1–3 Spain 🇪🇸
🇧🇷 Brazil 0–2 England 🏴
🇨🇭 Switzerland 0–1 Argentina 🇦🇷
```

**Quarterfinalist accuracy: 4/4 — 100%**

---

# 🔥 Semifinals

### France vs Spain

🇪🇸 **Spain advances**

### England vs Argentina

🇦🇷 **Argentina advances**

**Semifinalist accuracy: 2/2 — 100%**

---

# 🥉 Third Place

```text
🇫🇷 France 1–0 England 🏴
```

### 🥉 Third Place

🇫🇷 **France**

---

# 🏆 Final

```text
🇪🇸 Spain 3–1 Argentina 🇦🇷
```

### Final Prediction

🥇 **🇪🇸 Spain — 2026 FIFA World Cup Champions**

🥈 **🇦🇷 Argentina — Runner-up**

🥉 **🇫🇷 France — Third Place**

---

# 📈 Model Accuracy

The simulation was compared against the actual 2026 FIFA World Cup results.

| Stage                         | Predicted         | Actual            |          Accuracy |
| ----------------------------- | ----------------- | ----------------- | ----------------: |
| **Group-stage match winners** | —                 | —                 | **50/72 = 69.4%** |
| **R32 advancement**           | 16 predicted      | 16 actual         | **11/16 = 68.8%** |
| **R16 advancement**           | 8 predicted       | 8 actual          |     **6/8 = 75%** |
| **Quarterfinalists**          | 4 predicted       | 4 actual          |    **4/4 = 100%** |
| **Semifinalists**             | 2 predicted       | 2 actual          |    **2/2 = 100%** |
| **Finalists**                 | Spain & Argentina | Spain & Argentina |    **2/2 = 100%** |
| **Champion**                  | 🇪🇸 Spain        | 🇪🇸 Spain        |       **Correct** |

The model correctly predicted the eventual **World Cup champion, finalist matchup, semifinalists, and quarterfinalists**.

---

# 📁 Project Structure

```text
worldcup-2026-sim/
│
├── README.md
│
├── ml/
│   ├── predict_match.py
│   ├── predict_group_stage.py
│   ├── generate_knockout.py
│   ├── simulate_tournament.py
│   ├── bracket_rules.py
│   │
│   ├── worldcup_model.pkl
│   ├── worldcup_model_knockout.pkl
│   ├── worldcup_model_competitive.pkl
│   │
│   └── data_prep/
│       ├── train_predictive_model.py
│       ├── integrate_team_history.py
│       ├── integrate_club_features.py
│       ├── add_key_player_availability.py
│       └── evaluate_model.py
│
├── data/
│   ├── fifa_rankings_2026.csv
│   ├── squad_values.csv
│   ├── games.csv
│   ├── key_players.csv
│   │
│   └── output/
│       ├── group_stage_predictions.json
│       └── group_standings.json
│
└── apps/
    └── web/
        └── # Frontend coming soon
```

---

# 📊 Output Files

The simulation produces structured JSON output that can be consumed by the future frontend.

```text
data/output/
│
├── group_stage_predictions.json
│   └── All 72 group-stage match predictions,
│       probabilities, and predicted scores
│
└── group_standings.json
    └── Final group standings and rankings
```

---

# 🚧 Frontend — Coming Soon

The backend simulation engine is complete.

A web-based frontend is currently in development.

The frontend will provide an interactive way to explore the entire simulation without running the Python scripts manually.

### Planned Features

* 🌎 Interactive World Cup groups
* 📊 Group standings
* 🏟️ Match prediction cards
* 📈 Win / draw / loss probabilities
* ⚽ Predicted scorelines
* 🏆 Interactive knockout bracket
* 🥇 Tournament champion visualization
* 📉 Model accuracy dashboard
* 🔄 Run new simulations directly from the browser
* 📊 Prediction confidence visualization

```text
Backend
   ↓
Prediction API
   ↓
Frontend
   ↓
Interactive World Cup Simulator
```

---

# 🔮 Future Improvements

* [ ] Interactive frontend
* [ ] Elo rating integration
* [ ] Player-level statistics
* [ ] Improved injury and squad availability modeling
* [ ] Home-field and travel effects
* [ ] Multiple full-tournament Monte Carlo simulations
* [ ] Prediction confidence intervals
* [ ] Automated real-world result comparison
* [ ] Historical team performance trends
* [ ] Weather effects
* [ ] Altitude effects
* [ ] Advanced player availability
* [ ] Model performance dashboard
* [ ] Automated model retraining

---

# 🛠️ Technology Stack

### Machine Learning

* Python
* XGBoost
* NumPy
* Pandas
* Joblib

### Data

* FIFA rankings
* International match history
* Tournament results
* Squad values
* Player availability
* Team historical performance

### Frontend

🚧 **Coming Soon**

---

# 📌 Project Status

| Component                  | Status             |
| -------------------------- | ------------------ |
| Backend prediction engine  | ✅ Complete         |
| ML models                  | ✅ Complete         |
| Group-stage simulation     | ✅ Complete         |
| Third-place qualification  | ✅ Complete         |
| Knockout simulation        | ✅ Complete         |
| Full tournament simulation | ✅ Complete         |
| Accuracy comparison        | ✅ Complete         |
| Output generation          | ✅ Complete         |
| Frontend                   | 🚧 **Coming Soon** |

---

# 🏆 Final Prediction

## 🇪🇸 SPAIN — 2026 FIFA WORLD CUP CHAMPIONS

### Predicted Final

**Spain 3–1 Argentina**

The simulation correctly predicted teams reaching:

* **69.4%** of group-stage match winners
* **100%** of quarterfinalists
* **100%** of semifinalists
* **100%** of finalists
* **The World Cup Champion 🇪🇸**

