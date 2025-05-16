# git_helper_pro/state.py

# This variable will store the absolute path to the currently selected local Git repository.
# It is initialized to None, meaning no repository is selected by default.
# Other modules (like git_actions.py and ui_menus.py) will read and update this variable.
current_repo_path = None