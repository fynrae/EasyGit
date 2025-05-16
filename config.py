import os
import platform

# Default editor for modifying files
DEFAULT_EDITOR = os.environ.get('EDITOR', 'nano' if platform.system() != 'Windows' else 'notepad')

# GitHub CLI command
GH_COMMAND = "gh" # Make sure 'gh' is in your PATH

# --- UI Configuration ---
CLEAR_SCREEN_BETWEEN_MENUS = True
CENTER_MENUS = True