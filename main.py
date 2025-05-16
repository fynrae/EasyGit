# git_helper_pro/main.py
import os
import sys

# This setup helps if running main.py directly from its directory
try:
    import config
    import utils
    import ui_menus
    import state
except ImportError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
         sys.path.insert(0, current_dir)
    import config
    import utils
    import ui_menus
    import state


def initialize_app():
    """Perform initial checks and setup."""
    utils.clear_screen()
    print("🚀 Welcome to EasyGit! 🚀")
    print("-" * 40) # Wider separator
    
    if not utils.check_git_installed(): # This function prints its own messages
        # Message already printed by check_git_installed
        return False
    print("-" * 40)

    # Check and display GitHub authentication status
    print("🔎 Checking GitHub Authentication Status...")
    # utils.ensure_gh_installed_and_authed() will print details.
    # We call it here for the initial check. It will also be called by actions requiring auth.
    # It returns True if authed, False otherwise. We don't strictly need its return value here
    # as its side effect of printing is what we want for the initial display.
    # However, we should check if 'gh' is even installed first.
    _, _, gh_version_code = utils.run_command([config.GH_COMMAND, "--version"], capture_output=True)
    if gh_version_code == 0:
        utils.ensure_gh_installed_and_authed() # This will print the auth status
    else:
        print(f"❌ GitHub CLI ('{config.GH_COMMAND}') not found. Some features like remote repo management will be unavailable.")
        print(f"   Please install it from: https://cli.github.com/")

    print("-" * 40)
    print("✅ Initial checks complete.")
    input("Press Enter to continue to the main menu...")
    return True


if __name__ == "__main__":
    if initialize_app():
        ui_menus.display_main_menu()
    else:
        print("\nApplication initialization failed. Exiting.")
        input("Press Enter to exit.")