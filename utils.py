# git_helper_pro/utils.py
import os
import subprocess
import platform
import shutil # For getting terminal width
# from . import config # Use relative import if part of a package
import config # Assuming direct run from the directory for simplicity

def run_command(command_list, cwd=None, capture_output=False, text=True, check=False, env=None):
    """Runs a shell command."""
    effective_env = os.environ.copy()
    if env:
        effective_env.update(env)

    # Only print if not capturing output, or if it's a sensitive command
    # This avoids cluttering when output is processed internally.
    # For commands like 'gh auth login', we want to see the execution message.
    if not capture_output or command_list[0] == config.GH_COMMAND and "auth" in command_list :
        print(f"⚙️ Executing: {' '.join(command_list)}" + (f" in {cwd}" if cwd else ""))
    
    try:
        process = subprocess.run(
            command_list,
            cwd=cwd,
            capture_output=capture_output,
            text=text,
            check=check, # If True, will raise CalledProcessError on non-zero exit
            env=effective_env
        )
        if capture_output:
            return process.stdout.strip() if process.stdout else "", \
                   process.stderr.strip() if process.stderr else "", \
                   process.returncode
        return None, None, process.returncode
    except FileNotFoundError:
        print(f"❌ Error: Command '{command_list[0]}' not found. Is it installed and in PATH?")
        return None, f"Command not found: {command_list[0]}", 1
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing command: {e}")
        if capture_output:
            return e.stdout.strip() if e.stdout else "", \
                   e.stderr.strip() if e.stderr else "", \
                   e.returncode
        return None, str(e), e.returncode
    except Exception as e_gen:
        print(f"❌ An unexpected error occurred with run_command: {e_gen}")
        return None, str(e_gen), -1


def is_git_repository(path="."):
    """Checks if the given path is a Git repository."""
    return os.path.isdir(os.path.join(path, ".git"))

def select_editor_and_edit(filepath):
    """Opens the given file in the configured system editor."""
    editor_command = [config.DEFAULT_EDITOR, filepath]
    print(f"📝 Opening {filepath} with {config.DEFAULT_EDITOR}...")
    try:
        return_code = subprocess.call(editor_command)
        if return_code == 0:
            print(f"✅ Finished editing {filepath}.")
        else:
            print(f"⚠️ Editor closed with code {return_code}. File: {filepath}")

    except Exception as e:
        print(f"❌ Error opening editor: {e}")
        print(f"   Please edit '{filepath}' manually.")

def check_git_installed():
    print("🔎 Checking Git installation...")
    _, _, git_check_code = run_command(["git", "--version"], capture_output=True)
    if git_check_code != 0:
        print("❌ Git is not installed or not found in PATH. This tool requires Git.")
        print("   Please install Git and ensure it's in your system's PATH.")
        return False
    print("✅ Git is installed.")
    return True

def ensure_gh_installed_and_authed():
    """Checks if GitHub CLI is installed and auth status."""
    print("🔎 Checking GitHub CLI ('gh') installation and authentication...")
    _, _, gh_check_code = run_command([config.GH_COMMAND, "--version"], capture_output=True)
    if gh_check_code != 0:
        print(f"❌ GitHub CLI ('{config.GH_COMMAND}') not found or not working. This is required for creating GitHub repos.")
        print("   Please install and configure it from: https://cli.github.com/")
        return False

    _, stderr_auth, auth_code = run_command([config.GH_COMMAND, "auth", "status"], capture_output=True)
    if auth_code != 0:
        print(f"❌ GitHub CLI ('{config.GH_COMMAND}') is installed but you are not authenticated.")
        print(f"   Please run '{config.GH_COMMAND} auth login' to authenticate.")
        if stderr_auth:
            print(f"   {config.GH_COMMAND} auth status error: {stderr_auth}")
        return False
    print(f"✅ GitHub CLI ('{config.GH_COMMAND}') is installed and authenticated.")
    return True

def clear_screen():
    """Clears the terminal screen."""
    if not config.CLEAR_SCREEN_BETWEEN_MENUS:
        return
    if os.name == 'nt': # For Windows
        _ = os.system('cls')
    else: # For macOS and Linux
        _ = os.system('clear')

# This function is not directly used by InquirerPy message prompts anymore,
# but kept for potential future use with static text.
def format_menu_text(text_lines, title=""):
    """
    Formats menu text lines, optionally centering them based on config.CENTER_MENUS.
    Adds a title if provided.
    Returns a list of formatted lines.
    """
    output_lines = []
    terminal_width = shutil.get_terminal_size((80, 20)).columns

    if title:
        if config.CENTER_MENUS:
            output_lines.append(title.center(terminal_width))
        else:
            output_lines.append(title)
        output_lines.append("-" * len(title) if not config.CENTER_MENUS else ("-" * len(title)).center(terminal_width))
        output_lines.append("")

    for line in text_lines:
        if config.CENTER_MENUS:
            output_lines.append(line.center(terminal_width))
        else:
            output_lines.append(line)
    return output_lines

# This function is also not directly used by InquirerPy message prompts.
def print_formatted_menu(text_lines, title=""):
    """Clears screen (if configured) and prints formatted menu text."""
    clear_screen()
    formatted_lines = format_menu_text(text_lines, title)
    for line in formatted_lines:
        print(line)
def view_file_content_in_terminal(filepath, max_lines=50):
    """
    Prints the content of a file to the terminal.
    Limits output to max_lines to avoid flooding the screen for large files.
    """
    print(f"\n--- Content of {os.path.basename(filepath)} (first {max_lines} lines) ---")
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            line_count = 0
            for line in f:
                if line_count >= max_lines:
                    print(f"... (and more - output truncated at {max_lines} lines)")
                    break
                print(line, end='') # end='' to avoid double newlines
                line_count += 1
            if line_count == 0:
                print("(File is empty)")
    except FileNotFoundError:
        print(f"❌ Error: File '{filepath}' not found.")
    except Exception as e:
        print(f"❌ Error reading file '{filepath}': {e}")
    print("\n" + "-" * 40) # Separator