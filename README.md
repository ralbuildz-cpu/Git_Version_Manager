Here’s a cleaned-up README that matches how you’re shipping it now — no copy-paste, just `gvm` in the project folder. I kept your voice and the original structure, just updated the install/use parts and swapped the name.

---

**Known Issue:** When you open Roll Back, version 1 in the list is always your current state. The script blocks rolling back to that same state, so if you want to go back to the *previous* save, make a quick dummy save first ("temp"), then roll back to version 2. That pushes your current work into the history as a backup. You can delete the dummy later. Nothing is lost.

# gvm — Git Version Manager

No-hassle Git wrapper for DIY projects. This is a small tool that gives you a simple way to save versions of your project without learning Git. It wraps Git behind a text menu and handles the repetitive steps for you.

I wrote it because I kept losing track of changes and wanted something that worked like a "save game" for code. You run it, type a short note, and it stores a snapshot. Later you can flip back to any previous snapshot, and it creates a backup first so you don't lose your current work.

**What it does**
When you run `gvm`, it shows a menu with four main options:

Save a version – it looks at what you have changed, shows you the list of modified, added, or deleted files, and then asks for a note. For completely new files, it asks whether you want to include them or ignore them permanently. Once you confirm, it creates a save point.

View history – it prints a list of all your previous save points, with the date and the note you wrote. The most recent one is marked as current.

Roll back – you pick a version number from the history. The script backs up your current state as a new save point, then restores the files from that older version. You can undo the rollback the same way if you change your mind.

Update ignore list – you can add or remove files and folders that should be skipped. This is just an interactive way to edit the .gitignore file without opening a text editor.

The tool keeps everything local. It does not push anything to a remote server or require a GitHub account.

**Requirements**
- Python 3.6 or newer (only needed if you run the .py directly — the packaged builds include it)
- Git installed on your machine

If Git is not installed, gvm will detect that and offer to open the download page. Install Git, close the terminal, and run gvm again.

**Install**

Linux (Debian/Ubuntu):
```
<sudo apt install ./gvm_1.1.0_all.deb!>
```

Windows:
Download `gvm.exe` and put it somewhere on your PATH (for example `C:\Tools`). 

Or, if you prefer the source:
```
python gvm.py
```

**How to use it**
You no longer need to copy the script into each project. Open a terminal in the root folder of whatever project you want to track and run:

```
gvm
```

The first time you run it in a folder, it will ask if you want to set up version saving. Say yes, and it will initialise a Git repository and create a .gitignore file with common exclusions (cache folders, virtual environments, etc). It also makes the first save point automatically so you start with a clean baseline.

After that, just cd into any project and type `gvm` whenever you want to save progress or look at what you have done. It will find the existing history even if it was created by the old version_manager.py script.

**What it does not do**
It does not handle branches, merging, or remote repositories. It is deliberately simple. If you need full Git features, this tool is not the right fit. But for a solo project or a quick way to keep snapshots of a folder, it works fine.

**License**
This project is released under the MIT License. You can use it, modify it, and include it in other projects as long as you keep the original copyright notice. See the LICENSE file for the full terms.
