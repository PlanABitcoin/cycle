import os
import shutil
import subprocess
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

REPO_URL = "https://github.com/PlanABitcoin/cycle.git"

INDEX_FILE = "index.html"

BOOK_DIR = "book"
FIGURES_DIR = "figures"
IMAGES_DIR = "images"

COVER_FILE = os.path.join(BOOK_DIR, "cover.png")
BOOK_FILE = os.path.join(BOOK_DIR, "Bitcoin_book.pdf")


# ============================================================
# GIT
# ============================================================

def find_git():

    git_path = shutil.which("git")

    if git_path:
        return git_path

    paths = [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
    ]

    for p in paths:
        if os.path.exists(p):
            return p

    raise FileNotFoundError("Git not found")


GIT = find_git()


def run(cmd):

    print(" ".join(cmd))

    subprocess.run(cmd, check=True)


# ============================================================
# PREPARE FOLDERS
# ============================================================

def prepare_folders():

    os.makedirs(BOOK_DIR, exist_ok=True)

    os.makedirs(FIGURES_DIR, exist_ok=True)

    os.makedirs(IMAGES_DIR, exist_ok=True)


# ============================================================
# CREATE HOMEPAGE
# ============================================================

def create_homepage():

    html = """
<!DOCTYPE html>
<html>

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Bitcoin Cycle</title>

<link rel="icon" href="data:,">

<style>

body {

    margin: 0;

    font-family: Arial, sans-serif;

    background: #f6f4ef;

    color: #111;
}

.page {

    display: grid;

    grid-template-columns: 320px 1fr;

    min-height: 100vh;
}

/* ============================================================
   SIDEBAR
============================================================ */

.sidebar {

    background: #111;

    color: white;

    padding: 32px 24px;
}

.sidebar h2 {

    font-size: 30px;

    margin-bottom: 28px;
}

.sidebar a {

    display: block;

    color: white;

    text-decoration: none;

    font-size: 24px;

    padding: 22px 0;

    border-bottom: 1px solid #333;

    transition: 0.2s;
}

.sidebar a:hover {

    color: #f2a900;

    transform: translateX(6px);
}

/* ============================================================
   MAIN
============================================================ */

.main {

    display: flex;

    flex-direction: column;

    align-items: center;

    justify-content: center;

    padding: 45px;

    text-align: center;
}

.cover {

    width: 520px;

    max-width: 92vw;

    border-radius: 24px;

    box-shadow: 0 18px 60px rgba(0,0,0,0.45);
}

h1 {

    font-size: 56px;

    margin: 30px 0 8px;
}

h3 {

    font-size: 28px;

    font-weight: normal;

    margin: 0 0 32px;

    color: #555;
}

.book-button {

    display: inline-block;

    background: #111;

    color: white;

    padding: 26px 42px;

    border-radius: 18px;

    text-decoration: none;

    font-size: 30px;

    font-weight: bold;

    transition: 0.2s;
}

.book-button:hover {

    background: #f2a900;

    color: #111;

    transform: scale(1.03);
}

/* ============================================================
   MOBILE
============================================================ */

@media (max-width: 850px) {

    .page {

        grid-template-columns: 1fr;

        display: flex;

        flex-direction: column;
    }

    /* BOOK FIRST */
    .main {

        order: 1;
    }

    /* FIGURES AFTER */
    .sidebar {

        order: 2;

        text-align: center;
    }

    .sidebar h2 {

        font-size: 34px;
    }

    .sidebar a {

        font-size: 28px;

        padding: 24px 0;
    }

    .cover {

        width: 92vw;
    }

    h1 {

        font-size: 42px;
    }

    h3 {

        font-size: 30px;
    }

    .book-button {

        width: 85vw;

        font-size: 32px;

        padding: 28px 0;
    }
}

</style>

</head>

<body>

<div class="page">

    <!-- ====================================================
         SIDEBAR
    ===================================================== -->

    <div class="sidebar">

        <h2>Interactive Figures</h2>

        <a href="figures/f_cycle.html">
            Bitcoin Cycles
        </a>

        <a href="figures/f_pred.html">
            Prediction
        </a>

        
    
        <a href="figures/f_mining_cost.html">
            Mining Cost
        </a>

        <a href="figures/f_cycle_dates.html">
            Cycle Dates
        </a>

        <a href="figures/f_dem1.html">
            Diminishing Returns 1
        </a>

        <a href="figures/f_dem2.html">
            Diminishing Returns 2
        </a>

        <a href="figures/f_seg.html">
            Cycle Segments
        </a>

        <a href="figures/f_powerlaw.html">
            Power Law
        </a>

    </div>

    <!-- ====================================================
         MAIN BOOK SECTION
    ===================================================== -->

    <div class="main">

        <img
            class="cover"
            src="book/cover.png"
            alt="Bitcoin Cycle Book Cover"
        >

     <h1>Bitcoin Cycle</h1>

<h3>By Plan A</h3>



<p style="
    font-size:20px;
    margin:0 0 28px;
">
    <a
        href="mailto:planA.bitcoin@gmail.com"
        style="
            color:#f2a900;
            text-decoration:none;
            font-weight:bold;
        "
    >
        planA.bitcoin@gmail.com
    </a>
</p>

<a
    class="book-button"
    href="book/Bitcoin_book.pdf"
>
    Read the Book PDF
</a>
    </div>

</div>

</body>
</html>
"""

    with open(
        INDEX_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html)

    print("Created:", INDEX_FILE)


# ============================================================
# GIT PUSH
# ============================================================

def git_push():
    from github_publish import publish_to_github

    publish_to_github(
        add_paths=["index.html", ".nojekyll", BOOK_DIR, FIGURES_DIR, IMAGES_DIR],
        message=f"update website {datetime.now()}",
        log_file="run_log.txt",
    )


# ============================================================
# MAIN
# ============================================================
def open_local_website():
    import webbrowser

    if os.environ.get("SKIP_OPEN_BROWSER") == "1":
        print("Skipping local browser open.")
        return

    local_path = os.path.abspath("index.html")
    url = "file:///" + local_path.replace("\\", "/")

    print("Opening local website:")
    print(url)

    webbrowser.open_new_tab(url)
    
def main():

    prepare_folders()

    if not os.path.exists(COVER_FILE):

        print(
            "WARNING missing:",
            COVER_FILE
        )

    if not os.path.exists(BOOK_FILE):

        print(
            "WARNING missing:",
            BOOK_FILE
        )

    create_homepage()
    open_local_website()

    if os.environ.get("SKIP_GITHUB_PUSH") == "1":
        print("Skipping per-script GitHub push; runner will publish once at the end.")
    else:
        git_push()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
