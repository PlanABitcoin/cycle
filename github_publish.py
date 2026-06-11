import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


REPO_URL = "https://github.com/PlanABitcoin/cycle.git"

# Use only your pen name / book identity in Git commits
USER_NAME = "Plan A"
USER_EMAIL = "plana.bitcoin@gmail.com"

DOMAIN = "cycbtc.com"

DEFAULT_ADD_PATHS = [
    "index.html",
    ".nojekyll",
    "CNAME",
    "figures",
    "book",
    "images",
]

LOCK_FILES = [
    Path(".git") / "packed-refs.lock",
    Path(".git") / "index.lock",
]


def find_git():
    git_path = shutil.which("git")
    if git_path:
        return git_path

    for path in [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
    ]:
        if os.path.exists(path):
            return path

    raise FileNotFoundError("Git not found")


def log(message, log_file=None):
    print(message)
    if log_file:
        with open(log_file, "a", encoding="utf-8") as handle:
            handle.write(f"{datetime.now()} {message}\n")


def git_process_running():
    try:
        for name in ["git.exe", "git-remote-https.exe"]:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {name}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                check=False,
            )
            if name.lower() in result.stdout.lower():
                return True
        return False
    except Exception:
        return False


def remove_stale_git_locks(log_file=None):
    existing_locks = [path for path in LOCK_FILES if path.exists()]
    if not existing_locks:
        return

    if git_process_running():
        names = ", ".join(str(path) for path in existing_locks)
        raise RuntimeError(f"Git lock file exists while Git is running: {names}")

    for path in existing_locks:
        log(f"Removing stale git lock: {path}", log_file)
        path.unlink()


def run_git(git, args, log_file=None, check=True):
    remove_stale_git_locks(log_file)

    cmd = [git] + args
    log(" ".join(cmd), log_file)

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.stdout:
        log(result.stdout.rstrip(), log_file)
    if result.stderr:
        log(result.stderr.rstrip(), log_file)

    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            cmd,
            output=result.stdout,
            stderr=result.stderr,
        )

    return result


def ensure_cname_file(log_file=None):
    with open("CNAME", "w", encoding="utf-8") as handle:
        handle.write(DOMAIN + "\n")

    log(f"Created/updated CNAME with domain: {DOMAIN}", log_file)


def ensure_nojekyll_file(log_file=None):
    Path(".nojekyll").touch()
    log("Created/updated .nojekyll", log_file)


def ensure_repository(git, log_file=None):
    if not Path(".git").exists():
        run_git(git, ["init"], log_file)
        run_git(git, ["branch", "-M", "main"], log_file)

    remotes = run_git(git, ["remote"], log_file, check=False).stdout.split()

    if "origin" in remotes:
        run_git(git, ["remote", "set-url", "origin", REPO_URL], log_file)
    else:
        run_git(git, ["remote", "add", "origin", REPO_URL], log_file)

    run_git(git, ["config", "user.name", USER_NAME], log_file)
    run_git(git, ["config", "user.email", USER_EMAIL], log_file)


def publish_to_github(add_paths=None, message=None, log_file=None):
    git = find_git()
    add_paths = add_paths or DEFAULT_ADD_PATHS
    message = message or f"update website {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    try:
        log("Publishing to GitHub once at end of workflow...", log_file)
        log(f"Using Git: {git}", log_file)

        ensure_repository(git, log_file)
        ensure_cname_file(log_file)
        ensure_nojekyll_file(log_file)

        for path in add_paths:
            if Path(path).exists():
                run_git(git, ["add", "-f", path], log_file)
            else:
                log(f"Skipping missing path: {path}", log_file)

        run_git(git, ["status", "--short"], log_file)

        diff = run_git(git, ["diff", "--cached", "--quiet"], log_file, check=False)

        if diff.returncode == 0:
            log("Nothing to commit.", log_file)
        elif diff.returncode == 1:
            run_git(git, ["commit", "-m", message], log_file)
        else:
            raise subprocess.CalledProcessError(
                diff.returncode,
                [git, "diff", "--cached", "--quiet"],
            )

        run_git(git, ["push", "-u", "origin", "main"], log_file)

        log("GitHub updated successfully.", log_file)
        log("Website:", log_file)
        log(f"https://{DOMAIN}/", log_file)

        return True

    except Exception as exc:
        log(f"GitHub publish failed: {exc}", log_file)
        return False


if __name__ == "__main__":
    publish_to_github()