
import os
import shutil
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
import git_actions
import state
import utils
import config

def _center_text_in_terminal(text_to_center):
    terminal_width = shutil.get_terminal_size((80, 20)).columns
    return text_to_center.center(terminal_width)

def _get_formatted_message(base_message):
    if config.CENTER_MENUS:
        return _center_text_in_terminal(base_message)
    return base_message

def _get_choices_with_centered_names(choices_data):
    processed_choices = []
    terminal_width = shutil.get_terminal_size((80, 20)).columns
    for item in choices_data:
        value, name, enabled = None, None, True
        if isinstance(item, Choice): value, name, enabled = item.value, item.name, item.enabled
        elif isinstance(item, tuple) and len(item) == 2: value, name = item
        elif isinstance(item, tuple) and len(item) == 3: value, name, enabled = item
        else: raise ValueError(f"Unsupported choice item format: {item}")

        if config.CENTER_MENUS:
            centered_name = name.center(terminal_width)
            processed_choices.append(Choice(value=value, name=centered_name, enabled=enabled))
        else:
            processed_choices.append(Choice(value=value, name=name, enabled=enabled))
    return processed_choices

def display_manage_remote_menu():
    while True:
        utils.clear_screen()
        message_prompt = _get_formatted_message("Manage Remote GitHub Repositories:")
        choices_definition = [
            ("view_remote", "👁️ View My Remote Repositories"),
            ("rename_remote", "✏️ Rename Remote Repository"),
            ("edit_desc_remote", "📜 Edit Remote Repository Description"),
            ("delete_remote", "🗑️ Delete Remote Repository"),
            ("back", "🔙 Back to Main Menu"),
        ]
        action = inquirer.select(
            message=message_prompt,
            choices=_get_choices_with_centered_names(choices_definition),
            pointer="❯ " if not config.CENTER_MENUS else "  ", qmark="🛠️ " if not config.CENTER_MENUS else "  ", cycle=True
        ).execute()
        utils.clear_screen()
        if action == "view_remote": git_actions.view_remote_repositories()
        elif action == "rename_remote": git_actions.rename_remote_repository()
        elif action == "edit_desc_remote": git_actions.edit_remote_repository_description()
        elif action == "delete_remote": git_actions.delete_remote_repository()
        elif action == "back": break
        else: print("Invalid choice.")
        if action != "back": inquirer.text(message="Press Enter to continue...").execute()

def display_local_repo_menu():
    if not state.current_repo_path:
        utils.clear_screen(); print("Error: No repository selected for local operations.")
        if not git_actions.set_current_repository():
            inquirer.text(message="Press Enter to return to main menu...").execute(); return
    while True:
        utils.clear_screen()
        repo_name = os.path.basename(state.current_repo_path) if state.current_repo_path else "N/A"
        if state.current_repo_path and (not os.path.isdir(state.current_repo_path) or not utils.is_git_repository(state.current_repo_path)):
            print(f"⚠️ Current repository path '{state.current_repo_path}' is no longer valid or not a Git repo.")
            state.current_repo_path = None
            if not git_actions.set_current_repository():
                inquirer.text(message="Press Enter to return to main menu...").execute(); return
            utils.clear_screen(); repo_name = os.path.basename(state.current_repo_path) if state.current_repo_path else "N/A"
        message_prompt = _get_formatted_message(f"Local Repo ({repo_name}): What would you like to do?")
        choices_definition = [
            ("status", "📊 View Status"), ("modify", "📝 Modify/Create File"), ("stage", "➕ Stage Changes"),
            ("commit", "✉️ Commit Changes"), ("push", "⬆️ Push Changes"), ("pull", "⬇️ Pull Changes"),
            ("change_repo", "🔄 Change Current Repository"), ("back", "🔙 Back to Main Menu"),
        ]
        action = inquirer.select(
            message=message_prompt, choices=_get_choices_with_centered_names(choices_definition),
            pointer="❯ " if not config.CENTER_MENUS else "  ", qmark="⚙️ " if not config.CENTER_MENUS else "  ", cycle=True
        ).execute()
        utils.clear_screen()
        if action == "status": git_actions.view_status()
        elif action == "modify": git_actions.modify_file()
        elif action == "stage": git_actions.stage_changes()
        elif action == "commit": git_actions.commit_changes()
        elif action == "push": git_actions.push_changes()
        elif action == "pull": git_actions.pull_changes()
        elif action == "change_repo": git_actions.set_current_repository(); continue
        elif action == "back": break
        else: print("Invalid choice.")
        if action not in ["back", "change_repo"]: inquirer.text(message="Press Enter to continue...").execute()


def display_main_menu():
    """Displays and handles the main application menu."""
    while True:
        utils.clear_screen()
        current_repo_info = f"(Active: {state.current_repo_path})" if state.current_repo_path else "(No active repo)"
        base_message = f"EasyGit {current_repo_info} - Main Menu:"
        message_prompt = _get_formatted_message(base_message)

        choices_definition = [
            ("auth_github", "🔑 Authenticate GitHub Account"),
            ("create_new_empty_remote", "☁️ Create New Empty GitHub Repo (and clone)"),
            ("push_existing_project", "🚀 Push Existing Local Project to New GitHub Repo"),
            ("work_local", "💻 Work with Existing Local Repository"),
            ("manage_remote", "🛠️ Manage Remote GitHub Repositories"),
            (None, "🚪 Exit"),
        ]
        
        action = inquirer.select(
            message=message_prompt,
            choices=_get_choices_with_centered_names(choices_definition),
            default="work_local" if state.current_repo_path else "auth_github",
            pointer="❯ " if not config.CENTER_MENUS else "  ",
            qmark="" if not config.CENTER_MENUS else "  ",
            cycle=True
        ).execute()

        utils.clear_screen()

        if action == "auth_github": git_actions.authenticate_github_account()
        elif action == "create_new_empty_remote": git_actions.create_github_repository()
        elif action == "push_existing_project":
            git_actions.push_existing_project_to_new_repo()
        elif action == "work_local":
            if not state.current_repo_path:
                if not git_actions.set_current_repository():
                    inquirer.text(message="Press Enter to return to menu...").execute()
                    continue
            if state.current_repo_path:
                display_local_repo_menu()
                continue
            else: print("Error: Could not proceed to local repository menu.")
        elif action == "manage_remote":
            display_manage_remote_menu()
            continue
        elif action is None:
            print("👋 Exiting Git Helper Pro. Goodbye!")
            break
        
        if action is not None and action not in ["work_local", "manage_remote"]:
            inquirer.text(message="Press Enter to return to menu...").execute()