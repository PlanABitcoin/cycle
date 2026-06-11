import subprocess
import sys
import os
from pathlib import Path

from datetime import datetime
from github_publish import publish_to_github

with open("run_log.txt", "a") as f:
    f.write(f"Started: {datetime.now()}\n")

BASE = Path(__file__).parent

PROGRAMS = [

    "Creat_block_number_2_date.py",
    # Bitcoin cycles
   # "Bitcoin_book_only_f_cycle.py",
    "Bitcoin_book_only_f_cycle_web.py",

    # Cycle evidence
    #"Bitcoin_book_only_f_cycle_evidence.py",
    "Bitcoin_book_only_f_cycle_evidence_web.py",

    # Prediction
    "Bitcoin_book_final_f_pred_web.py",

    # Mining cost
    #"Bitcoin_book_only_f_mining_cost.py",
    "Bitcoin_book_only_f_mining_cost_web.py",
    
    # Dates
    "Bitcoin_book_only_f_dates_web.py",

    # Diminishing returns
    #"Bitcoin_book_only_f_dem1.py",
    "Bitcoin_book_only_f_dem1_web.py",

    #"Bitcoin_book_only_f_dem2.py",
    "Bitcoin_book_only_f_dem2_web.py",

    # Power law
    #"Bitcoin_book_only_power_law.py",
    "Bitcoin_book_only_power_law_web.py",

    # ETF
    # Website + GitHub push
    "main_website.py",
]


for program in PROGRAMS:

    file_path = BASE / program

    if not file_path.exists():
        print(f"\nSKIPPING (not found): {program}")
        continue

    print("\n" + "=" * 70)
    print(f"RUNNING: {program}")
    print("=" * 70)

    try:
        env = os.environ.copy()
        env["SKIP_GITHUB_PUSH"] = "1"
        env["SKIP_OPEN_BROWSER"] = "1"

        subprocess.run(
            [sys.executable, str(file_path)],
            check=True,
            env=env
        )

        print(f"SUCCESS: {program}")

    except subprocess.CalledProcessError as e:

       print(f"FAILED: {program}")
       print(e)

    # Continue automatically
    continue

with open("run_log.txt", "a") as f:
    f.write(f"Finished: {datetime.now()}\n\n")

publish_to_github(
    add_paths=[
        "index.html",
        ".nojekyll",
        "figures",
        "book",
        "images",
    ],
    message=f"update website {datetime.now()}",
    log_file="run_log.txt",
)

print("\nDONE.")
