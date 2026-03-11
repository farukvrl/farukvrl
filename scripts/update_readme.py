#!/usr/bin/env python3
"""
Auto-updates README.md with latest public GitHub repositories.
Runs via GitHub Actions on a weekly schedule.
"""

import json
import os
import re
import urllib.request
from datetime import date

GITHUB_USERNAME = "farukvrl"
README_PATH = os.path.join(os.path.dirname(__file__), "..", "README.md")


def fetch_public_repos():
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    all_repos = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
            f"?per_page=100&page={page}&sort=updated&direction=desc"
        )
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            repos = json.loads(resp.read())
        if not repos:
            break
        all_repos.extend(repos)
        page += 1

    public = [
        r for r in all_repos
        if not r["private"] and not r["fork"] and r["name"] != GITHUB_USERNAME
    ]
    public.sort(key=lambda r: r["stargazers_count"], reverse=True)
    return public


def build_table(repos):
    rows = []
    for r in repos:
        name = r["name"]
        url = r["html_url"]
        desc = (r["description"] or "—").replace("|", "\\|")
        lang = r["language"] or "—"
        stars = r["stargazers_count"]
        star_str = f"⭐ {stars}" if stars > 0 else "—"
        rows.append(f"| [{name}]({url}) | {desc} | {lang} | {star_str} |")

    if not rows:
        rows.append("| — | No public projects yet | — | — |")

    header = (
        "| Project | Description | Language | Stars |\n"
        "|---------|-------------|----------|-------|"
    )
    return header + "\n" + "\n".join(rows)


def update_readme(repos):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    table = build_table(repos)
    block = (
        "<!-- PROJECTS_START -->\n"
        "<!-- This section is auto-updated by GitHub Actions. Do not edit manually. -->\n"
        f"{table}\n"
        "<!-- PROJECTS_END -->"
    )
    content = re.sub(
        r"<!-- PROJECTS_START -->.*?<!-- PROJECTS_END -->",
        block,
        content,
        flags=re.DOTALL,
    )

    today = date.today().isoformat()
    content = re.sub(
        r"<!-- LAST_UPDATED -->.*?<!-- /LAST_UPDATED -->",
        f"<!-- LAST_UPDATED -->{today}<!-- /LAST_UPDATED -->",
        content,
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"README updated with {len(repos)} public repo(s).")


if __name__ == "__main__":
    repos = fetch_public_repos()
    update_readme(repos)
