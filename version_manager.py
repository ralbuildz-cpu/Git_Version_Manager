```python
#!/usr/bin/env python3
"""
Version Manager – with interactive ignore, safe rollback, and user-friendly menus.
No Git knowledge required.
"""

import os
import sys
import subprocess
import webbrowser
import platform
from pathlib import Path
from datetime import datetime

# ==================== CONFIG ====================
VERSION = "1.1.0"
PROJECT_NAME = Path.cwd().name
HASH_FILE = ".file_hashes.json"
IGNORE_DIRS = {".git", "__pycache__", "venv", ".venv", "env", ".env"}
IGNORE_FILES = {HASH_FILE, ".gitignore", "version_manager.py"}

# Operating system detection
SYSTEM = platform.system()
IS_WINDOWS = SYSTEM == "Windows"
IS_LINUX = SYSTEM == "Linux"

# Try to enable ANSI colors on Windows (no dependency if not available)
try:
    from colorama import just_fix_windows_console
    just_fix_windows_console()
except ImportError:
    pass

# Default .gitignore content (will be appended to)
DEFAULT_GITIGNORE = """
# Python cache
__pycache__/
*.pyc
*.pyo

# Virtual environments
venv/
.venv/
env/

# Version manager internal
.file_hashes.json

# Linux
*~
*.swp
*.swo

# macOS
.DS_Store

# Windows
Thumbs.db
desktop.ini
"""

# ==================== DISPLAY HELPERS ====================
def clear_screen():
    """Clear the terminal screen in a cross-platform way, only if stdout is a tty."""
    if sys.stdout.isatty():
        os.system("cls" if IS_WINDOWS else "clear")

def header():
    clear_screen()
    print("\n  " + "=" * 44)
    print(f"    {PROJECT_NAME}  --  Version Manager v{VERSION}")
    print("  " + "=" * 44 + "\n")

def ok(msg):   print(f"  [OK] {msg}" + "\033[0m")
def err(msg):  print(f"  [!!] {msg}" + "\033[0m")
def info(msg): print(f"       {msg}")
def warn(msg): print(f"  [>>] {msg}")

def pause():
    input("\n  Press Enter to go back to the menu...")

# ==================== GIT SETUP ====================
def git_installed():
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def ensure_git():
    if git_installed():
        return True
    header()
    err("Git is not installed on this computer.")
    print("\n  Git is a free tool that keeps saved copies of your project.")
    print("  Installing it takes about 2 minutes.\n")

    if IS_WINDOWS:
        git_url = "https://git-scm.com/download/win"
        install_text = (
            "Download and run the installer.\n"
            "Click Next through the default options."
        )
    elif IS_LINUX:
        git_url = "https://git-scm.com/download/linux"
        install_text = (
            "Install Git using your package manager.\n\n"
            "For Mint/Ubuntu:\n"
            "sudo apt install git\n\n"
            "For Fedora:\n"
            "sudo dnf install git"
        )
    else:
        git_url = "https://git-scm.com/downloads"
        install_text = "Install Git using your operating system's package manager."

    print(f"  Download from:  {git_url}")
    print(f"\n  {install_text}\n")

    choice = input("  Open the download page now? (Y/N): ").strip().lower()
    if choice == 'y':
        webbrowser.open(git_url)
    pause()
    return False

def ensure_git_config(repo_root):
    """Set local user.name and user.email if missing."""
    for key in ["user.name", "user.email"]:
        rc, out, _ = run_git("config", "--local", key, repo_root=repo_root, capture=True)
        if rc != 0 or not out.strip():
            if key == "user.name":
                val = f"{PROJECT_NAME} User"
            else:
                safe_name = PROJECT_NAME.lower().replace(" ", "_")
                val = f"user@{safe_name}.local"
            run_git("config", "--local", key, val, repo_root=repo_root)

def run_git(*args, repo_root=None, capture=False):
    if repo_root is None:
        repo_root = Path.cwd()
    cmd = ["git"] + list(args)
    try:
        if capture:
            result = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        else:
            subprocess.run(cmd, cwd=str(repo_root), check=True, capture_output=True)
            return 0, "", ""
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr
    except FileNotFoundError:
        return 1, "", "Git not found"

def repo_root():
    cwd = Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / ".git").exists():
            return p
    return None

def init_repo(repo_root):
    if (repo_root / ".git").exists():
        return True
    header()
    warn("First-time setup – initialising version control.")
    print("\n  This will set up version saving for your project.")
    print("  It only needs to happen once.\n")
    choice = input("  Set up version saving now? (Y/N): ").strip().lower()
    if choice != 'y':
        return False

    gitignore = repo_root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(DEFAULT_GITIGNORE, encoding="utf-8")
        ok(".gitignore written – junk files will be excluded.")

    run_git("init", repo_root=repo_root)
    ensure_git_config(repo_root)
    run_git("add", "-A", repo_root=repo_root)
    run_git("commit", "-m", "First save point – version manager initialized", repo_root=repo_root)
    ok("Version saving is ready. Your first save point has been created.")
    pause()
    return True

# ==================== CORE: SAVE ====================
def get_untracked_files(repo_root):
    """Return list of untracked file paths (relative) from git status."""
    rc, out, _ = run_git("status", "--porcelain", repo_root=repo_root, capture=True)
    if rc != 0:
        return []
    untracked = []
    for line in out.splitlines():
        if line.startswith("??"):
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                untracked.append(parts[1].strip())
    return untracked

def save_version():
    header()
    print("  SAVE A VERSION")
    print("  ---------------------------------------------\n")

    root = repo_root()
    if not root:
        err("No Git repository found. Please run setup first.")
        pause()
        return

    rc, status, _ = run_git("status", "--porcelain", repo_root=root, capture=True)
    if rc != 0 or not status.strip():
        info("No changes have been made since your last save.")
        info("There is nothing new to save right now.")
        pause()
        return

    print("  Files changed since last save:\n")
    for line in status.splitlines():
        if len(line) < 3:
            continue
        flag = line[:2].strip()
        file = line[3:]
        color = ""
        label = ""
        if flag == "M":
            color = "\033[93m"
            label = "Modified"
        elif flag == "A":
            color = "\033[92m"
            label = "Added"
        elif flag == "D":
            color = "\033[91m"
            label = "Deleted"
        elif flag == "??":
            color = "\033[96m"
            label = "New file"
        else:
            color = "\033[90m"
            label = "Changed"
        print(f"    {color}{label:9} : {file}\033[0m")

    untracked = get_untracked_files(root)
    if untracked:
        print("\n  Some files are completely new (untracked).")
        print("  You can choose to include them or ignore them forever.\n")
        gitignore_path = root / ".gitignore"

        to_ignore = []
        to_include = []
        skip_all = None

        for f in untracked:
            if skip_all == 'y':
                to_include.append(f)
                continue
            if skip_all == 'n':
                to_ignore.append(f)
                continue

            while True:
                choice = input(f"  Include '{f}' in the repo? (Y)es / (N)o / (A)ll yes / (I)gnore all: ").strip().lower()
                if choice == 'y':
                    to_include.append(f)
                    break
                elif choice == 'n':
                    to_ignore.append(f)
                    break
                elif choice == 'a':
                    skip_all = 'y'
                    to_include.append(f)
                    break
                elif choice == 'i':
                    skip_all = 'n'
                    to_ignore.append(f)
                    break
                else:
                    print("  Please enter Y, N, A, or I.")

        if to_ignore:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write("\n# User-ignored files\n")
                for item in to_ignore:
                    f.write(f"{item}\n")
            ok(f"Ignored {len(to_ignore)} file(s) – added to .gitignore.")
            run_git("add", ".gitignore", repo_root=root)

    print("\n  Write a short note about what you changed.")
    print("  Examples:  'Fixed the bug'  /  'Added new feature'\n")
    msg = input("  Your note: ").strip()
    if not msg:
        warn("No note entered. Save cancelled.")
        pause()
        return

    run_git("add", "-A", repo_root=root)
    rc, out, err = run_git("commit", "-m", msg, repo_root=root, capture=True)
    if rc != 0:
        err(f"Commit failed: {err}")
    else:
        ok(f"Version saved: \"{msg}\"")
    pause()

# ==================== VIEW HISTORY ====================
def get_commits(repo_root):
    rc, out, _ = run_git("log", "--pretty=format:%h|%ai|%s", repo_root=repo_root, capture=True)
    if rc != 0 or not out:
        return []
    commits = []
    for line in out.splitlines():
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        h, dt, subj = parts
        try:
            dt_obj = datetime.fromisoformat(dt[:19])
            dt_str = dt_obj.strftime("%b %d %Y   %I:%M %p")
        except:
            dt_str = dt
        commits.append({"hash": h, "date": dt_str, "subject": subj})
    return commits

def show_history():
    header()
    print("  VERSION HISTORY  (newest first)")
    print("  ---------------------------------------------\n")

    root = repo_root()
    if not root:
        info("No repository found.")
        pause()
        return None

    commits = get_commits(root)
    if not commits:
        info("No saved versions found.")
        pause()
        return None

    for i, c in enumerate(commits, start=1):
        num = str(i).rjust(3)
        note = c["subject"]
        if len(note) > 50:
            note = note[:47] + "..."
        if i == 1:
            print(f"  {num}.  {c['date']}   {note}   [CURRENT]\033[0m")
        else:
            print(f"  {num}.  {c['date']}   {note}")
    print()

    pause()
    return commits

# ==================== SAFE ROLLBACK ====================
def rollback():
    header()
    commits = get_commits(repo_root())
    if not commits:
        info("No versions to roll back to.")
        pause()
        return

    print("  VERSION HISTORY  (newest first)")
    print("  ---------------------------------------------\n")
    for i, c in enumerate(commits, start=1):
        num = str(i).rjust(3)
        note = c["subject"][:50]
        print(f"  {num}.  {c['date']}   {note}")

    print("\n  ROLL BACK TO AN OLDER VERSION")
    print("  ---------------------------------------------")
    warn("This replaces your current files with an older version.")
    warn("Your current work is saved as a backup first – nothing is lost.\n")

    choice = input("  Enter the version number to roll back to (or ENTER to cancel): ").strip()
    if not choice:
        return
    if not choice.isdigit():
        err("That is not a valid number.")
        pause()
        return
    num = int(choice)
    if num < 1 or num > len(commits):
        err(f"Please pick a number between 1 and {len(commits)}.")
        pause()
        return
    if num == 1:
        info("Version 1 is already your current version. Nothing to roll back to.")
        pause()
        return

    target = commits[num-1]
    print(f"\n  You chose:")
    print(f"    Version {num}  --  {target['date']}  --  {target['subject']}\n")
    confirm = input("  Type YES to confirm the rollback: ").strip()
    if confirm != "YES":
        info("Rollback cancelled. Nothing was changed.")
        pause()
        return

    root = repo_root()
    run_git("add", "-A", repo_root=root)
    rc, out, _ = run_git("status", "--porcelain", repo_root=root, capture=True)
    if out.strip():
        run_git("commit", "-m", f"Auto-backup before rollback to: {target['subject']}", repo_root=root)
        ok("Current files backed up as a new save point.")

    run_git("checkout", target["hash"], "--", ".", repo_root=root)
    run_git("add", "-A", repo_root=root)
    run_git("commit", "-m", f"Rolled back to version {num}: {target['subject']}", repo_root=root)

    print()
    ok(f"Rollback complete. Your project is now at version {num}.")
    info("The rollback is saved as a new version – you can undo it the same way.")
    pause()

# ==================== UPDATE IGNORE LIST ====================
def edit_ignore():
    header()
    print("  MANAGE IGNORE LIST")
    print("  ---------------------------------------------\n")

    root = repo_root()
    if not root:
        err("No repository found.")
        pause()
        return

    gitignore = root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(DEFAULT_GITIGNORE, encoding="utf-8")
        ok("Created new .gitignore file.")
        run_git("add", ".gitignore", repo_root=root)
        run_git("commit", "-m", "Initial .gitignore", repo_root=root)

    while True:
        print("\n  Current ignored patterns (from .gitignore):")
        lines = gitignore.read_text(encoding="utf-8").splitlines()
        shown = 0
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                print(f"    - {line}")
                shown += 1
        if shown == 0:
            print("    (No custom ignore patterns set)")

        print("\n  What do you want to do?")
        print("  1. Add a file/folder to ignore list")
        print("  2. Remove a pattern from ignore list")
        print("  3. Back to main menu")
        choice = input("  Enter a number: ").strip()

        if choice == "1":
            candidates = []
            for dirpath, dirnames, filenames in os.walk(root):
                rel_dir = Path(dirpath).relative_to(root)
                if rel_dir == Path("."):
                    rel_dir = Path("")
                if rel_dir.parts and rel_dir.parts[0] == ".git":
                    continue

                for f in filenames:
                    rel_path = rel_dir / f
                    if rel_path.name in ["version_manager.py", ".gitignore"]:
                        continue
                    rc, _, _ = run_git("check-ignore", "-q", str(rel_path), repo_root=root, capture=True)
                    if rc != 0:
                        candidates.append(str(rel_path))

            if not candidates:
                info("No files found that are not already ignored.")
                continue

            print("\n  Select a file to ignore (enter the number, or 'a' for all, 'q' to cancel):")
            for i, f in enumerate(candidates, start=1):
                print(f"    {i}. {f}")

            sel = input("  Choice: ").strip()
            if sel == 'q':
                continue

            to_add = []
            if sel == 'a':
                to_add = candidates
            else:
                try:
                    idx = int(sel) - 1
                    if 0 <= idx < len(candidates):
                        to_add = [candidates[idx]]
                    else:
                        err("Invalid number.")
                        continue
                except ValueError:
                    err("Invalid input. Enter a number, 'a', or 'q'.")
                    continue

            if not to_add:
                continue

            with open(gitignore, "a", encoding="utf-8") as f:
                f.write("\n# User-added ignores\n")
                for item in to_add:
                    f.write(f"{item}\n")

            ok(f"Added {len(to_add)} pattern(s) to .gitignore.")
            run_git("add", ".gitignore", repo_root=root)
            run_git("commit", "-m", "Updated ignore list (added files)", repo_root=root)
            ok("Changes committed.")

        elif choice == "2":
            lines = gitignore.read_text(encoding="utf-8").splitlines()
            selectable = []
            print("\n  Select a pattern to remove (enter the number, or 'a' for all, 'q' to cancel):")
            display_idx = 1
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    print(f"    {display_idx}. {line}")
                    selectable.append(i)
                    display_idx += 1

            if not selectable:
                info("No patterns to remove.")
                continue

            sel = input("  Choice: ").strip()
            if sel == 'q':
                continue

            to_remove = []
            if sel == 'a':
                to_remove = selectable
            else:
                try:
                    idx = int(sel) - 1
                    if 0 <= idx < len(selectable):
                        to_remove = [selectable[idx]]
                    else:
                        err("Invalid number.")
                        continue
                except ValueError:
                    err("Invalid input. Enter a number, 'a', or 'q'.")
                    continue

            if not to_remove:
                continue

            new_lines = lines.copy()
            for idx in sorted(to_remove, reverse=True):
                del new_lines[idx]

            gitignore.write_text("\n".join(new_lines), encoding="utf-8")
            ok(f"Removed {len(to_remove)} pattern(s) from .gitignore.")
            run_git("add", ".gitignore", repo_root=root)
            run_git("commit", "-m", "Updated ignore list (removed patterns)", repo_root=root)
            ok("Changes committed.")

        elif choice == "3":
            break
        else:
            warn("Invalid choice. Enter 1, 2, or 3.")

# ==================== MAIN ====================
def main():
    if not ensure_git():
        sys.exit(1)

    root = repo_root()
    if root is None:
        root = Path.cwd()
        if not init_repo(root):
            sys.exit(1)

    ensure_git_config(root)

    while True:
        header()
        print("  What would you like to do?\n")
        print("  1.  Save a version       -- snapshot your current work")
        print("  2.  View history         -- see all your save points")
        print("  3.  Roll back            -- go back to a previous save point")
        print("  4.  Update ignore list   -- edit which files get skipped")
        print("  5.  Exit")
        choice = input("\n  Enter a number: ").strip()

        if choice == "1":
            save_version()
        elif choice == "2":
            show_history()
        elif choice == "3":
            rollback()
        elif choice == "4":
            edit_ignore()
        elif choice == "5":
            print("\n  👋 Goodbye!")
            sys.exit(0)
        else:
            warn("Please enter a number between 1 and 5.")
            pause()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  👋 Exited by user.")
        sys.exit(0)
```
