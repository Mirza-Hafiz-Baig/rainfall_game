import os
import random
import tkinter as tk
import numpy as np
import pandas as pd

SIZE = 30       # grid is 30 x 30
CELL = 20       # size of one square in pixels
PANEL = 230     # width of the side panel
GRASS_ENERGY = 5     # energy a rabbit gets from eating grass
BREED_ENERGY = 15    # rabbit makes a baby at this energy
MEAT_ENERGY = 14     # energy a wolf gets from eating a rabbit
MAX_RABBITS = 250    # rabbits can not go above this
GROW_CHANCE = 0.055  # normal chance of grass growing on one square in a month
N_RIVALS = 2         # number of rival wolves
DROUGHT_SURVIVE = 0.9   # in a drought month each grass square survives with this chance
MOVES = [(0, -1), (1, 0), (0, 1), (-1, 0)]     # up, right, down, left
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

data = None     # the whole rainfall dataset (filled in main)
regions = []    # regions that have enough years of data
region = ""
regions_played = set()   # a set: every region played so far (no repeats)
best_score = 0          # best score read from the high score file
score = 0


def read_high_score():
    # read the best score from the text file (0 if there is no file yet)
    try:
        with open("high_score.txt", "r") as f:
            return int(f.read())
    except (FileNotFoundError, ValueError):
        return 0


def save_high_score(new_score):
    with open("high_score.txt", "w") as f:
        f.write(str(new_score))


def get_rain():
    # pick a random region and a random 10 year part of its data
    global region
    region = random.choice(regions)
    regions_played.add(region)
    part = data[data["SUBDIVISION"] == region][["YEAR"] + MONTHS]
    part = part.fillna(part.mean())     # fill missing values with the average
    normal = part[MONTHS].mean().values     # normal rain of each month (average of all years)
    start = random.randint(0, len(part) - 10)
    part = part.iloc[start:start + 10]
    return part[MONTHS].values.flatten(), part["YEAR"].values, np.tile(normal, 10)


def sign(n):
    if n > 0:
        return 1
    if n < 0:
        return -1
    return 0


def clamp(n):
    # keep a position inside the grid
    return min(max(n, 0), SIZE - 1)


def new_game():
    global rain, years, normal_rain, avg_rain, grass, rabbits, rivals, wolf, energy, eaten, month
    global log, over, message, score, best_score
    rain, years, normal_rain = get_rain()
    avg_rain = rain.mean()
    grass = np.random.rand(SIZE, SIZE) < 0.6
    rabbits = [[random.randrange(SIZE), random.randrange(SIZE), 8] for i in range(30)]
    rivals = [[random.randrange(SIZE), random.randrange(SIZE), 30] for i in range(N_RIVALS)]
    wolf = [SIZE // 2, SIZE // 2]
    energy = 40
    eaten = 0
    month = 0
    log = []
    over = False
    message = ""
    score = 0
    best_score = read_high_score()


def eat_rabbit():
    # player wolf eats a rabbit on the same square
    global energy, eaten
    for r in rabbits:
        if r[0] == wolf[0] and r[1] == wolf[1]:
            rabbits.remove(r)
            energy = min(energy + MEAT_ENERGY, 60)
            eaten += 1
            return


def move_rabbits():
    global rabbits
    wolves = [[w[0], w[1]] for w in rivals] + [wolf]
    babies = []
    for r in rabbits:
        if random.random() < 0.6:                    # rabbits move in 60% of the months
            near = min(wolves, key=lambda w: abs(w[0] - r[0]) + abs(w[1] - r[1]))
            if abs(near[0] - r[0]) + abs(near[1] - r[1]) <= 4:
                # a wolf is close: run away (pick the move that ends furthest from it)
                dx, dy = max(MOVES, key=lambda m: abs(clamp(r[0] + m[0]) - near[0])
                             + abs(clamp(r[1] + m[1]) - near[1]))
            else:
                dx, dy = random.choice(MOVES)
            r[0] = clamp(r[0] + dx)
            r[1] = clamp(r[1] + dy)
        if grass[r[1], r[0]]:
            grass[r[1], r[0]] = False
            r[2] += GRASS_ENERGY
        r[2] -= 1
        if r[2] >= BREED_ENERGY and len(rabbits) + len(babies) < MAX_RABBITS:
            baby_energy = r[2] // 2                  # the baby gets half of the energy
            r[2] = r[2] - baby_energy
            babies.append([r[0], r[1], baby_energy])
    rabbits = [r for r in rabbits if r[2] > 0] + babies


def move_rivals():
    # rival wolves walk towards the nearest rabbit (sometimes they wander)
    global rivals
    for w in rivals:
        if len(rabbits) > 0 and random.random() < 0.8:
            near = min(rabbits, key=lambda r: abs(r[0] - w[0]) + abs(r[1] - w[1]))
            dx = near[0] - w[0]
            dy = near[1] - w[1]
            if abs(dx) >= abs(dy):
                w[0] += sign(dx)
            else:
                w[1] += sign(dy)
        else:
            m = random.choice(MOVES)
            w[0] = clamp(w[0] + m[0])
            w[1] = clamp(w[1] + m[1])
        w[2] -= 1
        for r in rabbits:
            if r[0] == w[0] and r[1] == w[1]:
                rabbits.remove(r)
                w[2] += MEAT_ENERGY
                break
    rivals = [w for w in rivals if w[2] > 0]


def is_drought(i):
    # drought = a rainy-season month (normal rain above the average) that got less than half of its normal rain
    return normal_rain[i] >= avg_rain and rain[i] < 0.5 * normal_rain[i]


def grow_grass():
    global grass
    # more rain = more grass grows
    chance = min(GROW_CHANCE * (0.6 + 0.4 * rain[month - 1] / avg_rain), 0.1)
    grass = grass | (np.random.rand(SIZE, SIZE) < chance)
    # very dry month: some grass dies
    if rain[month - 1] < 0.3 * avg_rain:
        grass = grass & (np.random.rand(SIZE, SIZE) < 0.9)
    # drought: a lot more grass dies
    if is_drought(month - 1):
        grass = grass & (np.random.rand(SIZE, SIZE) < DROUGHT_SURVIVE)


def step(dx, dy):
    # one key press = one month
    global energy, month, over, message, score, best_score, outcome
    if over:
        return
    wolf[0] = min(max(wolf[0] + dx, 0), SIZE - 1)
    wolf[1] = min(max(wolf[1] + dy, 0), SIZE - 1)
    energy -= 1
    month += 1
    eat_rabbit()
    move_rabbits()
    eat_rabbit()
    move_rivals()
    grow_grass()
    log.append({"month": month, "year": years[(month - 1) // 12],
                "rain": rain[month - 1], "grass": int(grass.sum()),
                "rabbits": len(rabbits), "rivals": len(rivals), "energy": energy,
                "drought": is_drought(month - 1)})
    if energy <= 0:
        over, message, outcome = True, "You starved!", "starved"
    elif len(rabbits) == 0:
        over, message, outcome = True, "Ecosystem collapsed!\n(all rabbits are gone)", "collapsed"
    elif month >= 120:
        over, message, outcome = True, "You survived 10 years!", "won"
    if over:
        score = month + 5 * eaten            # months survived + 5 points per rabbit eaten
        if score > best_score:
            best_score = score
            save_high_score(score)
        df = pd.DataFrame(log)
        df.to_csv("game_log.csv", index=False)
        print("Average rain:", round(df["rain"].mean(), 1), "mm")
        print("Correlation between rain and grass:", round(df["rain"].corr(df["grass"]), 2))
        table = make_table()
        table.to_csv("year_summary.csv")
        print(table)
        # add one row for this game to results.csv (write the header only the first time)
        row = {"region": region, "first_year": years[0], "months": month, "eaten": eaten,
               "score": score, "outcome": outcome, "drought_months": int(df["drought"].sum())}
        pd.DataFrame([row]).to_csv("results.csv", mode="a", index=False,
                                   header=not os.path.exists("results.csv"))


# ---------------- drawing ----------------

def draw_rabbit(px, py):
    o = CELL / 28      # sprites are drawn for a 28 pixel square, o scales them
    canvas.create_oval(px + 8 * o, py + 2 * o, px + 12 * o, py + 13 * o, fill="white", outline="gray")
    canvas.create_oval(px + 16 * o, py + 2 * o, px + 20 * o, py + 13 * o, fill="white", outline="gray")
    canvas.create_oval(px + 5 * o, py + 9 * o, px + 23 * o, py + 25 * o, fill="white", outline="gray")
    canvas.create_oval(px + 16 * o, py + 14 * o, px + 19 * o, py + 17 * o, fill="black")


def draw_wolf(px, py, color, ring=False):
    o = CELL / 28
    if ring:
        canvas.create_oval(px + 1 * o, py + 1 * o, px + 27 * o, py + 27 * o, outline="gold", width=2)
    canvas.create_polygon(px + 4 * o, py + 12 * o, px + 6 * o, py + 2 * o, px + 13 * o, py + 8 * o,
                          fill=color, outline="black")
    canvas.create_polygon(px + 24 * o, py + 12 * o, px + 22 * o, py + 2 * o, px + 15 * o, py + 8 * o,
                          fill=color, outline="black")
    canvas.create_oval(px + 3 * o, py + 7 * o, px + 25 * o, py + 26 * o, fill=color, outline="black")
    canvas.create_oval(px + 8 * o, py + 13 * o, px + 12 * o, py + 17 * o, fill="yellow")
    canvas.create_oval(px + 16 * o, py + 13 * o, px + 20 * o, py + 17 * o, fill="yellow")


def draw_bar(x, y, width, ratio, color):
    canvas.create_rectangle(x, y, x + width, y + 12, fill="#444", outline="")
    canvas.create_rectangle(x, y, x + width * min(max(ratio, 0), 1), y + 12, fill=color, outline="")


def draw_panel():
    x = SIZE * CELL + 15
    white = "white"
    i = max(month - 1, 0)
    canvas.create_rectangle(SIZE * CELL, 0, SIZE * CELL + PANEL, SIZE * CELL, fill="#222", outline="")
    canvas.create_text(x, 22, text="RAINFALL WOLF GAME", anchor="w", fill=white,
                       font=("Arial", 12, "bold"))
    canvas.create_text(x, 44, text=region.title(), anchor="w", fill="gray")

    canvas.create_text(x, 75, text="Energy: " + str(max(energy, 0)), anchor="w", fill=white)
    color = "green" if energy > 30 else "orange" if energy > 15 else "red"
    draw_bar(x, 88, PANEL - 30, energy / 60, color)
    canvas.create_text(x, 120, text=f"{MONTHS[i % 12]} {years[i // 12]}   (month {month}/120)",
                       anchor="w", fill=white)
    draw_bar(x, 133, PANEL - 30, month / 120, "dodgerblue")

    canvas.create_text(x, 170, text="Rabbits eaten: " + str(eaten), anchor="w", fill=white)
    canvas.create_text(x, 192, text="Rabbits alive: " + str(len(rabbits)), anchor="w", fill=white)
    canvas.create_text(x, 214, text="Rival wolves: " + str(len(rivals)), anchor="w", fill=white)
    canvas.create_text(x, 236, text=f"Rain this month: {rain[i]:.0f} mm", anchor="w",
                       fill="skyblue")
    if is_drought(i):
        canvas.create_text(x, 258, text=f"DROUGHT! Rain {rain[i] / normal_rain[i] * 100:.0f}% of normal",
                           anchor="w", fill="orange", font=("Arial", 9, "bold"))
    elif rain[i] < 0.3 * avg_rain:
        canvas.create_text(x, 258, text="Dry season", anchor="w", fill="gray")
    elif rain[i] > 2 * avg_rain:
        canvas.create_text(x, 258, text="Heavy rain!", anchor="w", fill="skyblue")

    if len(rabbits) < 10:
        canvas.create_text(x, 276, text="Rabbits low - ease off!", anchor="w", fill="red")

    draw_wolf(x, 290, "blue", True)
    canvas.create_text(x + 38, 304, text="You", anchor="w", fill=white)
    draw_wolf(x, 326, "red")
    canvas.create_text(x + 38, 340, text="Rival wolf", anchor="w", fill=white)
    draw_rabbit(x, 362)
    canvas.create_text(x + 38, 376, text="Rabbit", anchor="w", fill=white)

    canvas.create_text(x, 430, text="Arrow keys / WASD = move", anchor="w", fill="gray")
    canvas.create_text(x, 450, text="1 move = 1 month", anchor="w", fill="gray")
    canvas.create_text(x, 470, text="R restart   T table", anchor="w", fill="gray")
    canvas.create_text(x, 490, text="E = results by region", anchor="w", fill="gray")
    canvas.create_text(x, 518, text="Eat rabbits, keep some alive!", anchor="w", fill="gray")
    canvas.create_text(x, 548, text="Best score: " + str(best_score), anchor="w", fill="gold")
    canvas.create_text(x, 568, text="Regions played: " + str(len(regions_played)), anchor="w",
                       fill="gray")


def draw():
    canvas.delete("all")
    for y in range(SIZE):
        for x in range(SIZE):
            color = "#4c9a2a" if grass[y, x] else "#c8a878"
            canvas.create_rectangle(x * CELL, y * CELL, (x + 1) * CELL, (y + 1) * CELL,
                                    fill=color, outline="")
    for r in rabbits:
        draw_rabbit(r[0] * CELL, r[1] * CELL)
    for w in rivals:
        draw_wolf(w[0] * CELL, w[1] * CELL, "red")
    draw_wolf(wolf[0] * CELL, wolf[1] * CELL, "blue", True)
    draw_panel()
    if is_drought(max(month - 1, 0)):
        canvas.create_rectangle(2, 2, SIZE * CELL - 1, SIZE * CELL - 1, outline="orange", width=4)
    if over:
        canvas.create_rectangle(80, 200, SIZE * CELL - 80, 360, fill="white", outline="black")
        canvas.create_text(SIZE * CELL / 2, 250, text=message, font=("Arial", 22, "bold"),
                           fill="red", justify="center")
        canvas.create_text(SIZE * CELL / 2, 292, text=f"Score: {score}    Best: {best_score}",
                           font=("Arial", 14, "bold"), fill="black")
        canvas.create_text(SIZE * CELL / 2, 332, text="R restart   T table   E results",
                           font=("Arial", 13), fill="black")


def make_table():
    # yearly summary of the game using groupby
    df = pd.DataFrame(log)
    table = df.groupby("year").agg(total_rain=("rain", "sum"),
                                   avg_rabbits=("rabbits", "mean"),
                                   avg_grass=("grass", "mean"),
                                   lowest_energy=("energy", "min"),
                                   drought_months=("drought", "sum"))
    return table.round(1)


def show_table():
    win = tk.Toplevel(root)
    win.title("Yearly summary")
    text = "Year summary (from the game log)\n\n" + make_table().to_string()
    tk.Label(win, text=text, font=("Courier", 11), justify="left").pack(padx=15, pady=15)


def make_results():
    # every game ever played (from results.csv), summarised for each region
    df = pd.read_csv("results.csv")
    df["won"] = df["outcome"] == "won"
    table = df.groupby("region").agg(games=("score", "count"),
                                     avg_score=("score", "mean"),
                                     best_score=("score", "max"),
                                     win_rate=("won", "mean"),
                                     drought_months=("drought_months", "mean"))
    table["win_rate"] = table["win_rate"] * 100          # as a percentage
    return table.sort_values("win_rate", ascending=False).round(1)


def show_results():
    win = tk.Toplevel(root)
    win.title("Results by region")
    text = "All games played (results.csv)\n\n" + make_results().to_string()
    tk.Label(win, text=text, font=("Courier", 11), justify="left").pack(padx=15, pady=15)


def key_pressed(event):
    k = event.keysym
    if k in ("Up", "w"):
        step(0, -1)
    elif k in ("Down", "s"):
        step(0, 1)
    elif k in ("Left", "a"):
        step(-1, 0)
    elif k in ("Right", "d"):
        step(1, 0)
    elif k == "r":
        new_game()
    elif k == "t" and len(log) > 1:
        show_table()
    elif k == "e" and os.path.exists("results.csv"):
        show_results()
    draw()


if __name__ == "__main__":
    data = pd.read_csv("rainfall in india 1901-2015.csv")
    data["SUBDIVISION"] = data["SUBDIVISION"].str.strip().str.upper()
    counts = data["SUBDIVISION"].value_counts()
    regions = list(counts[counts >= 10].index)

    new_game()
    root = tk.Tk()
    root.title("Rainfall Wolf Game")
    canvas = tk.Canvas(root, width=SIZE * CELL + PANEL, height=SIZE * CELL)
    canvas.pack()
    root.bind("<Key>", key_pressed)
    draw()
    root.mainloop() 