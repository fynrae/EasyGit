# git_helper_pro/git_actions.py
import os
import json
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
import utils
import state
import config

# ... (_fetch_remote_repo_list, _select_remote_repository, view_remote_repositories, 
# delete_remote_repository, rename_remote_repository, and all local git actions remain the same) ...

# Helper functions for remote repo management (_fetch_remote_repo_list, _select_remote_repository)
# and existing actions (view_remote_repositories, delete_remote_repository, rename_remote_repository)
# remain the same as in the previous "full code" response.
# All local git actions (set_current_repository, authenticate_github_account, create_github_repository, 
# view_status, modify_file, stage_changes, commit_changes, push_changes, pull_changes)
# also remain the same.

# Ensure _fetch_remote_repo_list and _select_remote_repository are present as they were
def _fetch_remote_repo_list():
    print("⏳ Fetching your remote repositories...")
    stdout, stderr, code = utils.run_command(
        [config.GH_COMMAND, "repo", "list", "--json", "nameWithOwner,name,visibility,updatedAt,description", "--limit", "100"], # Added description
        capture_output=True
    )
    if code != 0:
        utils.clear_screen(); print("❌ Failed to fetch remote repository list.");
        if stderr: print(f"   Error: {stderr}"); return None
    try:
        repos = json.loads(stdout)
        if not repos: utils.clear_screen(); print("ℹ️ No remote repositories found."); return []
        return repos
    except json.JSONDecodeError:
        utils.clear_screen(); print("❌ Error parsing repository list."); return None

def _select_remote_repository(prompt_message="Select a remote repository:", include_description=False):
    repos = _fetch_remote_repo_list()
    if repos is None or not repos: return None

    utils.clear_screen()
    choices = []
    for repo in repos:
        name_display = f"{repo['nameWithOwner']} ({repo.get('visibility', 'N/A')})"
        if include_description: # Optionally show current description
            current_desc = repo.get('description') or "No description"
            name_display += f" - Desc: {current_desc[:50]}{'...' if current_desc and len(current_desc) > 50 else ''}"
        choices.append(Choice(value=repo['nameWithOwner'], name=name_display))
    
    choices.append(Choice(value=None, name="[Cancel]"))

    selected_repo_name_with_owner = inquirer.select(
        message=prompt_message, choices=choices, pointer="❯ ", qmark="❓"
    ).execute()
    
    utils.clear_screen()
    return selected_repo_name_with_owner

# --- New Function ---
def edit_remote_repository_description():
    """Edits the description of a remote GitHub repository."""
    if not utils.ensure_gh_installed_and_authed(): return

    utils.clear_screen()
    print("--- Edit Remote Repository Description ---")
    
    # Fetch with description to show current one (optional, but good UX)
    repo_to_edit_owner_name = _select_remote_repository(
        prompt_message="Select repository to edit its description:",
        include_description=True # Ask helper to include description in selection list
    )

    if not repo_to_edit_owner_name:
        print("Repository description editing cancelled.")
        return

    # Fetch the selected repo's current description again to pre-fill input
    # (or could pass it from the selection if _select_remote_repository returned more data)
    print(f"⏳ Fetching current description for {repo_to_edit_owner_name}...")
    stdout_repo, stderr_repo, code_repo = utils.run_command(
        [config.GH_COMMAND, "repo", "view", repo_to_edit_owner_name, "--json", "description"],
        capture_output=True
    )
    current_description = ""
    if code_repo == 0:
        try:
            repo_data = json.loads(stdout_repo)
            current_description = repo_data.get("description", "")
        except json.JSONDecodeError:
            print("⚠️ Could not parse current repository description.")
    else:
        print(f"⚠️ Could not fetch current repository details: {stderr_repo}")

    utils.clear_screen()
    print(f"--- Edit Description for: {repo_to_edit_owner_name} ---")
    if current_description:
        print(f"Current description: \"{current_description}\"")
    else:
        print("Current description: (empty)")

    new_description = inquirer.text(
        message="Enter the new description (leave blank to clear, Ctrl+C to cancel):",
        default=current_description # Pre-fill with current description
    ).execute()

    utils.clear_screen()
    # If the user simply presses Enter on the default, new_description will be the current_description.
    # If they clear the input, new_description will be "".
    # If they cancel with Ctrl+C, inquirerpy usually returns None or raises KeyboardInterrupt.
    # We'll assume execute() returns the text or empty string.

    if new_description is None: # Should not happen if not `amark` is used, but good check
        print("Description editing cancelled.")
        return

    print(f"⏳ Updating description for '{repo_to_edit_owner_name}'...")
    
    # Command: gh repo edit <owner/repo> --description "new description"
    # If new_description is an empty string, it effectively clears the description.
    gh_command = [config.GH_COMMAND, "repo", "edit", repo_to_edit_owner_name, "--description", new_description]
    
    stdout, stderr, code = utils.run_command(gh_command, capture_output=True)

    if code == 0:
        print(f"✅ Description for '{repo_to_edit_owner_name}' updated successfully.")
        if new_description:
            print(f"   New description: \"{new_description}\"")
        else:
            print(f"   Description cleared.")
        if stdout: print(f"   Output: {stdout}")
    else:
        print(f"❌ Failed to update description.")
        if stderr: print(f"   Error: {stderr}")
        if stdout: print(f"   Output: {stdout}")


# --- Keep existing remote management functions ---
def view_remote_repositories():
    if not utils.ensure_gh_installed_and_authed(): return
    repos = _fetch_remote_repo_list()
    utils.clear_screen()
    if repos is None: return
    if not repos: print("ℹ️ You have no remote repositories on GitHub, or none could be retrieved."); return
    print("--- Your Remote GitHub Repositories ---")
    for repo in repos:
        desc_preview = repo.get('description') or "N/A"
        desc_preview = (desc_preview[:30] + '...') if len(desc_preview) > 33 else desc_preview
        print(f"  ➡️  {repo['nameWithOwner']:<35} (Vis: {repo.get('visibility', 'N/A'):<7} | Desc: {desc_preview:<35} | Upd: {repo.get('updatedAt', 'N/A')[:10]})")
    print("-" * 100)


def delete_remote_repository():
    if not utils.ensure_gh_installed_and_authed(): return
    utils.clear_screen(); print("--- Delete Remote GitHub Repository ---")
    repo_to_delete = _select_remote_repository("Select repository to DELETE:")
    if not repo_to_delete: print("Repository deletion cancelled."); return
    utils.clear_screen()
    print(f"⚠️ WARNING: You are about to delete the repository '{repo_to_delete}'."); print("   This action is IRREVERSIBLE.")
    if not inquirer.confirm(message=f"Proceed with deleting '{repo_to_delete}'?", default=False).execute():
        utils.clear_screen(); print("Repository deletion cancelled."); return
    utils.clear_screen(); print(f"🚨 FINAL CONFIRMATION FOR DELETING '{repo_to_delete}' 🚨")
    confirmation_name = inquirer.text(message=f"To confirm, please type the full repository name ('{repo_to_delete}'):").execute()
    utils.clear_screen()
    if confirmation_name != repo_to_delete: print("Name mismatch. Deletion cancelled."); return
    print(f"⏳ Deleting '{repo_to_delete}'... '{config.GH_COMMAND}' will now ask for final confirmation.")
    _, _, code = utils.run_command([config.GH_COMMAND, "repo", "delete", repo_to_delete]) # Interactive gh prompt
    utils.clear_screen()
    if code == 0: print(f"✅ Repository '{repo_to_delete}' deleted successfully.")
    else: print(f"❌ Failed to delete '{repo_to_delete}' or cancelled at 'gh' prompt.")

def rename_remote_repository():
    if not utils.ensure_gh_installed_and_authed(): return
    utils.clear_screen(); print("--- Rename Remote GitHub Repository ---")
    repo_to_rename = _select_remote_repository("Select repository to RENAME:")
    if not repo_to_rename: print("Repository renaming cancelled."); return
    utils.clear_screen(); print(f"Selected repository to rename: {repo_to_rename}")
    new_repo_name = inquirer.text(
        message="Enter the new name for the repository (without owner/prefix):",
        validate=lambda name: len(name) > 0 and "/" not in name and " " not in name,
        invalid_message="Invalid repository name."
    ).execute()
    utils.clear_screen()
    if not new_repo_name: print("New name cannot be empty. Renaming cancelled."); return
    print(f"⏳ Renaming '{repo_to_rename}' to '{new_repo_name}'...")
    stdout, stderr, code = utils.run_command(
        [config.GH_COMMAND, "repo", "rename", new_repo_name, "-R", repo_to_rename], capture_output=True
    )
    if code == 0:
        print(f"✅ Repo '{repo_to_rename}' renamed to '{new_repo_name}'."); print(f"ℹ️  Update local clone remote URLs if needed.")
        if stdout: print(f"   Output: {stdout}")
    else:
        print(f"❌ Failed to rename repository.");
        if stderr: print(f"   Error: {stderr}");
        if stdout: print(f"   Output: {stdout}")

# ... (All local git actions like set_current_repository, view_status, etc. remain unchanged)
# (Include the previous full definitions for all local git actions here)
def set_current_repository():
    """Prompts user for a repo path and initializes if needed."""
    while True:
        path_input = inquirer.text(
            message="Enter the path to your local Git repository:",
            default=state.current_repo_path if state.current_repo_path else "."
        ).execute()

        if not path_input:
            utils.clear_screen() # Clear before printing message if input is cancelled
            print("Path cannot be empty. Selection cancelled.")
            return False

        path = os.path.abspath(path_input)
        utils.clear_screen() # Clear before processing and printing results

        if os.path.isdir(path):
            if utils.is_git_repository(path):
                state.current_repo_path = path
                print(f"✅ Current repository set to: {state.current_repo_path}")
                return True
            else:
                init_choice = inquirer.confirm(
                    message=f"'{path}' is not a Git repository. Initialize it?",
                    default=False
                ).execute()
                utils.clear_screen() # Clear after confirm
                if init_choice:
                    _, err, code = utils.run_command(["git", "init"], cwd=path)
                    if code == 0:
                        print(f"✅ Initialized empty Git repository in {path}")
                        state.current_repo_path = path
                        return True
                    else:
                        print(f"❌ Failed to initialize repository: {err}")
                else:
                    print("ℹ️ Repository not initialized. Please choose a directory that is a Git repository.")
        else:
            print(f"❌ Invalid path: '{path}'. Please enter a valid directory path.")
        if not state.current_repo_path:
            return False

def authenticate_github_account():
    print("\n--- Authenticate GitHub Account (via 'gh' CLI) ---")
    print(f"🔎 Checking if '{config.GH_COMMAND}' CLI is installed...")
    _, _, gh_version_code = utils.run_command([config.GH_COMMAND, "--version"], capture_output=True)
    if gh_version_code != 0:
        print(f"❌ GitHub CLI ('{config.GH_COMMAND}') not found or not working.")
        print(f"   Please install it from: https://cli.github.com/ before attempting to authenticate.")
        return
    print(f"✅ '{config.GH_COMMAND}' CLI is installed.")
    print(f"ℹ️ Starting GitHub CLI authentication process ('{config.GH_COMMAND} auth login')...")
    print(f"   Please follow the prompts from the GitHub CLI. This might open a web browser.")
    _, _, login_code = utils.run_command([config.GH_COMMAND, "auth", "login"])
    utils.clear_screen(); print("--- Authentication Status ---")
    if login_code != 0:
        print(f"⚠️ '{config.GH_COMMAND} auth login' process exited with code {login_code}.")
        print("   Authentication may not have completed successfully or might have been cancelled.")
    else:
        print(f"✅ '{config.GH_COMMAND} auth login' process seems to have completed.")
    print("\n🔎 Verifying current GitHub authentication status:")
    utils.ensure_gh_installed_and_authed()

def create_github_repository():
    if not utils.ensure_gh_installed_and_authed(): return
    utils.clear_screen(); print("--- Create New GitHub Repository (via 'gh' CLI) ---")
    repo_name = inquirer.text(message="Enter repository name (e.g., my-awesome-project):").execute()
    if not repo_name: utils.clear_screen(); print("Repository name cannot be empty."); return
    description = inquirer.text(message="Enter repository description (optional):").execute()
    visibility = inquirer.select(message="Select visibility:", choices=["private", "public", "internal"], default="private").execute()
    create_local_and_clone = inquirer.confirm(message="Create a local directory for this repo and clone it?", default=True).execute()
    local_path_base_for_gh_clone = "."; target_cloned_path = os.path.abspath(os.path.join(local_path_base_for_gh_clone, repo_name))
    utils.clear_screen()
    if create_local_and_clone and os.path.exists(target_cloned_path): print(f"❌ Directory '{target_cloned_path}' already exists."); return
    gh_command_list = [config.GH_COMMAND, "repo", "create", repo_name, f"--{visibility}"]
    if description: gh_command_list.extend(["--description", description])
    cwd_for_gh = local_path_base_for_gh_clone
    if create_local_and_clone: gh_command_list.append("--clone"); print(f"⏳ Creating GitHub repository '{repo_name}' and cloning to '{target_cloned_path}'...")
    else: print(f"⏳ Creating GitHub repository '{repo_name}' remotely (no local clone)...")
    stdout, stderr, code = utils.run_command(gh_command_list, cwd=cwd_for_gh, capture_output=True)
    print("--- Repository Creation Result ---")
    if code == 0:
        print(f"✅ Successfully created GitHub repository: {repo_name}");
        if stdout: print(f"   Output from gh: {stdout}")
        if create_local_and_clone:
            if os.path.isdir(target_cloned_path):
                state.current_repo_path = target_cloned_path
                print(f"   Local repository cloned to: {state.current_repo_path}"); print(f"   Current repository automatically set to: {state.current_repo_path}")
                readme_path = os.path.join(state.current_repo_path, "README.md")
                if not os.path.exists(readme_path):
                    utils.clear_screen(); print("--- Initial Commit ---")
                    if inquirer.confirm(message="Create a default README.md, commit, and push initial content?",default=True).execute():
                        utils.clear_screen(); print("📝 Creating and pushing README.md...")
                        with open(readme_path, "w") as f: f.write(f"# {repo_name}\n\n{description if description else 'A new project.'}\n")
                        branch_stdout_g, _, branch_code_g = utils.run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=state.current_repo_path, capture_output=True)
                        default_branch_g = branch_stdout_g if branch_code_g == 0 and branch_stdout_g else "main"
                        utils.run_command(["git", "add", "README.md"], cwd=state.current_repo_path)
                        utils.run_command(["git", "commit", "-m", "Initial commit with README"], cwd=state.current_repo_path)
                        _, err_push, code_push = utils.run_command(["git", "push", "-u", "origin", default_branch_g], cwd=state.current_repo_path, capture_output=True)
                        if code_push == 0: print("   ✅ Added, committed, and pushed a default README.md.")
                        else: print(f"   ❌ Failed to push initial README. Error:\n{err_push}")
            else: print(f"   ⚠️  Expected cloned directory '{target_cloned_path}' not found.")
    else:
        print(f"❌ Failed to create GitHub repository using '{config.GH_COMMAND}'.")
        if stderr: print(f"   Error Output: {stderr}");
        if stdout: print(f"   Standard Output (from gh): {stdout}")

def view_status():
    if not state.current_repo_path: print("⚠️ No repository selected."); return
    print(f"--- Git Status for {os.path.basename(state.current_repo_path)} ---")
    utils.run_command(["git", "status"], cwd=state.current_repo_path)
    print("-" * (len(f"--- Git Status for {os.path.basename(state.current_repo_path)} ---")))

def modify_file():
    if not state.current_repo_path: print("⚠️ No repository selected."); return
    print("--- Modify/Create File ---")
    files_and_dirs = os.listdir(state.current_repo_path)
    choices = [Choice(".", name="[Current Directory Root]")]
    choices.extend([Choice(f, name=f"{'[D] ' if os.path.isdir(os.path.join(state.current_repo_path, f)) else ''}{f}") for f in files_and_dirs if f != ".git"])
    choices.append(Choice(value="NEW_FILE", name="[Create New File]")); choices.append(Choice(value=None, name="[Cancel]"))
    selected_item = inquirer.select(message="Select a file/directory or create new:", choices=choices, pointer="❯ ", qmark="📝", cycle=True).execute()
    utils.clear_screen()
    if selected_item is None: print("File modification cancelled."); return
    if selected_item == "NEW_FILE":
        new_filename = inquirer.text(message="Enter new file name (e.g., script.py):").execute()
        utils.clear_screen()
        if not new_filename: print("Filename cannot be empty."); return
        file_to_edit = os.path.join(state.current_repo_path, new_filename)
        if not os.path.exists(file_to_edit):
            try: open(file_to_edit, 'a').close(); print(f"✅ Created new file: {file_to_edit}")
            except IOError as e: print(f"❌ Error creating file {file_to_edit}: {e}"); return
        utils.select_editor_and_edit(file_to_edit)
    elif selected_item == ".": print("ℹ️ Selected current directory.")
    elif os.path.isdir(os.path.join(state.current_repo_path, selected_item)): print(f"ℹ️ '{selected_item}' is a directory.")
    else: utils.select_editor_and_edit(os.path.join(state.current_repo_path, selected_item))

def stage_changes():
    if not state.current_repo_path: print("⚠️ No repository selected."); return
    print("--- Stage Changes ---"); print("🔎 Checking for changes...")
    stdout_status, _, _ = utils.run_command(["git", "status", "--porcelain"], cwd=state.current_repo_path, capture_output=True)
    if not stdout_status: print("✅ No changes to stage."); return
    changed_files = [line[3:] for line in stdout_status.splitlines()]
    choices = [Choice("all", name="[Stage ALL Changes] (git add .)")]
    if changed_files: choices.extend([Choice(f, name=f) for f in changed_files])
    choices.append(Choice(value=None, name="[Cancel]"))
    action = inquirer.select(message="Select files to stage or stage all:", choices=choices, multiselect=True, validate=lambda r: len(r) >= 1, invalid_message="Must select at least one.", qmark="➕").execute()
    utils.clear_screen()
    if action is None or not action: print("Staging cancelled."); return
    if "all" in action:
        _, err, code = utils.run_command(["git", "add", "."], cwd=state.current_repo_path)
        if code == 0: print("✅ All changes staged.")
        else: print(f"❌ Error staging all changes: {err}")
    else:
        files_to_stage = [f for f in action if f != "all"]
        if files_to_stage:
            _, err, code = utils.run_command(["git", "add"] + files_to_stage, cwd=state.current_repo_path)
            if code == 0: print(f"✅ Staged: {', '.join(files_to_stage)}")
            else: print(f"❌ Error staging files: {err}")

def commit_changes():
    if not state.current_repo_path: print("⚠️ No repository selected."); return
    print("--- Commit Changes ---")
    _, _, code_status = utils.run_command(["git", "diff", "--staged", "--quiet"], cwd=state.current_repo_path, capture_output=True)
    if code_status == 0:
        print("ℹ️ No changes staged for commit.")
        _, _, unstaged_code = utils.run_command(["git", "diff", "--quiet"], cwd=state.current_repo_path, capture_output=True)
        if unstaged_code != 0:
            utils.clear_screen(); print("--- Commit Changes ---")
            if inquirer.confirm(message="No staged changes, but unstaged changes exist. Stage all and commit?", default=False).execute(): utils.run_command(["git", "add", "."], cwd=state.current_repo_path)
            else: utils.clear_screen(); print("Commit cancelled."); return
        else: return
    _, _, code_status_after_add = utils.run_command(["git", "diff", "--staged", "--quiet"], cwd=state.current_repo_path, capture_output=True)
    if code_status_after_add == 0 and code_status == 0: return
    utils.clear_screen(); print("--- Commit Changes ---")
    commit_message = inquirer.text(message="Enter commit message:", validate=lambda t: len(t) > 0, invalid_message="Commit message cannot be empty.").execute()
    utils.clear_screen()
    if not commit_message: print("Commit aborted (empty message)."); return
    stdout_c, err_c, code_c = utils.run_command(["git", "commit", "-m", commit_message], cwd=state.current_repo_path, capture_output=True)
    if code_c == 0: print("✅ Changes committed successfully."); print(f"   Output:\n{stdout_c}" if stdout_c else "")
    else:
        if "nothing to commit" in err_c.lower() or (stdout_c and "nothing to commit" in stdout_c.lower()): print("ℹ️ Nothing to commit.")
        else: print(f"❌ Error committing changes:\n{err_c if err_c else stdout_c}")

def push_changes():
    if not state.current_repo_path: print("⚠️ No repository selected."); return
    print("--- Push Changes ---")
    branch_stdout, _, branch_code = utils.run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=state.current_repo_path, capture_output=True)
    current_branch = branch_stdout if branch_code == 0 and branch_stdout else "HEAD"
    remote_stdout, _, remote_code = utils.run_command(["git", "remote"], cwd=state.current_repo_path, capture_output=True)
    remotes = remote_stdout.split() if remote_code == 0 and remote_stdout else []
    if not remotes: print("❌ No remotes configured."); return
    current_remote = "origin"
    if len(remotes) == 1: current_remote = remotes[0]
    elif "origin" not in remotes and remotes: current_remote = remotes[0]
    if len(remotes) > 1:
         utils.clear_screen(); print("--- Push Changes ---")
         selected_remote = inquirer.select(message="Select remote to push to:", choices=remotes, default=current_remote).execute()
         utils.clear_screen();
         if not selected_remote: print("Push cancelled."); return
         current_remote = selected_remote
    push_command = ["git", "push"]
    _, _, upstream_check_code = utils.run_command(["git", "rev-parse", "--abbrev-ref", f"{current_branch}@{{u}}"], cwd=state.current_repo_path, capture_output=True)
    if upstream_check_code != 0:
        utils.clear_screen(); print("--- Push Changes ---")
        print(f"ℹ️ Upstream for branch '{current_branch}' on remote '{current_remote}' not set.")
        if inquirer.confirm(message=f"Set upstream to '{current_remote}/{current_branch}' and push?", default=True).execute(): push_command.extend(["-u", current_remote, current_branch])
        else: utils.clear_screen(); print("Push cancelled."); return
    utils.clear_screen(); print("--- Push Changes ---")
    print(f"⏳ Attempting to push branch '{current_branch}' to remote '{current_remote}'...")
    stdout, stderr, code = utils.run_command(push_command, cwd=state.current_repo_path, capture_output=True)
    if code == 0: print("✅ Changes pushed successfully."); print(f"   Output:\n{stdout}" if stdout else "")
    else: print(f"❌ Error pushing changes:"); print(f"   Error Output:\n{stderr}" if stderr else ""); print(f"   Standard Output:\n{stdout}" if stdout else "")

def pull_changes():
    if not state.current_repo_path: print("⚠️ No repository selected."); return
    print("--- Pull Changes ---"); print(f"⏳ Attempting to pull changes for remote 'origin' (default)...")
    stdout, stderr, code = utils.run_command(["git", "pull"], cwd=state.current_repo_path, capture_output=True)
    if code == 0: print("✅ Changes pulled successfully."); print(f"   Output:\n{stdout}" if stdout else "")
    else: print(f"❌ Error pulling changes:"); print(f"   Error Output:\n{stderr}" if stderr else ""); print(f"   Standard Output:\n{stdout}" if stdout else "")
def modify_file_or_navigate(current_directory_in_repo="."):
    """
    Allows navigating directories within the repo, viewing file content,
    editing files, or creating new files.
    `current_directory_in_repo` is relative to the repo root.
    """
    if not state.current_repo_path:
        utils.clear_screen()
        print("⚠️ No repository selected. Please select one first.")
        return

    # Construct absolute path for the current directory being viewed
    abs_current_dir = os.path.abspath(os.path.join(state.current_repo_path, current_directory_in_repo))

    if not os.path.isdir(abs_current_dir):
        utils.clear_screen()
        print(f"❌ Error: Directory '{abs_current_dir}' does not exist within the repository.")
        return

    utils.clear_screen()
    # Display a breadcrumb-like path
    display_path = os.path.join(os.path.basename(state.current_repo_path), current_directory_in_repo)
    print(f"--- Files in: {display_path} ---")

    items = []
    try:
        items = sorted(os.listdir(abs_current_dir))
    except OSError as e:
        print(f"❌ Error listing directory contents: {e}")
        return

    choices = []
    # Add "Go Up" option if not at the repo root
    if current_directory_in_repo != ".":
        choices.append(Choice(value="..", name="⬆️ [Go Up a Directory]"))

    for item_name in items:
        if item_name == ".git":  # Skip .git folder
            continue
        item_path_abs = os.path.join(abs_current_dir, item_name)
        if os.path.isdir(item_path_abs):
            choices.append(Choice(value=item_name, name=f"📁 {item_name}/"))
        else:
            choices.append(Choice(value=item_name, name=f"📄 {item_name}"))
    
    choices.append(Choice(value="NEW_FILE_HERE", name="➕ [Create New File Here]"))
    choices.append(Choice(value="BACK_TO_LOCAL_MENU", name="🔙 [Back to Local Repo Menu]"))

    if not choices: # Should at least have Create New and Back
        print("No items to display or create.")
        return

    selected_item_name = inquirer.select(
        message="Select an item or action:",
        choices=choices,
        pointer="❯ ",
        qmark="👀", # View/Explore emoji
        cycle=True
    ).execute()

    if selected_item_name is None: # User cancelled (e.g., Ctrl+C)
        utils.clear_screen()
        print("Action cancelled.")
        return # Or recurse to the same directory: modify_file_or_navigate(current_directory_in_repo)

    if selected_item_name == "BACK_TO_LOCAL_MENU":
        return # This will return to the local repo menu

    elif selected_item_name == "..":
        # Go up one directory
        parent_dir_in_repo = os.path.dirname(current_directory_in_repo)
        if not parent_dir_in_repo or parent_dir_in_repo == current_directory_in_repo : # Safety for root
             parent_dir_in_repo = "."
        modify_file_or_navigate(parent_dir_in_repo)

    elif selected_item_name == "NEW_FILE_HERE":
        utils.clear_screen()
        print(f"--- Create New File in: {display_path} ---")
        new_filename_relative = inquirer.text(
            message="Enter new file name (e.g., script.py):"
        ).execute()
        if not new_filename_relative:
            utils.clear_screen(); print("Filename cannot be empty."); return
        
        # Ensure the new filename doesn't try to escape the current directory with ../
        if ".." in new_filename_relative.split(os.path.sep):
            utils.clear_screen(); print("❌ Invalid filename: cannot use '..' in filename."); return

        file_to_edit_abs = os.path.join(abs_current_dir, new_filename_relative)
        
        utils.clear_screen()
        if os.path.exists(file_to_edit_abs):
            print(f"⚠️ File '{file_to_edit_abs}' already exists.")
            if not inquirer.confirm(message="Edit this existing file?", default=True).execute():
                modify_file_or_navigate(current_directory_in_repo) # Go back to listing
                return
        else:
            try:
                open(file_to_edit_abs, 'a').close() # Create empty file
                print(f"✅ Created new file: {file_to_edit_abs}")
            except IOError as e:
                print(f"❌ Error creating file {file_to_edit_abs}: {e}"); return
        
        utils.select_editor_and_edit(file_to_edit_abs)
        modify_file_or_navigate(current_directory_in_repo) # Return to the same directory after editing

    else: # An existing file or directory was selected
        selected_item_abs_path = os.path.join(abs_current_dir, selected_item_name)
        if os.path.isdir(selected_item_abs_path):
            # Navigate into the selected subdirectory
            new_path_in_repo = os.path.join(current_directory_in_repo, selected_item_name)
            modify_file_or_navigate(new_path_in_repo)
        elif os.path.isfile(selected_item_abs_path):
            # It's a file, offer to view or edit
            utils.clear_screen()
            print(f"--- Actions for file: {selected_item_name} ---")
            file_action = inquirer.select(
                message=f"What do you want to do with '{selected_item_name}'?",
                choices=[
                    Choice("edit", name="✏️ Edit File"),
                    Choice("view", name="👁️ View File Content (in terminal)"),
                    Choice("back", name="↩️ Go Back to File List"),
                ],
                pointer="❯ ",
                qmark="❓"
            ).execute()

            if file_action == "edit":
                utils.clear_screen()
                utils.select_editor_and_edit(selected_item_abs_path)
                modify_file_or_navigate(current_directory_in_repo) # Go back to file list in current dir
            elif file_action == "view":
                utils.clear_screen()
                utils.view_file_content_in_terminal(selected_item_abs_path)
                inquirer.text(message="Press Enter to return to file actions...").execute()
                # Recurse to offer actions for the same file again or go back
                # For simplicity, let's go back to the file list of the current directory
                modify_file_or_navigate(current_directory_in_repo)
            elif file_action == "back":
                modify_file_or_navigate(current_directory_in_repo)
        else:
            utils.clear_screen()
            print(f"❌ Error: '{selected_item_name}' is neither a file nor a directory, or it's inaccessible.")
            modify_file_or_navigate(current_directory_in_repo)

# This is the entry point called by the menu
def modify_file(): # Wrapper for the recursive function
    """Entry point for modifying files or navigating repository."""
    modify_file_or_navigate(".") # Start at the repository root
def push_existing_project_to_new_repo():
    """
    Initializes a local project as a Git repo (if not already),
    creates a new GitHub repo, and pushes the project content.
    """
    if not utils.ensure_gh_installed_and_authed(): return

    utils.clear_screen()
    print("--- Push Existing Local Project to New GitHub Repo ---")

    # 1. Get local project path
    project_path_input = inquirer.text(
        message="Enter the path to your existing local project folder:",
        default="." # Default to current directory
    ).execute()

    if not project_path_input:
        utils.clear_screen(); print("Project path cannot be empty."); return
    
    project_path = os.path.abspath(project_path_input)
    utils.clear_screen() # Clear after path input

    if not os.path.isdir(project_path):
        print(f"❌ Error: Provided path '{project_path}' is not a valid directory."); return

    print(f"Selected project path: {project_path}")

    # 2. GitHub Repository Details
    repo_name_default = os.path.basename(project_path) # Suggest repo name based on folder name
    repo_name = inquirer.text(
        message="Enter the desired GitHub repository name:",
        default=repo_name_default
    ).execute()
    if not repo_name:
        utils.clear_screen(); print("Repository name cannot be empty."); return

    description = inquirer.text(message="Enter repository description (optional):").execute()
    visibility = inquirer.select(
        message="Select repository visibility:",
        choices=["private", "public", "internal"],
        default="private"
    ).execute()

    utils.clear_screen() # Clear before execution starts

    # 3. Local Git Initialization (if needed)
    is_already_git_repo = utils.is_git_repository(project_path)
    initial_commit_needed = False

    if not is_already_git_repo:
        print(f"ℹ️ Project at '{project_path}' is not a Git repository.")
        if inquirer.confirm(message="Initialize it as a Git repository now?", default=True).execute():
            utils.clear_screen() # Clear after confirm
            print(f"⏳ Initializing Git repository in '{project_path}'...")
            _, err_init, code_init = utils.run_command(["git", "init"], cwd=project_path)
            if code_init != 0:
                print(f"❌ Failed to initialize Git repository: {err_init}"); return
            print("✅ Git repository initialized.")
            initial_commit_needed = True # Will need to add files and commit
        else:
            utils.clear_screen(); print("Operation cancelled. Project must be a Git repository."); return
    else:
        print(f"ℹ️ Project at '{project_path}' is already a Git repository.")
        # Check if there are uncommitted changes that should be committed first
        # `git status --porcelain` is empty if clean
        status_out, _, _ = utils.run_command(["git", "status", "--porcelain"], cwd=project_path, capture_output=True)
        if status_out: # There are uncommitted changes or untracked files
            utils.clear_screen()
            print("⚠️ Your existing Git repository has uncommitted changes or untracked files.")
            if inquirer.confirm(message="Add all current files/changes and make an initial commit (or update commit)?", default=True).execute():
                initial_commit_needed = True
            else:
                print("ℹ️ Please commit your changes manually before proceeding or choose to commit them now.")
                # Could offer to run `git status` here for the user
                # For now, we'll assume if they say no, they might want to cancel or proceed carefully
        else: # Clean existing repo
            # Check if it has any commits. `git rev-parse HEAD` fails if no commits.
            _, _, head_check_code = utils.run_command(["git", "rev-parse", "--verify", "HEAD"], cwd=project_path, capture_output=True)
            if head_check_code != 0: # No commits yet in the existing repo
                 initial_commit_needed = True # Treat as needing an initial commit of existing files
                 print("ℹ️ Existing Git repository has no commits yet. Will create an initial commit.")


    # 4. Create Remote GitHub Repository and Push
    # `gh repo create <name> --source <path> --push` will:
    #   - Create the remote repo.
    #   - If <path> is not a git repo, it initializes it, adds a remote, commits, and pushes.
    #   - If <path> IS a git repo, it adds the remote and pushes.
    # We will handle the initial commit ourselves if `initial_commit_needed` is true for more control.
    
    print(f"⏳ Creating GitHub repository '{repo_name}' and preparing to push from '{project_path}'...")

    gh_create_command = [
        config.GH_COMMAND, "repo", "create", repo_name,
        f"--{visibility}",
        "--source", project_path, # Crucial: specify the source directory
        # We will handle push separately after ensuring a commit exists if needed.
        # Using --push here can sometimes be tricky if the local repo isn't set up exactly as gh expects.
        # Instead, we'll add remote and push manually.
    ]
    if description:
        gh_create_command.extend(["--description", description])

    # Create the remote repo first without pushing.
    # This command will also set up the remote "origin" in the local repo if it's a git repo.
    stdout_create, stderr_create, code_create = utils.run_command(gh_create_command, capture_output=True)

    utils.clear_screen() # Clear before showing results of remote creation
    print("--- GitHub Repository Creation ---")

    if code_create != 0:
        print(f"❌ Failed to create GitHub repository '{repo_name}'.")
        if stderr_create: print(f"   Error from gh: {stderr_create}")
        if stdout_create: print(f"   Output from gh: {stdout_create}")
        return
    
    print(f"✅ Successfully created GitHub repository: {repo_name}")
    if stdout_create: print(f"   Output from gh: {stdout_create}") # Often contains the repo URL

    # 5. Add, Commit (if needed), and Push
    if initial_commit_needed:
        utils.clear_screen()
        print("--- Preparing Initial Commit ---")
        print("Adding all files to staging area (git add .)...")
        _, err_add, code_add = utils.run_command(["git", "add", "."], cwd=project_path)
        if code_add != 0:
            print(f"❌ Failed to stage files: {err_add}"); return
        
        commit_msg_default = "Initial commit"
        if not is_already_git_repo: # New repo
            commit_msg = inquirer.text(message="Enter initial commit message:", default=commit_msg_default).execute()
        else: # Existing repo that needed changes committed
            commit_msg = inquirer.text(message="Enter commit message for current changes:", default="Update project files").execute()
        
        utils.clear_screen()
        if not commit_msg: print("Commit message cannot be empty. Aborting."); return

        print(f"Committing files with message: '{commit_msg}'...")
        _, err_commit, code_commit = utils.run_command(["git", "commit", "-m", commit_msg], cwd=project_path, capture_output=True) # Capture for detailed error
        if code_commit != 0:
            if "nothing to commit" in err_commit.lower() or ( _ and "nothing to commit" in _.lower()):
                 print("ℹ️ No changes to commit. Proceeding to push if already committed.")
            else:
                print(f"❌ Failed to commit files: {err_commit if err_commit else 'Unknown error'}")
                return
        else:
            print("✅ Files committed locally.")

    # Ensure remote 'origin' is set up by `gh repo create --source .`
    # It usually is, but let's be safe or re-check.
    # `gh repo create` with `--source` *should* add the remote.
    # If not, we might need: git remote add origin <repo_url_from_stdout_create>

    # Determine current/default branch
    # `git symbolic-ref --short HEAD` or `git branch --show-current` (Git 2.22+)
    # `gh repo create` might set default branch name (e.g. main) if it initialized the repo.
    branch_stdout, _, branch_code = utils.run_command(["git", "branch", "--show-current"], cwd=project_path, capture_output=True)
    if branch_code != 0 or not branch_stdout: # Fallback for older git or if on detached HEAD
        branch_stdout, _, branch_code = utils.run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=project_path, capture_output=True)
    
    current_branch = branch_stdout if branch_code == 0 and branch_stdout else "main" # Default to main if detection fails

    # If `git init` was run by us, `gh repo create` (even with --source) might not set the upstream branch name.
    # For a brand new local repo initialized by us, the branch might be 'master' by default locally.
    # GitHub's default is usually 'main'. `gh repo create` might handle this.
    # Let's ensure the local branch name matches what `gh` might expect or set default to `main`.
    # If git init was run, it might be on 'master'. GitHub default is 'main'.
    # `gh repo create --source` might already align this by setting local branch to main or by creating remote with local branch name.
    # For simplicity, we push the `current_branch` detected.

    utils.clear_screen()
    print("--- Pushing to GitHub ---")
    print(f"⏳ Pushing local branch '{current_branch}' to remote 'origin/{current_branch}'...")
    # Use -u to set upstream for the first push
    stdout_push, stderr_push, code_push = utils.run_command(
        ["git", "push", "-u", "origin", current_branch],
        cwd=project_path,
        capture_output=True
    )

    if code_push != 0:
        print(f"❌ Failed to push to GitHub repository '{repo_name}'.")
        if stderr_push: print(f"   Error: {stderr_push}")
        if stdout_push: print(f"   Output: {stdout_push}")
        print(f"   Troubleshooting steps:")
        print(f"     - Ensure branch '{current_branch}' exists locally and has commits.")
        print(f"     - Check 'git remote -v' in '{project_path}' to verify 'origin' is set correctly.")
        print(f"     - Try running 'git push -u origin {current_branch}' manually from '{project_path}'.")

        return
    
    print(f"✅ Successfully pushed project from '{project_path}' to GitHub repository '{repo_name}'.")
    if stdout_push: print(f"   Output: {stdout_push}")

    # Set this newly pushed repo as the current working repo for the tool
    state.current_repo_path = project_path
    print(f"ℹ️ Current active repository for this tool set to: {project_path}")
