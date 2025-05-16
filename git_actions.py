
import os
import json
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
import utils
import state
import config

def _fetch_remote_repo_list():
    print("⏳ Fetching your remote repositories...")
    stdout, stderr, code = utils.run_command(
        [config.GH_COMMAND, "repo", "list", "--json", "nameWithOwner,name,visibility,updatedAt,description", "--limit", "100"],
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
        if include_description:
            current_desc = repo.get('description') or "No description"
            name_display += f" - Desc: {current_desc[:50]}{'...' if current_desc and len(current_desc) > 50 else ''}"
        choices.append(Choice(value=repo['nameWithOwner'], name=name_display))
    
    choices.append(Choice(value=None, name="[Cancel]"))

    selected_repo_name_with_owner = inquirer.select(
        message=prompt_message, choices=choices, pointer="❯ ", qmark="❓"
    ).execute()
    
    utils.clear_screen()
    return selected_repo_name_with_owner

def edit_remote_repository_description():
    """Edits the description of a remote GitHub repository."""
    if not utils.ensure_gh_installed_and_authed(): return

    utils.clear_screen()
    print("--- Edit Remote Repository Description ---")
    
    repo_to_edit_owner_name = _select_remote_repository(
        prompt_message="Select repository to edit its description:",
        include_description=True
    )

    if not repo_to_edit_owner_name:
        print("Repository description editing cancelled.")
        return

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
        default=current_description
    ).execute()

    utils.clear_screen()

    if new_description is None:
        print("Description editing cancelled.")
        return

    print(f"⏳ Updating description for '{repo_to_edit_owner_name}'...")
    
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
    _, _, code = utils.run_command([config.GH_COMMAND, "repo", "delete", repo_to_delete])
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

def set_current_repository():
    """Prompts user for a repo path and initializes if needed."""
    while True:
        path_input = inquirer.text(
            message="Enter the path to your local Git repository:",
            default=state.current_repo_path if state.current_repo_path else "."
        ).execute()

        if not path_input:
            utils.clear_screen()
            print("Path cannot be empty. Selection cancelled.")
            return False

        path = os.path.abspath(path_input)
        utils.clear_screen()

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
                utils.clear_screen()
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

def create_github_repository(): # This is for creating a NEW EMPTY repo and optionally cloning
    if not utils.ensure_gh_installed_and_authed(): return
    utils.clear_screen(); print("--- Create New Empty GitHub Repo (and optionally clone) ---")
    repo_name = inquirer.text(message="Enter repository name for the new GitHub repo:").execute()
    if not repo_name: utils.clear_screen(); print("Repository name cannot be empty."); return
    
    description = inquirer.text(message="Description (optional):").execute()
    visibility = inquirer.select(message="Visibility:", choices=["private", "public", "internal"], default="private").execute()
    
    # This option is about cloning the NEWLY CREATED EMPTY repo to a NEW local directory
    should_clone_locally = inquirer.confirm(
        message=f"Clone this new empty repository to a local directory named '{repo_name}'?",
        default=True
    ).execute()

    # Define where the clone would go if chosen
    # `gh repo create NAME --clone` creates a directory `NAME` in the CWD.
    target_clone_path = os.path.abspath(os.path.join(".", repo_name)) # Assumes clone in CWD

    utils.clear_screen() # Clear before executing gh command

    if should_clone_locally and os.path.exists(target_clone_path):
        print(f"❌ Error: A directory or file named '{target_clone_path}' already exists.")
        print(f"   Cannot clone into an existing path when creating a new empty repository this way.")
        print(f"   Please remove or rename it, or choose not to clone locally for now.")
        return

    gh_cmd_list = [config.GH_COMMAND, "repo", "create", repo_name, f"--{visibility}"]
    if description: gh_cmd_list.extend(["--description", description])
    
    if should_clone_locally:
        gh_cmd_list.append("--clone") # gh will create the directory and clone into it
        print(f"⏳ Creating GitHub repository '{repo_name}' and cloning to '{target_clone_path}'...")
    else:
        print(f"⏳ Creating remote GitHub repository '{repo_name}' (no local clone)...")

    # Run `gh repo create` from the current working directory.
    # If --clone is used, `gh` will create a subdirectory named `repo_name` inside CWD.
    stdout, stderr, code = utils.run_command(gh_cmd_list, cwd=".", capture_output=True)
    
    # utils.clear_screen() # Let user see output before this title
    print("\n--- Repository Creation Result ---")

    if code == 0:
        print(f"✅ GitHub repository '{repo_name}' created successfully.")
        if stdout: print(f"   Output from gh (usually includes URL): {stdout}")
        
        if should_clone_locally:
            if os.path.isdir(target_clone_path) and utils.is_git_repository(target_clone_path):
                state.current_repo_path = target_clone_path
                print(f"   ✅ Successfully cloned to: {state.current_repo_path}")
                print(f"   ℹ️ Current active repository for this tool set to: {state.current_repo_path}")
                
                # Optional: Add initial README to the newly cloned empty repo
                readme_p = os.path.join(state.current_repo_path, "README.md")
                if not os.path.exists(readme_p): # Check if gh --clone already made one
                    utils.clear_screen(); print("--- Initial Commit for Cloned Repo ---")
                    if inquirer.confirm(message="Create a default README.md, commit, and push?", default=True).execute():
                        utils.clear_screen(); print("📝 Creating and pushing README.md...")
                        with open(readme_p, "w") as f: f.write(f"# {repo_name}\n\n{description or 'A new empty project.'}\n")
                        
                        # Determine default branch (gh clone usually sets it up correctly, e.g., 'main')
                        br_o, _, _ = utils.run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=state.current_repo_path, capture_output=True)
                        def_br = br_o or "main" # Default to main if detection fails

                        utils.run_command(["git", "add", "README.md"], cwd=state.current_repo_path)
                        utils.run_command(["git", "commit", "-m", "Initial commit with README"], cwd=state.current_repo_path)
                        _, err_p, code_p = utils.run_command(["git", "push", "-u", "origin", def_br], cwd=state.current_repo_path, capture_output=True)
                        if code_p == 0: print("   ✅ README created, committed, and pushed.")
                        else: print(f"   ❌ Failed to push initial README. Error: {err_p}")
            else:
                print(f"   ⚠️  Clone was requested, but the expected directory '{target_clone_path}' was not found or is not a Git repo after 'gh repo create --clone'.")
                print(f"      The remote repository was likely created. You may need to clone it manually.")
    else:
        # This is where your error occurs
        print(f"❌ Failed to create GitHub repository '{repo_name}'.")
        if stderr: print(f"   Error from gh: {stderr}") # This will print "X Unable to add remote "origin""
        if stdout: print(f"   Output from gh: {stdout}") # This will print the URL
        print(f"   This can happen if:")
        print(f"     a) A directory named '{repo_name}' already exists where the clone was attempted.")
        print(f"     b) There were permission issues creating the directory or initializing git within it.")
        print(f"     c) An unexpected issue with 'gh cli'.")
        print(f"   The remote repository on GitHub might have been created successfully despite this local error.")

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

    abs_current_dir = os.path.abspath(os.path.join(state.current_repo_path, current_directory_in_repo))

    if not os.path.isdir(abs_current_dir):
        utils.clear_screen()
        print(f"❌ Error: Directory '{abs_current_dir}' does not exist within the repository.")
        return

    utils.clear_screen()
    display_path = os.path.join(os.path.basename(state.current_repo_path), current_directory_in_repo)
    print(f"--- Files in: {display_path} ---")

    items = []
    try:
        items = sorted(os.listdir(abs_current_dir))
    except OSError as e:
        print(f"❌ Error listing directory contents: {e}")
        return

    choices = []
    if current_directory_in_repo != ".":
        choices.append(Choice(value="..", name="⬆️ [Go Up a Directory]"))

    for item_name in items:
        if item_name == ".git":
            continue
        item_path_abs = os.path.join(abs_current_dir, item_name)
        if os.path.isdir(item_path_abs):
            choices.append(Choice(value=item_name, name=f"📁 {item_name}/"))
        else:
            choices.append(Choice(value=item_name, name=f"📄 {item_name}"))
    
    choices.append(Choice(value="NEW_FILE_HERE", name="➕ [Create New File Here]"))
    choices.append(Choice(value="BACK_TO_LOCAL_MENU", name="🔙 [Back to Local Repo Menu]"))

    if not choices:
        print("No items to display or create.")
        return

    selected_item_name = inquirer.select(
        message="Select an item or action:",
        choices=choices,
        pointer="❯ ",
        qmark="👀",
        cycle=True
    ).execute()

    if selected_item_name is None:
        utils.clear_screen()
        print("Action cancelled.")
        return

    if selected_item_name == "BACK_TO_LOCAL_MENU":
        return

    elif selected_item_name == "..":
        parent_dir_in_repo = os.path.dirname(current_directory_in_repo)
        if not parent_dir_in_repo or parent_dir_in_repo == current_directory_in_repo :
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
        
        if ".." in new_filename_relative.split(os.path.sep):
            utils.clear_screen(); print("❌ Invalid filename: cannot use '..' in filename."); return

        file_to_edit_abs = os.path.join(abs_current_dir, new_filename_relative)
        
        utils.clear_screen()
        if os.path.exists(file_to_edit_abs):
            print(f"⚠️ File '{file_to_edit_abs}' already exists.")
            if not inquirer.confirm(message="Edit this existing file?", default=True).execute():
                modify_file_or_navigate(current_directory_in_repo)
                return
        else:
            try:
                open(file_to_edit_abs, 'a').close()
                print(f"✅ Created new file: {file_to_edit_abs}")
            except IOError as e:
                print(f"❌ Error creating file {file_to_edit_abs}: {e}"); return
        
        utils.select_editor_and_edit(file_to_edit_abs)
        modify_file_or_navigate(current_directory_in_repo)

    else:
        selected_item_abs_path = os.path.join(abs_current_dir, selected_item_name)
        if os.path.isdir(selected_item_abs_path):
            new_path_in_repo = os.path.join(current_directory_in_repo, selected_item_name)
            modify_file_or_navigate(new_path_in_repo)
        elif os.path.isfile(selected_item_abs_path):
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
                modify_file_or_navigate(current_directory_in_repo)
            elif file_action == "view":
                utils.clear_screen()
                utils.view_file_content_in_terminal(selected_item_abs_path)
                inquirer.text(message="Press Enter to return to file actions...").execute()
                modify_file_or_navigate(current_directory_in_repo)
            elif file_action == "back":
                modify_file_or_navigate(current_directory_in_repo)
        else:
            utils.clear_screen()
            print(f"❌ Error: '{selected_item_name}' is neither a file nor a directory, or it's inaccessible.")
            modify_file_or_navigate(current_directory_in_repo)

def modify_file():
    """Entry point for modifying files or navigating repository."""
    modify_file_or_navigate(".")
def push_existing_project_to_new_repo():
    if not utils.ensure_gh_installed_and_authed(): return
    utils.clear_screen(); print("--- Push Existing Project to New GitHub Repo ---")
    project_path_input = inquirer.text(message="Path to existing local project:", default=".").execute()
    if not project_path_input: utils.clear_screen(); print("Path empty."); return
    project_path = os.path.abspath(project_path_input); utils.clear_screen()
    if not os.path.isdir(project_path): print(f"❌ Invalid dir: '{project_path}'."); return
    print(f"Selected project: {project_path}")
    repo_name = inquirer.text(message="Desired GitHub repo name:", default=os.path.basename(project_path)).execute()
    if not repo_name: utils.clear_screen(); print("Repo name empty."); return
    description = inquirer.text(message="Description (optional):").execute()
    visibility = inquirer.select(message="Visibility:", choices=["private", "public", "internal"], default="private").execute()
    utils.clear_screen()
    is_already_git = utils.is_git_repository(project_path); initial_commit_needed = False

    if not is_already_git:
        print(f"ℹ️ Project at '{project_path}' is not a Git repository.")
        if inquirer.confirm(message="Initialize it as a Git repository now?", default=True).execute():
            utils.clear_screen(); print(f"⏳ Initializing Git in '{project_path}'...")
            _, err_i, code_i = utils.run_command(["git", "init"], cwd=project_path) # Default branch name depends on Git version
            if code_i != 0: print(f"❌ Failed to init Git: {err_i}"); return
            print("✅ Git repository initialized.")

            # ---- NEW: Set default branch to main ----
            print("Swit> Renaming default branch to 'main' (git branch -M main)...")
            _, err_b, code_b = utils.run_command(["git", "branch", "-M", "main"], cwd=project_path, capture_output=True)
            if code_b != 0:
                # This might fail if the repo is completely empty (no initial commit template from git init)
                # or if 'main' already exists (unlikely for fresh init).
                print(f"⚠️  Could not rename branch to 'main': {err_b}. Will proceed with current default.")
            else:
                print("   ✅ Default branch set to 'main'.")
            # ---- END NEW ----
            initial_commit_needed = True
        else: utils.clear_screen(); print("Operation cancelled by user."); return
    else: # Already a Git repo
        print(f"ℹ️ Project at '{project_path}' is already a Git repository.")
        remote_v_out, _, _ = utils.run_command(["git", "remote", "-v"], cwd=project_path, capture_output=True)
        origin_exists = any("origin\t" in line for line in remote_v_out.splitlines())
        if origin_exists:
            print("⚠️  An 'origin' remote already exists:"); print(remote_v_out)
            if not inquirer.confirm(message="Overwrite existing 'origin' to point to new GitHub repo?", default=False).execute():
                utils.clear_screen(); print("Cancelled. Manage remotes manually or choose different project."); return
            else:
                utils.clear_screen(); print("⏳ Removing existing 'origin' remote...")
                utils.run_command(["git", "remote", "remove", "origin"], cwd=project_path) # Ignore errors for now
                print("✅ Existing 'origin' removed (if it existed).")
        
        stat_o, _, _ = utils.run_command(["git", "status", "--porcelain"], cwd=project_path, capture_output=True)
        if stat_o:
            utils.clear_screen(); print("⚠️ Uncommitted changes/untracked files exist.")
            if inquirer.confirm(message="Add all & make initial/update commit?", default=True).execute():
                initial_commit_needed = True
            # else: user might proceed without committing, push will send existing commits
        else: 
            _, _, head_c = utils.run_command(["git", "rev-parse", "--verify", "HEAD"], cwd=project_path, capture_output=True)
            if head_c != 0: initial_commit_needed = True; print("ℹ️ No commits yet. Will create initial commit.")
    
    print(f"⏳ Creating GitHub repository '{repo_name}' and setting up remote for '{project_path}'...")
    gh_create_cmd = [config.GH_COMMAND, "repo", "create", repo_name, f"--{visibility}", "--source", project_path]
    if description: gh_create_cmd.extend(["--description", description])
    
    stdout_create, stderr_create, code_create = utils.run_command(gh_create_cmd, capture_output=True)
    utils.clear_screen(); print("--- GitHub Repository Creation & Remote Setup ---")
    remote_repo_url = None
    if stdout_create and "https://" in stdout_create:
        for line in stdout_create.splitlines():
            if line.strip().startswith("https://github.com/"): remote_repo_url = line.strip(); break
    
    if code_create != 0 and "Unable to add remote" not in stderr_create:
        print(f"❌ Failed to create GitHub repo '{repo_name}'.\nError: {stderr_create}\nOutput: {stdout_create}"); return
    elif "Unable to add remote" in stderr_create:
        print(f"ℹ️ Remote GitHub repo '{repo_name}' likely created ({remote_repo_url or 'URL N/A'}).")
        print(f"⚠️ `gh` couldn't auto-add remote 'origin' to '{project_path}'.")
        if remote_repo_url:
            print(f"   Attempting manual remote setup for 'origin' to: {remote_repo_url}")
            utils.run_command(["git", "remote", "remove", "origin"], cwd=project_path, capture_output=True) # Suppress
            _, err_add_man, code_add_man = utils.run_command(["git", "remote", "add", "origin", remote_repo_url], cwd=project_path, capture_output=True)
            if code_add_man == 0: print("✅ Manually set 'origin' remote.")
            else: print(f"❌ Failed to set 'origin' manually: {err_add_man}\n   Set manually: git remote add origin {remote_repo_url}"); return
        else: print("❌ No remote URL found to set manually. Check GitHub."); return
    elif code_create == 0:
        print(f"✅ GitHub repo '{repo_name}' created."); print(f"   URL: {remote_repo_url}" if remote_repo_url else (f"   Output: {stdout_create}" if stdout_create else ""))
    else: print(f"Unexpected issue creating repo. Code: {code_create}\nError: {stderr_create}\nOutput: {stdout_create}"); return

    if initial_commit_needed:
        utils.clear_screen(); print("--- Preparing Local Commit ---"); print("📂 Staging all files (git add .)...")
        add_out, add_err, add_code = utils.run_command(["git", "add", "."], cwd=project_path, capture_output=True)
        if add_code != 0: print(f"❌ Failed to stage files: {add_err or add_out}"); return
        _, _, staged_check_code = utils.run_command(["git", "diff", "--staged", "--quiet"], cwd=project_path, capture_output=True)
        if staged_check_code == 0: print("ℹ️ No new changes staged."); initial_commit_needed = False
        else: print("   ✅ Files staged.")

    if initial_commit_needed:
        commit_msg = inquirer.text(message="Enter commit message:", default="Initial commit" if not is_already_git else "Update project files").execute()
        utils.clear_screen()
        if not commit_msg: print("Commit message empty. Aborting."); return
        print(f"✉️ Committing with message: '{commit_msg}'...")
        commit_out, commit_err, commit_code = utils.run_command(["git", "commit", "-m", commit_msg], cwd=project_path, capture_output=True)
        msg_com = commit_err or commit_out
        if commit_code != 0:
            if "nothing to commit" in msg_com.lower(): print("ℹ️ No changes to commit.")
            else: print(f"❌ Failed to commit: {msg_com}"); return
        else: print("✅ Project files committed locally.")
    else: print("ℹ️ No new local commit made.")

    br_o, _, br_c = utils.run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=project_path, capture_output=True)
    cur_br = br_o if br_c == 0 and br_o and br_o != "HEAD" else "main" # Default to 'main' if on detached or no branch

    utils.clear_screen(); print("--- Pushing to GitHub ---")
    print(f"⏳ Pushing local branch '{cur_br}' to remote 'origin/{cur_br}'...")
    push_out, push_err, push_code = utils.run_command(["git", "push", "-u", "origin", cur_br], cwd=project_path, capture_output=True)
    msg_push = push_err or push_out
    if push_code != 0:
        print(f"❌ Failed to push to '{repo_name}'.\nDetails: {msg_push}")
        if "Everything up-to-date" in msg_push: print("   (This means no new local commits to send.)")
        else: print("   Troubleshooting: check branch, remote, or try manual push."); return
    else: print(f"✅ Pushed '{project_path}' to '{repo_name}'.\n   Output: {push_out}" if push_out else "")
    state.current_repo_path = project_path; print(f"ℹ️ Active repo set to: {project_path}")
