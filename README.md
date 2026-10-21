# Rainfall Wolf Game

A playable ecosystem survival game driven by real Indian rainfall data (1901-2015). You are a wolf hunting rabbits on a grass field. The rain in each month comes from a real region and a real 10-year period, so droughts and heavy rain change how much grass grows, how many rabbits survive, and how hard it is to stay alive.

Built in Python with NumPy and pandas as a software lab mini project.

## Gameplay

- You control the blue wolf on a 30 x 30 grid. **One move = one month.**
- Eat rabbits to gain energy. Moving costs 1 energy per month, and you starve at 0.
- Two red rival wolves also hunt the rabbits.
- Rabbits eat grass, breed when they have enough energy, and run away from nearby wolves.
- Survive **10 years (120 months)** to win. The game also ends if you starve or all the rabbits are gone.
- **Score = months survived + 5 points per rabbit eaten.**
- Don't eat every rabbit: if the ecosystem collapses, you lose.

## How rainfall affects the game

Each game picks a random region and a random 10-year period from the dataset.

- More rain makes grass grow faster.
- A very dry month (below 30% of the average) kills some grass.
- A **drought** is a rainy-season month that gets less than half of its normal rain. It kills a lot more grass, and the game shows an orange warning.

## Controls

| Key | Action |
|-----|--------|
| Arrow keys / WASD | Move |
| R | Restart |
| T | Yearly summary table for the current game |
| E | Results by region across all games played |

## Dataset

`rainfall in india 1901-2015.csv`: monthly rainfall (mm) for 36 meteorological subdivisions of India, from 1901 to 2015.

## How pandas, NumPy and Python features are used

- **pandas:** loading and cleaning the CSV, filling missing values with the mean, `groupby` summaries (`make_table`, `make_results`), saving CSV output
- **NumPy:** grass grid as a boolean array, random growth and death of grass, 10-year rain arrays
- **Sets:** `regions_played` tracks the regions played, with no repeats
- **File handling:** high score in a text file, game logs in CSV files, results appended after every game

## Files created while playing

| File | Contents |
|------|----------|
| `high_score.txt` | Best score |
| `game_log.csv` | Month-by-month log of the last game |
| `year_summary.csv` | Yearly summary of the last game |
| `results.csv` | One row per game played (used by the **E** screen) |

## How to run

1. Install Python 3.8 or newer. Tkinter comes with the standard Python installer. On some Linux systems you need `sudo apt install python3-tk`.
2. Clone the repo or download it as a ZIP:
   ```bash
   git clone https://github.com/<your-username>/<repo-name>.git
   cd <repo-name>
   ```
3. Install the packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Keep the dataset CSV in the same folder as `rainfall_game.py`.
5. Start the game:
   ```bash
   python rainfall_game.py
   ```

## Project structure

```
.
├── rainfall_game.py
├── rainfall in india 1901-2015.csv
├── requirements.txt
├── .gitignore
└── README.md
```

## Author

Team Project
