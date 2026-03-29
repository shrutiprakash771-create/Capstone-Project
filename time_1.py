import random
import sys

#  Time conversion function
def to_min(t):
    try:
        h, m = map(int, t.split(":"))
        if 0 <= h < 24 and 0 <= m < 60:
            return h * 60 + m
    except Exception:
        pass
    return None

# Time formatting
def format_time(m):
    m = int(max(0, m % 1440))
    return f"{m//60:02d}:{m%60:02d}"

# Data cleaning function
def clean(arr):
    return [s.strip().lower() for s in arr if s.strip()]


def safe_int(prompt, default):
    try:
        raw = input(prompt)
        if not raw.strip():
            return default
        val = int(raw)
        return val if val >= 0 else default
    except Exception:
        return default


#  Inputs 
print("\n--- Timetable Generator ---")

days = safe_int("Number of days : ", 1)

subjects = clean(input("All subjects (comma separated): ").split(","))
weak = clean(input("Weak subjects: ").split(","))
strong = clean(input("Strong subjects: ").split(","))

# Fix subject categories
if not subjects:
    subjects = ["general study"]

if not weak:
    weak = subjects.copy()

if not strong:
    strong = subjects.copy()

strong = [s for s in strong if s not in weak]
normal = [s for s in subjects if s not in weak and s not in strong]
if not normal:
    normal = subjects.copy()


start_input = input("Start time (HH:MM, default 08:00): ")
start = to_min(start_input)
if start is None:
    start = 480  # 08:00  = 480 min

base_duration = safe_int("Base study duration (minutes): ", 60)
break_after = safe_int("Sessions before a break: ", 3)
base_break = safe_int("Break duration (minutes): ", 15)

study_hours = safe_int("Total study hours per day: ", 6)
break_hours = safe_int("Total break hours per day: ", 2)

study_minutes_goal = study_hours * 60
break_minutes_goal = break_hours * 60


#  Meals 
def get_meal(name):
    print(f"\nSet time for {name}:")
    s = to_min(input(f"  {name} start (HH:MM): "))
    e = to_min(input(f"  {name} end (HH:MM): "))
    if s is not None and e is not None and e > s:
        return (s, e)
    return (None, None)


meals = {
    "Breakfast": get_meal("Breakfast"),
    "Lunch": get_meal("Lunch"),
    "Dinner": get_meal("Dinner")
}


#  VALIDATION 

# Meal overlap check
meal_times = [(s, e, name) for name, (s, e) in meals.items() if s is not None]
meal_times.sort()

for i in range(len(meal_times) - 1):
    if meal_times[i][1] > meal_times[i + 1][0]:
        print(f"\n Error: {meal_times[i][2]} overlaps with {meal_times[i + 1][2]}!")
        sys.exit()

# Total meal time
total_meal_time = sum(e - s for s, e, _ in meal_times)

# Feasibility check
total_required = study_minutes_goal + break_minutes_goal + total_meal_time

if total_required > 1440:
    print("\nImpossible Schedule!")
    print("Total time exceeds 24 hours.")
    sys.exit()


#Subject Picker
def pick_subject():
    r = random.random()
    if r < 0.5:
        return random.choice(weak)
    elif r < 0.8:
        return random.choice(normal)
    else:
        return random.choice(strong)


#  Generator 
MIN_SESSION = 15

for d in range(1, days + 1):
    print("\n" + "═" * 15 + f" DAY {d} " + "═" * 15)

    current = start
    end_day = start + 1440

    session_count = 0
    meal_done = {k: False for k in meals}

    total_study_done = 0
    total_break_done = 0

    while current < end_day:

        # Stop condition (fixed)
        if (total_study_done >= study_minutes_goal and
            total_break_done >= break_minutes_goal and
            all(meal_done[m] or meals[m][0] is None for m in meals)):
            break

        #Handle Meals
        meal_triggered = False
        for name, (s, e) in meals.items():
            if s is None or meal_done[name]:
                continue

            if s <= current < e:
                meal_duration = max(0, e - current)
                if meal_duration > 0:
                    print(f" {name:<22} {format_time(current)} - {format_time(e)}")
                    current = e
                meal_done[name] = True
                meal_triggered = True
                break

        if meal_triggered:
            continue

        # Study 
        if total_study_done < study_minutes_goal:

            subject = pick_subject()

            duration = base_duration
            if subject in weak:
                duration += 15
            elif subject in strong:
                duration -= 10

            duration = max(25, min(duration, study_minutes_goal - total_study_done))

            # Next meal
            future_meals = [s for s, e, _ in meal_times if s > current]
            next_meal_start = min(future_meals) if future_meals else end_day

            if current + duration > next_meal_start:
                gap = max(0, next_meal_start - current)

                if gap >= MIN_SESSION:
                    print(f"{subject.title():<22} {format_time(current)} - {format_time(next_meal_start)}")
                    total_study_done += gap
                    current = next_meal_start
                else:
                    current = next_meal_start
            else:
                print(f"{subject.title():<22} {format_time(current)} - {format_time(current + duration)}")
                current += duration
                total_study_done += duration
                session_count += 1

            # Break 
            if session_count >= break_after and total_break_done < break_minutes_goal:

                future_meals = [s for s, e, _ in meal_times if s > current]
                next_meal_start = min(future_meals) if future_meals else end_day

                gap = max(0, next_meal_start - current)
                b_dur = min(base_break, break_minutes_goal - total_break_done, gap)

                if b_dur > 0:
                    print(f"{'Break':<22} {format_time(current)} - {format_time(current + b_dur)}")
                    current += b_dur
                    total_break_done += b_dur

                session_count = 0

        else:
            # Nothing left to do -> safely exit
            break

    print("═" * 40)
    print(f"Summary: {total_study_done//60}h {total_study_done%60}m Study | {total_break_done//60}h {total_break_done%60}m Break")