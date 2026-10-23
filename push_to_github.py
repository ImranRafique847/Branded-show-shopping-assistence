#!/usr/bin/env python3
"""
push_to_github.py
=================
Reads GITHUB_TOKEN and GITHUB_REPO from .env and pushes the current
tretter-shopping-assistant project to GitHub — no browser login needed.

Usage:
    1. Open .env and paste your GitHub Personal Access Token into GITHUB_TOKEN
    2. Run:  python push_to_github.py
"""

import os
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("GITHUB_TOKEN", "").strip()
repo  = os.getenv("GITHUB_REPO", "ImranRafique847/Branded-show-shopping-assistence").strip()

if not token or token == "paste_your_github_personal_access_token_here":
    print("ERROR: Open .env and paste your real GITHUB_TOKEN first.")
    print("  Get one at: https://github.com/settings/tokens")
    print("  Required scopes: repo")
    sys.exit(1)

remote_url = f"https://{token}@github.com/{repo}.git"

def run(cmd, **kwargs):
    print("$", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    return result.returncode

# Set or update the remote to include the token.
run(["git", "remote", "remove", "origin"])   # remove if exists (ignore error)
run(["git", "remote", "add", "origin", remote_url])

# Push.
code = run(["git", "push", "-u", "origin", "main"])
if code == 0:
    print(f"\nPushed successfully to https://github.com/{repo}")
else:
    print("\nPush failed. Check your GITHUB_TOKEN has 'repo' scope and try again.")
    sys.exit(1)
