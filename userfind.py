#!/usr/bin/env python3
"""userfind — check whether a username exists on public platforms.

Given a username, userfind requests the public profile URL on a set of sites
and reports where an account with that name appears to exist. It reads only
publicly available pages.

Responsible use: this is for OSINT research and investigations you are
authorized to perform. Do not use it to stalk, harass, or de-anonymize people.
Results are heuristic and can be wrong (anti-bot pages, rate limits, name
collisions across unrelated people).

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

__version__ = "1.0.0"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0 Safari/537.36"
)

# Each site: detection is either by HTTP status (404 == absent) or by a marker
# string that only appears on a "not found" page.
SITES: list[dict] = [
    {"name": "GitHub", "url": "https://github.com/{u}", "mode": "status"},
    {"name": "GitLab", "url": "https://gitlab.com/{u}", "mode": "status"},
    {"name": "Reddit", "url": "https://www.reddit.com/user/{u}/about.json", "mode": "status"},
    {"name": "Medium", "url": "https://medium.com/@{u}", "mode": "status"},
    {"name": "Dev.to", "url": "https://dev.to/{u}", "mode": "status"},
    {"name": "Keybase", "url": "https://keybase.io/{u}", "mode": "status"},
    {"name": "Replit", "url": "https://replit.com/@{u}", "mode": "status"},
    {"name": "Gravatar", "url": "https://en.gravatar.com/{u}", "mode": "status"},
    {"name": "About.me", "url": "https://about.me/{u}", "mode": "status"},
    {"name": "HackerNews", "url": "https://news.ycombinator.com/user?id={u}",
     "mode": "string", "absent": "No such user."},
    {"name": "Wordpress", "url": "https://{u}.wordpress.com", "mode": "status"},
    {"name": "Pastebin", "url": "https://pastebin.com/u/{u}", "mode": "status"},
]


class Colors:
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls) -> None:
        for n in ("GREEN", "YELLOW", "DIM", "BOLD", "RESET"):
            setattr(cls, n, "")


def check(site: dict, username: str, timeout: float) -> dict:
    url = site["url"].format(u=username)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    result = {"site": site["name"], "url": url, "status": "unknown"}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
            body = resp.read(20000).decode("utf-8", errors="ignore") if site["mode"] == "string" else ""
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            result["status"] = "absent"
        elif exc.code in (403, 429):
            result["status"] = "blocked"
        return result
    except Exception:  # noqa: BLE001 - network issues -> unknown
        return result

    if site["mode"] == "string":
        result["status"] = "absent" if site.get("absent", "") in body else "found"
    else:
        result["status"] = "found" if code == 200 else "absent"
    return result


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="userfind", description=__doc__.splitlines()[0])
    p.add_argument("username")
    p.add_argument("--all", action="store_true", help="show absent/blocked too")
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-color", action="store_true")
    p.add_argument("--timeout", type=float, default=10.0)
    p.add_argument("--version", action="version", version=__version__)
    args = p.parse_args(argv)

    if args.no_color or args.json or not sys.stdout.isatty():
        Colors.disable()
    c = Colors

    username = args.username.strip()
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda s: check(s, username, args.timeout), SITES))
    results.sort(key=lambda r: r["site"].lower())

    if args.json:
        print(json.dumps({"username": username, "results": results}, indent=2))
        return 0

    found = [r for r in results if r["status"] == "found"]
    print(f"{c.BOLD}userfind{c.RESET} {c.DIM}{username}{c.RESET}  "
          f"{c.GREEN}{len(found)}{c.RESET} of {len(results)} sites\n")
    for r in results:
        if r["status"] == "found":
            print(f"  {c.GREEN}+{c.RESET} {r['site']:<12} {r['url']}")
        elif args.all:
            mark = {"absent": f"{c.DIM}-", "blocked": f"{c.YELLOW}?", "unknown": f"{c.YELLOW}?"}[r["status"]]
            print(f"  {mark} {r['site']:<12} {c.DIM}{r['status']}{c.RESET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
