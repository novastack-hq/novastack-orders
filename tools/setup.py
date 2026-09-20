"""Set up a laptop for working on NovaStack Orders (Windows, macOS, Linux).

Run it through the bootstrap script, which installs uv first:

    ./scripts/setup.sh                                            (macOS / Linux)
    powershell -ExecutionPolicy Bypass -File .\\scripts\\setup.ps1   (Windows)

What it does, in order (each step is explained before it runs, and it is safe
to run the script again):

1. Check Git, and set your Git name and email if they're missing.
2. ``uv sync``: install Python 3.12 and the project's tools into ``.venv``.
3. Find your SSH key, or create one (you choose the passphrase).
4. Load the key into your SSH agent, so you type the passphrase once.
5. Help you add the public key to GitHub.
6. Test the SSH connection, falling back to port 443 if port 22 is blocked.
7. Point this clone at your fork over SSH, and fetch the course branches.
8. Install the recommended VS Code extensions.
9. Run ``tools/check_setup.py`` and summarise.

Safety: it never overwrites an existing key, never prints or copies your
private key, asks before changing anything outside this folder, and only talks
to github.com. Standard library only, so it runs before anything is installed.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.request
import webbrowser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "https://github.com/novastack-hq/novastack-orders.git"
COURSE_BRANCHES = [
    "exercise/ORD-318",
    "lab2/beginner-start",
    "lab2/medium-start",
    "lab2/advanced-start",
    "feature/ORD-329-currency",
]
SYSTEM = platform.system()  # "Windows", "Darwin" (macOS) or "Linux"
WINDOWS_OPENSSH = Path(r"C:\Windows\System32\OpenSSH")

DRY_RUN = False
ASSUME_YES = False


# ----------------------------------------------------------------- output
def heading(number: int, text: str) -> None:
    print(f"\n\033[1m[{number}/9] {text}\033[0m")


def info(text: str) -> None:
    print(f"      {text}")


def ok(text: str) -> None:
    print(f"   \033[32mOK\033[0m {text}")


def warn(text: str) -> None:
    print(f"   \033[33m!!\033[0m {text}")


def ask(question: str, default: bool = True) -> bool:
    """Yes/no question. Enter accepts the default."""
    if ASSUME_YES:
        return default
    hint = "Y/n" if default else "y/N"
    answer = input(f"   ?  {question} [{hint}] ").strip().lower()
    return default if not answer else answer.startswith("y")


def run(
    cmd: list[str],
    *,
    mutating: bool = False,
    interactive: bool = False,
    cwd: Path = REPO_ROOT,
) -> subprocess.CompletedProcess[str]:
    """Show a command, then run it. In --dry-run, commands that change things are skipped."""
    print(f"      $ {' '.join(cmd)}")
    if DRY_RUN and mutating:
        info("(dry run: skipped)")
        return subprocess.CompletedProcess(cmd, 0, "", "")
    if interactive:
        return subprocess.run(cmd, cwd=cwd, text=True)  # the user types into it
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def quiet(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a read-only command without echoing it."""
    return subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)


# ----------------------------------------------------------------- helpers
def ssh_tool(name: str) -> str:
    """Path to ssh / ssh-add / ssh-keygen. On Windows, prefer the built-in OpenSSH,
    whose agent runs as a Windows service."""
    if SYSTEM == "Windows" and (WINDOWS_OPENSSH / f"{name}.exe").exists():
        return str(WINDOWS_OPENSSH / f"{name}.exe")
    return shutil.which(name) or name


def git_config(key: str) -> str:
    return quiet(["git", "config", "--global", "--get", key]).stdout.strip()


def ssh_dir() -> Path:
    return Path.home() / ".ssh"


def append_ssh_config(block: str, marker: str) -> None:
    """Add a block to ~/.ssh/config unless an identical marker is already there."""
    config = ssh_dir() / "config"
    existing = config.read_text(encoding="utf-8") if config.exists() else ""
    if marker in existing:
        ok(f"~/.ssh/config already has: {marker}")
        return
    print("\n" + "\n".join("      | " + line for line in block.strip().splitlines()))
    if not ask("Add these lines to ~/.ssh/config?"):
        warn("Skipped. You can add them yourself later.")
        return
    if not DRY_RUN:
        config.parent.mkdir(mode=0o700, exist_ok=True)
        with config.open("a", encoding="utf-8") as f:
            f.write(
                ("\n" if existing and not existing.endswith("\n") else "")
                + "\n"
                + block.strip()
                + "\n"
            )
        if SYSTEM != "Windows":
            config.chmod(0o600)
    if not DRY_RUN:
        ok("Updated ~/.ssh/config")


def copy_to_clipboard(text: str) -> bool:
    candidates = {
        "Darwin": [["pbcopy"]],
        "Windows": [["clip"]],
        "Linux": [
            ["wl-copy"],
            ["xclip", "-selection", "clipboard"],
            ["xsel", "--clipboard", "--input"],
        ],
    }.get(SYSTEM, [])
    for cmd in candidates:
        if shutil.which(cmd[0]):
            subprocess.run(cmd, input=text, text=True)
            return True
    return False


def ssh_test(port: int) -> tuple[bool, str]:
    """Try to authenticate to GitHub over SSH. GitHub exits 1 even on success."""
    host = "git@github.com" if port == 22 else "git@ssh.github.com"
    cmd = [ssh_tool("ssh"), "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]
    if port != 22:
        cmd += ["-p", str(port)]
    result = quiet([*cmd, host])
    output = (result.stdout + result.stderr).strip()
    return "successfully authenticated" in output, output


def add_github_host_keys() -> None:
    """Trust GitHub's real SSH host keys, fetched over HTTPS from GitHub's API.

    This avoids the "authenticity of host can't be established" prompt without
    blindly accepting whatever answers on port 22.
    """
    known_hosts = ssh_dir() / "known_hosts"
    existing = known_hosts.read_text(encoding="utf-8") if known_hosts.exists() else ""
    if "github.com ssh-ed25519" in existing and "[ssh.github.com]:443" in existing:
        ok("GitHub's host keys are already trusted")
        return
    try:
        with urllib.request.urlopen(
            "https://api.github.com/meta", timeout=15
        ) as response:
            keys = json.load(response)["ssh_keys"]
    except Exception as exc:  # noqa: BLE001 - any network problem: carry on without
        warn(
            f"Couldn't fetch GitHub's host keys ({exc}); SSH may ask you to confirm them."
        )
        return
    lines = [f"github.com {k}" for k in keys] + [
        f"[ssh.github.com]:443 {k}" for k in keys
    ]
    new = [line for line in lines if line not in existing]
    if DRY_RUN:
        info(f"(dry run: would add {len(new)} GitHub host keys to ~/.ssh/known_hosts)")
        return
    known_hosts.parent.mkdir(mode=0o700, exist_ok=True)
    with known_hosts.open("a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write("\n".join(new) + "\n")
    ok("Trusted GitHub's published SSH host keys (from api.github.com/meta)")


# ----------------------------------------------------------------- steps
def step_git() -> str:
    heading(1, "Git")
    if not shutil.which("git"):
        warn(
            "Git isn't installed. Install it from https://git-scm.com/downloads, then run this again."
        )
        sys.exit(1)
    version = quiet(["git", "--version"]).stdout.strip()
    numbers = [int(n) for n in re.findall(r"\d+", version)[:2]]
    ok(version)
    if numbers < [2, 34]:
        warn(
            "Git 2.34 or newer is needed for SSH commit signing (Advanced lab). Consider upgrading."
        )

    for key, prompt in [
        ("user.name", "Your name for commits (e.g. Alex Morgan): "),
        ("user.email", "Your email for commits (the one on your GitHub account): "),
    ]:
        value = git_config(key)
        if value:
            ok(f"git {key} = {value}")
            continue
        value = "" if ASSUME_YES else input(f"   ?  {prompt}").strip()
        if value:
            run(["git", "config", "--global", key, value], mutating=True)
        else:
            warn(f"git {key} is not set; commits will fail until it is.")
    return git_config("user.email")


def step_uv_sync() -> None:
    heading(2, "Python 3.12 and the project's tools (uv sync)")
    info(
        "uv reads .python-version and uv.lock, downloads Python 3.12 if you don't have it,"
    )
    info(
        "and installs exactly the locked versions of pytest, Ruff and mypy into .venv."
    )
    result = run(["uv", "sync"], mutating=True, interactive=True)
    if result.returncode != 0:
        warn(
            "uv sync failed. Read the message above; check your internet connection and try again."
        )
        sys.exit(1)
    ok(".venv is ready")


def step_ssh_key(email: str) -> Path:
    heading(3, "Your SSH key")
    key = ssh_dir() / "id_ed25519"
    if key.exists() and key.with_suffix(".pub").exists():
        ok(f"Using your existing key {key}")
        return key
    info("You don't have an ed25519 key yet. ssh-keygen will now create one.")
    info("Choose a passphrase when asked (you won't see it as you type). The agent")
    info("remembers it, so you'll rarely need to type it again.")
    if not DRY_RUN:
        ssh_dir().mkdir(mode=0o700, exist_ok=True)
    cmd = [ssh_tool("ssh-keygen"), "-t", "ed25519", "-f", str(key)]
    if email:
        cmd += ["-C", email]
    if run(cmd, mutating=True, interactive=True).returncode != 0:
        warn("ssh-keygen didn't finish. Run this script again to retry.")
        sys.exit(1)
    if not DRY_RUN:
        ok(f"Created {key} (private: never share it) and {key}.pub (public)")
    return key


def step_agent(key: Path) -> None:
    heading(4, "Load the key into your SSH agent")
    if SYSTEM == "Darwin":
        append_ssh_config(
            f"Host github.com\n  AddKeysToAgent yes\n  UseKeychain yes\n  IdentityFile {key}\n",
            marker="UseKeychain yes",
        )
        run(
            ["ssh-add", "--apple-use-keychain", str(key)],
            mutating=True,
            interactive=True,
        )
    elif SYSTEM == "Windows":
        status = quiet(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-Service ssh-agent).StartType.ToString() + ' ' + (Get-Service ssh-agent).Status.ToString()",
            ]
        )
        state = status.stdout.strip()
        info(f"Windows ssh-agent service: {state or 'unknown'}")
        if "Running" not in state:
            info("The agent service needs administrator rights to switch on (once).")
            if ask(
                "Open an administrator PowerShell to enable it? (you'll see a Windows prompt)"
            ):
                command = "Set-Service ssh-agent -StartupType Automatic; Start-Service ssh-agent"
                run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f"Start-Process powershell -Verb RunAs -Wait -ArgumentList "
                        f"'-NoProfile -Command \"{command}\"'",
                    ],
                    mutating=True,
                )
        run([ssh_tool("ssh-add"), str(key)], mutating=True, interactive=True)
        # Git for Windows ships its own ssh, which can't see the Windows agent.
        current = git_config("core.sshCommand")
        wanted = "C:/Windows/System32/OpenSSH/ssh.exe"
        if current != wanted and ask(
            "Tell Git to use Windows' OpenSSH (so it uses this agent)?"
        ):
            run(["git", "config", "--global", "core.sshCommand", wanted], mutating=True)
    else:  # Linux
        if os.environ.get("SSH_AUTH_SOCK"):
            run(["ssh-add", str(key)], mutating=True, interactive=True)
        else:
            warn("No SSH agent is running in this terminal.")
            info(
                'Most desktops start one for you. Otherwise run: eval "$(ssh-agent -s)" && ssh-add'
            )
            info("Without an agent, SSH will ask for your passphrase on each push.")
        append_ssh_config(
            f"Host github.com\n  AddKeysToAgent yes\n  IdentityFile {key}\n",
            marker=f"IdentityFile {key}",
        )


def step_github_key(key: Path) -> None:
    heading(5, "Add your public key to GitHub")
    add_github_host_keys()
    authenticated, _ = ssh_test(22)
    if not authenticated:
        authenticated, _ = ssh_test(443)
    if authenticated:
        ok("GitHub already accepts this key")
        return
    public = (
        key.with_suffix(".pub").read_text(encoding="utf-8").strip()
        if key.with_suffix(".pub").exists()
        else ""
    )
    if public and copy_to_clipboard(public):
        ok("Your PUBLIC key is on the clipboard")
    else:
        info("Copy this PUBLIC key (one line):")
        print(f"\n{public}\n")
    info("On the GitHub page that opens: Title = this laptop's name, Key type =")
    info("Authentication Key, paste the key, then 'Add SSH key'.")
    if not DRY_RUN:
        webbrowser.open("https://github.com/settings/ssh/new")
    if not ASSUME_YES:
        input("   ?  Press Enter once you've added the key on GitHub... ")


def step_test_ssh() -> bool:
    heading(6, "Test the SSH connection to GitHub")
    authenticated, output = ssh_test(22)
    if authenticated:
        ok(output.splitlines()[0])
        return True
    info("Port 22 didn't work. Trying GitHub's SSH-over-HTTPS port (443)...")
    authenticated, output_443 = ssh_test(443)
    if authenticated:
        ok("Port 443 works (your network probably blocks port 22).")
        append_ssh_config(
            "Host github.com\n  Hostname ssh.github.com\n  Port 443\n  User git\n",
            marker="Hostname ssh.github.com",
        )
        return True
    warn("SSH to GitHub failed:")
    for line in (output or output_443).splitlines()[:4]:
        info(line)
    info("Check the key was added on GitHub (step 5), then run this script again.")
    return False


def step_remotes() -> None:
    heading(7, "Point this clone at your fork over SSH")
    origin = quiet(["git", "remote", "get-url", "origin"]).stdout.strip()
    match = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", origin)
    if not match:
        warn(f"origin is {origin or 'not set'}; expected your GitHub fork. Skipping.")
        return
    user, repo = match.groups()
    if user.lower() == "novastack-hq":
        warn("This clone points at the team's repository, not your fork.")
        info("Fork it on GitHub first, then clone your fork. Skipping remote changes.")
        return
    ssh_url = f"git@github.com:{user}/{repo}.git"
    if origin != ssh_url:
        run(["git", "remote", "set-url", "origin", ssh_url], mutating=True)
    ok(f"origin = {ssh_url}")

    remotes = quiet(["git", "remote"]).stdout.split()
    if "upstream" not in remotes:
        run(["git", "remote", "add", "upstream", UPSTREAM], mutating=True)
    ok(f"upstream = {UPSTREAM} (the team's repository, read-only for you)")
    run(["git", "fetch", "--all", "--prune"], mutating=True)

    missing = [
        b
        for b in COURSE_BRANCHES
        if quiet(
            ["git", "rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{b}"]
        ).returncode
    ]
    if not missing:
        ok("Your fork has all the course branches")
        return
    warn(f"Your fork is missing: {', '.join(missing)}")
    info("(This happens if 'Copy the main branch only' was ticked when forking.)")
    if ask("Copy them from upstream to your fork?"):
        for branch in missing:
            run(
                [
                    "git",
                    "push",
                    "origin",
                    f"refs/remotes/upstream/{branch}:refs/heads/{branch}",
                ],
                mutating=True,
                interactive=True,
            )
        run(["git", "fetch", "origin"], mutating=True)


def find_code_cli() -> str | None:
    found = shutil.which("code")
    if found:
        return found
    mac_app = Path(
        "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
    )
    return str(mac_app) if mac_app.exists() else None


def step_extensions() -> None:
    heading(8, "VS Code extensions")
    code = find_code_cli()
    if not code:
        warn("Couldn't find the 'code' command.")
        info("Open this folder in VS Code and click 'Install' when it offers the")
        info(
            'recommended extensions. (macOS: Command Palette -> "Shell Command: Install'
        )
        info("'code' command in PATH\" makes the 'code' command available.)")
        return
    text = (REPO_ROOT / ".vscode" / "extensions.json").read_text(encoding="utf-8")
    text = re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)  # JSON with comments
    wanted = json.loads(text)["recommendations"]
    installed = {e.lower() for e in quiet([code, "--list-extensions"]).stdout.split()}
    for extension in wanted:
        if extension.lower() in installed:
            ok(extension)
        else:
            run([code, "--install-extension", extension], mutating=True)


def step_check() -> int:
    heading(9, "Check everything")
    report = [] if DRY_RUN else ["--report"]  # a dry run writes nothing
    return run(
        ["uv", "run", "tools/check_setup.py", *report], interactive=True
    ).returncode


def main() -> int:
    global DRY_RUN, ASSUME_YES
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show what would change without changing it",
    )
    parser.add_argument(
        "--yes", action="store_true", help="accept every default (for testing)"
    )
    args = parser.parse_args()
    DRY_RUN, ASSUME_YES = args.dry_run, args.yes

    sys.stdout.reconfigure(
        line_buffering=True
    )  # keep output in order with subprocesses
    print("\033[1mNovaStack Orders: laptop set-up\033[0m")
    print(
        f"System: {SYSTEM} {platform.release()}, Python {platform.python_version()}, folder {REPO_ROOT}"
    )
    if DRY_RUN:
        print("DRY RUN: nothing outside read-only checks will be changed.")

    email = step_git()
    step_uv_sync()
    key = step_ssh_key(email)
    step_agent(key)
    step_github_key(key)
    ssh_works = step_test_ssh()
    if ssh_works:
        step_remotes()
    else:
        heading(7, "Point this clone at your fork over SSH")
        warn("Skipped until SSH works.")
    step_extensions()
    status = step_check()
    print()
    if status == 0:
        print("\033[32mAll done.\033[0m Open this folder in VS Code:  code .")
    else:
        print(
            "\033[33mAlmost there.\033[0m Fix the FAIL lines above and run this script again."
        )
        print("Stuck? Bring setup-report.txt to the set-up clinic.")
    return status


if __name__ == "__main__":
    sys.exit(main())
