# EasyGit 🚀

**Your Command-Line Companion for Simplified Git & GitHub Operations!**

---

## 👋 What is EasyGit?

EasyGit is a CLI-based tool designed to make common Git and GitHub tasks easier and more accessible, especially for those who prefer a menu-driven interface over memorizing numerous Git commands. Whether you're creating new repositories, pushing existing projects, managing remote repositories, or performing daily Git actions like staging, committing, and pushing, EasyGit aims to streamline your workflow.

This tool leverages the power of your existing `git` installation and the GitHub CLI (`gh`) to interact with your repositories, providing a guided experience through interactive menus.

**This very README and the initial project structure were pushed to GitHub using EasyGit itself!** Efficiency at its finest!

---

## ✨ Features

*   **Interactive Menus:** Navigate through options using arrow keys.
*   **GitHub Account Management:**
    *   Authenticate your GitHub account using the `gh` CLI.
    *   Check your current authentication status.
*   **Repository Creation:**
    *   Create new, empty repositories on GitHub and optionally clone them locally.
    *   Push an existing local project to a brand new GitHub repository (initializes Git locally if needed).
*   **Local Repository Operations:**
    *   View Git status (`git status`).
    *   Navigate project files and directories.
    *   View file content directly in the terminal (for quick peeks).
    *   Open files for editing in your default system editor.
    *   Create new files.
    *   Stage all changes or specific files (`git add`).
    *   Commit changes with a custom message (`git commit`).
    *   Push local commits to the remote repository (`git push`).
    *   Pull changes from the remote repository (`git pull`).
    *   Easily switch between different local repositories to work on.
*   **Remote Repository Management (via GitHub CLI):**
    *   View a list of your remote repositories on GitHub.
    *   Rename a remote repository on GitHub.
    *   Edit the description of a remote repository on GitHub.
    *   Delete a remote repository from GitHub (with multiple confirmations for safety).
*   **User-Friendly Interface:**
    *   Screen clearing for better readability between actions.
    *   Optional menu centering for a different visual style.
    *   Emoji indicators for actions!

---

##  Prerequisites

1.  **Python 3.6+:** The script is written in Python.
2.  **Git:** You must have Git installed and accessible in your system's PATH.
    *   Verify by typing `git --version` in your terminal.
3.  **GitHub CLI (`gh`):** Required for most GitHub-specific interactions (authentication, repository creation, remote management).
    *   Install it from [cli.github.com](https://cli.github.com/).
    *   Verify by typing `gh --version`.
    *   Authenticate it by running `gh auth login` in your terminal at least once, or use EasyGit's authentication option.

---

## 🛠️ Installation & Setup

1.  **Clone or Download EasyGit:**
    Get the EasyGit files. If it's hosted on GitHub:
    ```bash
    git clone https://github.com/fynrae/EasyGit.git 
    # Replace with the actual URL if different
    cd EasyGit 
    # Or cd into the directory containing main.py if you downloaded it
    ```
    If you have the files directly (e.g., in a folder named `easygit_project_files`), just navigate into that directory.

2.  **Install Dependencies:**
    EasyGit uses `inquirerpy` for interactive menus. Install it using pip:
    ```bash
    pip install -r requirements.txt
    ```
    (Or `python -m pip install -r requirements.txt` depending on your Python setup). The `requirements.txt` file should be in the root of the EasyGit project directory.

---

## 🚀 How to Use EasyGit

1.  **Navigate to the Script Directory:**
    Open your terminal and `cd` into the directory where `main.py` of EasyGit is located.

2.  **Run the Script:**
    ```bash
    python main.py
    ```

3.  **Follow the On-Screen Menus:**
    *   EasyGit will first perform some initial checks (Git installed, GitHub auth status).
    *   You'll be presented with the Main Menu.
    *   Use your **arrow keys** (Up/Down) to highlight an option and **Enter** to select it.

    **Main Menu Options:**
    *   `🔑 Authenticate GitHub Account`: Guides you through `gh auth login`.
    *   `☁️ Create New Empty GitHub Repo (& clone)`: Creates a fresh repository on GitHub and gives you the option to clone it to a new local directory.
    *   `🚀 Push Existing Local Project to New GitHub Repo`: Takes a local folder, initializes it as a Git repo (if needed), creates a corresponding GitHub repo, and pushes your project files.
    *   `💻 Work with Existing Local Repository`: Allows you to select a local Git project on your machine to perform operations on.
    *   `🛠️ Manage Remote GitHub Repositories`: View, rename, edit descriptions, or delete your repositories on GitHub.
    *   `🚪 Exit`: Quits the application.

    **Local Repository Menu (after selecting a local repo):**
    *   Standard Git operations like status, modify/create files, stage, commit, push, pull.
    *   Option to change the currently active local repository.

    **Manage Remote Repositories Menu:**
    *   Lists your repos, and allows renaming, editing descriptions, and deleting them.

4.  **Configuration (Optional):**
    You can modify settings in `config.py` (located in the same directory as `main.py`):
    *   `DEFAULT_EDITOR`: Change the default text editor used by EasyGit.
    *   `CLEAR_SCREEN_BETWEEN_MENUS`: Set to `True` (default) or `False` to control screen clearing.
    *   `CENTER_MENUS`: Set to `True` or `False` (default) to control the centering of menu titles and option text.


---

## 💡 Tips

*   **Authentication is Key:** For most GitHub interactions within EasyGit, ensure you've authenticated via the `gh` CLI. EasyGit will guide you or remind you.
*   **Path Inputs:** When asked for a path to a local project, you can use relative paths (e.g., `.` for current directory, `../my_other_project`) or absolute paths.
*   **Safety First:** For destructive actions like deleting a remote repository, EasyGit (and the underlying `gh` CLI) includes multiple confirmation steps. Read them carefully!
*   **Error Messages:** EasyGit tries to pass along error messages from `git` and `gh`. These can be very helpful for troubleshooting.

---

## 🤝 Contributing

Interested in contributing to EasyGit? That's great! Please feel free to fork the repository, make your changes, and submit a pull request.

---

Happy Gitting with EasyGit!