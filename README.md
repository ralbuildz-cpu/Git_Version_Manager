Known Issue:
  When rolling back, version 1 is always your current commit. The script prevents rolling back to that same state, so if you want to go back to the previous working version, first make a small dummy change and save a new version. That pushes the older version to position 2, and then you can roll back to it normally. No data is lost, and you can later delete the dummy commit if needed.

# Git_Version_Manager
No Hassle Git Manager for DIY projects
Version Manager
This is a small Python script that gives you a simple way to save versions of your project without learning Git. It wraps Git behind a text menu and handles the repetitive steps for you.

I wrote it because I kept losing track of changes and wanted something that worked like a "save game" for code. You run it, type a short note, and it stores a snapshot. Later you can flip back to any previous snapshot, and it creates a backup first so you don't lose your current work.

What it does
When you run the script, it shows a menu with four main options:

Save a version – it looks at what you have changed, shows you the list of modified, added, or deleted files, and then asks for a note. For completely new files, it asks whether you want to include them or ignore them permanently. Once you confirm, it creates a save point.

View history – it prints a list of all your previous save points, with the date and the note you wrote. The most recent one is marked as current.

Roll back – you pick a version number from the history. The script backs up your current state as a new save point, then restores the files from that older version. You can undo the rollback the same way if you change your mind.

Update ignore list – you can add or remove files and folders that should be skipped. This is just an interactive way to edit the .gitignore file without opening a text editor.

The script keeps everything local. It does not push anything to a remote server or require a GitHub account.

Requirements
Python 3.6 or newer

Git installed on your machine

If Git is not installed, the script will detect that and offer to open the download page. You can install Git, close the terminal, and then run the script again.

How to use it
Copy the script into the root folder of whatever project you want to track. Open a terminal in that folder and run:

python version_manager.py

The first time you run it, it will ask if you want to set up version saving. Say yes, and it will initialise a Git repository and create a .gitignore file with common Python exclusions (cache folders, virtual environments, the hash file it uses internally). It also makes the first save point automatically so you start with a clean baseline.

After that, just run the script whenever you want to save progress or look at what you have done.

What it does not do
It does not handle branches, merging, or remote repositories. It is deliberately simple. If you need full Git features, this script is not the right tool. But for a solo project or a quick way to keep snapshots of a folder, it works fine.

License
This project is released under the MIT License. You can use it, modify it, and include it in other projects as long as you keep the original copyright notice. See the LICENSE file for the full terms.

