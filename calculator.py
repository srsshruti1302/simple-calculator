#!/usr/bin/env python3
"""
simple_calculator_and_helpers.py

A single-file Python utility that contains:
  - A simple CLI calculator (interactive and one-shot).
  - A minimal Tkinter GUI calculator (optional run).
  - Helper functions (examples) to create a GitHub repo via API and
    to upload a file to a generic stream-like endpoint (e.g., share.stream.io)
    NOTE: The GitHub and upload helpers require you to provide your own API keys/tokens
    and are templates — they will not work without valid credentials and correct endpoints.

USAGE (command-line examples):
  - Interactive CLI calculator:
      python simple_calculator_and_helpers.py --cli
  - One-shot expression:
      python simple_calculator_and_helpers.py --expr "12/3 + 4*2"
  - Start GUI calculator:
      python simple_calculator_and_helpers.py --gui
  - Create GitHub repo (template; needs GITHUB_TOKEN):
      from this file import create_github_repo
      create_github_repo(token="ghp_xxx", name="my-repo", description="desc", private=False)
  - Upload file to stream endpoint (template):
      from this file import upload_file_to_stream
      upload_file_to_stream("https://api.share.stream.io/upload", "path/to/file", api_key="your_key")
"""

import argparse
import math
import operator
import sys
import json
import subprocess
from pathlib import Path

# Optional imports for network or GUI features
try:
    import requests
except Exception:
    requests = None  # helpers will check and raise if called

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except Exception:
    tk = None  # GUI won't be available

# ---------------------------
# Calculator core (safe eval)
# ---------------------------

# Allowed names and operators for expression evaluation
_ALLOWED_NAMES = {
    k: getattr(math, k) for k in dir(math) if not k.startswith("_")
}
# Add extra safe builtins
_ALLOWED_NAMES.update(
    {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "pow": pow,
    }
)

# Supported operators map (for postfix/simple calc usage if desired)
_OPERATORS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "//": operator.floordiv,
    "%": operator.mod,
    "**": operator.pow,
}


def safe_eval(expr: str):
    """
    Evaluate a numeric expression safely using Python's eval but restricted globals.
    Supports math.* functions and a handful of builtins defined above.
    Raises ValueError for unsafe expressions or other errors.
    """
    if not isinstance(expr, str):
        raise ValueError("Expression must be a string.")
    # simple sanitation: disallow __ and import statements
    forbidden = ["__", "import", "os.", "sys.", "subprocess", "open(", "eval(", "exec("]
    lower_expr = expr.lower()
    for token in forbidden:
        if token in lower_expr:
            raise ValueError("Unsafe token detected in expression.")
    try:
        result = eval(expr, {"__builtins__": {}}, _ALLOWED_NAMES)
    except ZeroDivisionError:
        raise
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")
    return result


# ---------------------------
# CLI interface
# ---------------------------

def interactive_cli():
    print("Simple CLI Calculator — type 'quit' or 'exit' to leave.")
    print("You can use math functions like sin(0.5), sqrt(2), pow(2,3), pi, e, etc.")
    while True:
        try:
            expr = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if expr.lower() in ("quit", "exit"):
            break
        if not expr:
            continue
        try:
            out = safe_eval(expr)
            print(out)
        except Exception as e:
            print("Error:", e)


# ---------------------------
# Minimal Tkinter Calculator
# ---------------------------

class SimpleGuiCalculator(tk.Tk if tk else object):
    def __init__(self):
        if tk is None:
            raise RuntimeError("tkinter is not available on this system.")
        super().__init__()
        self.title("Simple Calculator")
        self.geometry("320x450")
        self.resizable(False, False)
        self._create_widgets()

    def _create_widgets(self):
        self.entry_var = tk.StringVar()
        entry = ttk.Entry(self, textvariable=self.entry_var, font=("Segoe UI", 18), justify="right")
        entry.pack(fill="x", padx=8, pady=8, ipady=10)

        buttons = [
            ("7", "8", "9", "/"),
            ("4", "5", "6", "*"),
            ("1", "2", "3", "-"),
            ("0", ".", "(", ")"),
            ("C", "±", "%", "+"),
            ("sin", "cos", "tan", "sqrt"),
            ("pow", "pi", "e", "="),
        ]

        for row in buttons:
            frame = ttk.Frame(self)
            frame.pack(fill="x", padx=8, pady=2)
            for label in row:
                btn = ttk.Button(frame, text=label, command=lambda l=label: self._on_button(l))
                btn.pack(side="left", expand=True, fill="x", padx=2, pady=2)

    def _on_button(self, label):
        if label == "C":
            self.entry_var.set("")
            return
        if label == "±":
            cur = self.entry_var.get()
            if cur.startswith("-"):
                self.entry_var.set(cur[1:])
            else:
                self.entry_var.set("-" + cur)
            return
        if label == "=":
            expr = self.entry_var.get()
            try:
                result = safe_eval(expr)
                self.entry_var.set(str(result))
            except Exception as e:
                messagebox.showerror("Error", str(e))
            return

        mapping = {
            "pi": "pi",
            "e": "e",
            "sqrt": "sqrt(",
            "sin": "sin(",
            "cos": "cos(",
            "tan": "tan(",
            "pow": "pow(",
        }
        to_insert = mapping.get(label, label)
        # append
        self.entry_var.set(self.entry_var.get() + to_insert)


# ---------------------------
# GitHub helper (template)
# ---------------------------

def create_github_repo(token: str, name: str, description: str = "", private: bool = False):
    """
    Create a GitHub repository under the authenticated user using the REST API.
    This is a template function: you must pass a valid GitHub personal access token.

    Example:
      create_github_repo(token="ghp_xxx", name="my-repo", description="demo", private=False)

    Returns dict (API response) on success.

    WARNING: Storing tokens in code is insecure. Use environment variables in production.
    """
    if requests is None:
        raise RuntimeError("requests library is required for GitHub operations. Install via 'pip install requests'.")
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {
        "name": name,
        "description": description,
        "private": bool(private),
        "auto_init": False,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text}")
    return resp.json()


def init_and_push_local_repo(local_dir: str, repo_url: str, commit_message: str = "Initial commit"):
    """
    Initialize a local git repo, add all files, commit, and push to remote.
    Requires git installed and configured with remote authentication (SSH or stored credentials).

    local_dir: path to local directory
    repo_url: remote URL (e.g., git@github.com:user/repo.git or https://github.com/user/repo.git)
    """
    local_path = Path(local_dir).resolve()
    if not local_path.exists():
        raise FileNotFoundError(f"Local path not found: {local_path}")
    cmds = [
        ["git", "init"],
        ["git", "add", "--all"],
        ["git", "commit", "-m", commit_message],
        ["git", "branch", "-M", "main"],
        ["git", "remote", "add", "origin", repo_url],
        ["git", "push", "-u", "origin", "main"],
    ]
    for cmd in cmds:
        subprocess.run(cmd, cwd=str(local_path), check=True)


# ---------------------------
# Generic upload helper (template for share.stream.io)
# ---------------------------

def upload_file_to_stream(stream_endpoint: str, file_path: str, api_key: str = None, extra_payload: dict = None):
    """
    Upload a file to a generic stream-like endpoint (template).
    For share.stream.io you must adapt to their exact API (this is a generic pattern).

    Parameters:
      - stream_endpoint: full URL to POST the file.
      - file_path: path to the file to upload.
      - api_key: optional API key to include in headers.
      - extra_payload: dict with additional form fields.

    Returns:
      - Response JSON (if response contains JSON), or raw text.

    WARNING: This function uses 'requests'. Provide valid endpoint & credentials.
    """
    if requests is None:
        raise RuntimeError("requests library required. Install via 'pip install requests'.")
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    files = {"file": (p.name, p.open("rb"))}
    data = extra_payload or {}
    resp = requests.post(stream_endpoint, headers=headers, files=files, data=data, timeout=30)
    # close file
    files["file"][1].close()
    try:
        return resp.json()
    except Exception:
        return resp.text


# ---------------------------
# Main CLI argument parsing
# ---------------------------

def main():
    parser = argparse.ArgumentParser(description="Simple calculator + GitHub/upload helper (single .py file).")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--cli", action="store_true", help="Run interactive CLI calculator")
    group.add_argument("--gui", action="store_true", help="Run the Tkinter GUI calculator (if available)")
    group.add_argument("--expr", type=str, help='Evaluate a single expression, e.g. --expr "12/3 + sqrt(16)"')
    args = parser.parse_args()

    if args.cli:
        interactive_cli()
        return

    if args.gui:
        if tk is None:
            print("Tkinter not available on this system. Install tkinter or run with --cli or --expr.")
            return
        app = SimpleGuiCalculator()
        app.mainloop()
        return

    if args.expr:
        try:
            result = safe_eval(args.expr)
            print(result)
        except Exception as e:
            print("Error:", e)
        return

    # If no args: show usage and a tiny demo
    parser.print_help()
    print("\nDemo expressions you can try:")
    demos = [
        "2+2",
        "sqrt(16)",
        "sin(pi/2) + cos(0)",
        "pow(2, 8)",
        "10 % 3",
        "log(100, 10)"  # math.log with base
    ]
    for d in demos:
        try:
            print(f"{d}  ->  {safe_eval(d)}")
        except Exception:
            pass


if __name__ == "__main__":
    main()
```
