"""Check that this laptop is ready for Lecture 2.

    uv run tools/check_setup.py            # print PASS / FAIL / WARN for each item
    uv run tools/check_setup.py --report   # also write setup-report.txt for the set-up clinic

Every FAIL comes with a hint. The report contains no secrets (no keys, no
tokens), just versions, remote URLs and pass/fail lines.
"""

from __future__ import annotations

import argparse
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
COURSE_BRANCHES = [
    "exercise/ORD-318",
    "lab2/beginner-start",
    "lab2/medium-start",
    "lab2/advanced-start",
    "feature/ORD-329-currency",
]
WINDOWS_SSH = Path(r"C:\Windows\System32\OpenSSH\ssh.exe")

results: list[tuple[str, str, str]] = []  # (status, check, detail)


def record(status: str, check: str, detail: str = "", hint: str = "") -> None:
    colour = {"PASS": "32", "FAIL": "31", "WARN": "33"}[status]
    print(
        f"[\033[{colour}m{status}\033[0m] {check}" + (f": {detail}" if detail else "")
    )
    if hint and status != "PASS":
        print(f"       hint: {hint}")
    results.append((status, check, detail))


def sh(cmd: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            cmd, cwd=REPO_ROOT, text=True, capture_output=True, timeout=timeout
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(cmd, 127, "", str(exc))


def check_python() -> None:
    version = platform.python_version()
    in_venv = Path(sys.prefix).resolve() == (REPO_ROOT / ".venv").resolve()
    if sys.version_info >= (3, 12):  # noqa: UP036 - may be run with an old Python
        record("PASS", "Python", f"{version} ({sys.executable})")
    else:
        record("FAIL", "Python", version, "run this with `uv run tools/check_setup.py`")
    if in_venv:
        record("PASS", "Project environment", ".venv is active")
    else:
        record(
            "WARN",
            "Project environment",
            f"running from {sys.prefix}",
            "use `uv run tools/check_setup.py` so the project's .venv is used",
        )


def check_uv() -> None:
    uv = shutil.which("uv")
    if not uv:
        record(
            "FAIL",
            "uv",
            "not found",
            "run scripts/setup.sh (or setup.ps1), then open a new terminal",
        )
        return
    record("PASS", "uv", sh([uv, "--version"]).stdout.strip())
    locked = sh([uv, "lock", "--check"])
    if locked.returncode == 0:
        record("PASS", "uv.lock", "matches pyproject.toml")
    else:
        record("FAIL", "uv.lock", "out of date", "run `uv lock`, then commit uv.lock")


def check_git() -> None:
    git = shutil.which("git")
    if not git:
        record(
            "FAIL", "Git", "not found", "install Git from https://git-scm.com/downloads"
        )
        return
    version = sh([git, "--version"]).stdout.strip()
    numbers = [int(n) for n in re.findall(r"\d+", version)[:2]]
    record(
        "PASS" if numbers >= [2, 34] else "WARN",
        "Git",
        version,
        "Git 2.34+ is needed for SSH commit signing (Advanced lab)",
    )
    for key in ("user.name", "user.email"):
        value = sh([git, "config", "--get", key]).stdout.strip()
        if value:
            record("PASS", f"git {key}", value)
        else:
            record("FAIL", f"git {key}", "not set", f'git config --global {key} "..."')


def check_remotes() -> None:
    origin = sh(["git", "remote", "get-url", "origin"]).stdout.strip()
    if not origin:
        record(
            "FAIL", "origin remote", "not set", "clone your fork of novastack-orders"
        )
        return
    if "novastack-hq/" in origin:
        record(
            "FAIL",
            "origin remote",
            origin,
            "this is the team's repo; fork it on GitHub and clone your fork instead",
        )
    elif origin.startswith("git@github.com:") or origin.startswith(
        "ssh://git@ssh.github.com"
    ):
        record("PASS", "origin remote uses SSH", origin)
    else:
        record(
            "FAIL",
            "origin remote uses SSH",
            origin,
            "git remote set-url origin git@github.com:<you>/novastack-orders.git",
        )

    missing = [
        b
        for b in COURSE_BRANCHES
        if sh(
            ["git", "rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{b}"]
        ).returncode
    ]
    if missing:
        record(
            "FAIL",
            "Course branches",
            f"missing {', '.join(missing)}",
            "run the set-up script again: it can copy them from upstream",
        )
    else:
        record("PASS", "Course branches", f"all {len(COURSE_BRANCHES)} present")


def check_ssh() -> None:
    ssh = (
        str(WINDOWS_SSH)
        if platform.system() == "Windows" and WINDOWS_SSH.exists()
        else "ssh"
    )
    base = [ssh, "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]
    for label, cmd in [
        ("port 22", [*base, "git@github.com"]),
        ("port 443", [*base, "-p", "443", "git@ssh.github.com"]),
    ]:
        result = sh(cmd, timeout=20)
        output = (result.stdout + result.stderr).strip()
        if "successfully authenticated" in output:
            user = re.search(r"Hi ([^!]+)!", output)
            record(
                "PASS", "SSH to GitHub", f"{label}, as {user.group(1) if user else '?'}"
            )
            return
    record(
        "FAIL",
        "SSH to GitHub",
        (output.splitlines() or ["no response"])[-1][:120],
        "run the set-up script again; check the key is added at https://github.com/settings/keys",
    )


def check_tests() -> None:
    result = sh(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-m", "smoke"],
        timeout=120,
    )
    # pytest prints either "17/210 tests collected" or, when very quiet, one
    # "path: count" line per file. Accept both.
    summary = re.search(r"(\d+)(?:/\d+)? tests? (?:collected|selected)", result.stdout)
    per_file = [
        int(n) for n in re.findall(r"\.py: (\d+)$", result.stdout, re.MULTILINE)
    ]
    count = int(summary.group(1)) if summary else sum(per_file)
    if result.returncode == 0 and count:
        record("PASS", "pytest finds the tests", f"{count} smoke tests collected")
    else:
        tail = (result.stdout + result.stderr).strip().splitlines()[-1:] or [
            "no output"
        ]
        record(
            "FAIL",
            "pytest finds the tests",
            tail[0][:120],
            "run `uv sync`, then select the .venv interpreter in VS Code",
        )


def check_vscode() -> None:
    code = shutil.which("code")
    mac = Path("/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code")
    if not code and mac.exists():
        code = str(mac)
    if not code:
        record(
            "WARN",
            "VS Code command line",
            "'code' not on PATH",
            "optional; macOS: Command Palette -> Shell Command: Install 'code' command in PATH",
        )
        return
    installed = {e.lower() for e in sh([code, "--list-extensions"]).stdout.split()}
    needed = [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-python.debugpy",
        "charliermarsh.ruff",
    ]
    missing = [e for e in needed if e not in installed]
    if missing:
        record(
            "WARN",
            "VS Code extensions",
            f"missing {', '.join(missing)}",
            "open the folder in VS Code and accept the recommended extensions",
        )
    else:
        record(
            "PASS", "VS Code extensions", "Python, Pylance, Debugger and Ruff installed"
        )


def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)  # keep output in order when piped
    parser = argparse.ArgumentParser(
        description="Check this laptop is ready for Lecture 2."
    )
    parser.add_argument(
        "--report", action="store_true", help="also write setup-report.txt"
    )
    args = parser.parse_args()

    print(f"NovaStack Orders set-up check ({platform.system()} {platform.release()})\n")
    check_python()
    check_uv()
    check_git()
    check_remotes()
    check_ssh()
    check_tests()
    check_vscode()

    failures = [r for r in results if r[0] == "FAIL"]
    print(
        f"\n{len(results) - len(failures)} of {len(results)} checks passed or warned; "
        f"{len(failures)} failed."
    )
    if args.report:
        lines = [f"{platform.platform()} | Python {platform.python_version()}"]
        lines += [f"[{s}] {c}: {d}" for s, c, d in results]
        (REPO_ROOT / "setup-report.txt").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        print("Wrote setup-report.txt (no secrets in it).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
