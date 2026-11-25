"""Command-line interface: `streamlit-wake run | check | list | init | install-browser`."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .core import (DEFAULT_TIMEOUT, ICONS, Result, collect_urls, parse_urls, wake_all,
                   write_github_summary)

WORKFLOW_PATH = Path(".github/workflows/wake.yml")

WORKFLOW = """\
name: Wake Streamlit apps

on:
  schedule:
    # Streamlit puts an app to sleep after ~12 hours without visitors.
    - cron: "{minute} */{hours} * * *"
  workflow_dispatch: # adds a "Run workflow" button in the Actions tab

permissions:
  actions: write # only for the last step, which keeps this schedule enabled
  contents: read

jobs:
  wake:
    runs-on: ubuntu-latest
    timeout-minutes: 25
    steps:
      - uses: actions/checkout@v7
      - uses: Paul-Lai0111/streamlit-wake@v1
        with:
          file: {apps_file}
          timeout: "{timeout}"

      # GitHub turns off scheduled workflows in a public repo after 60 days without commits.
      # Re-enabling the workflow on every run keeps it on.
      - name: Keep the schedule enabled
        if: always()
        env:
          GH_TOKEN: ${{{{ github.token }}}}
        run: gh api -X PUT "repos/${{{{ github.repository }}}}/actions/workflows/wake.yml/enable"
"""

APPS_HEADER = "# Streamlit apps to keep awake, one URL per line. Lines starting with # are ignored.\n"


def _print_result(r: Result) -> None:
    note = f"  ({r.note})" if r.note else ""
    print(f"{ICONS[r.status]} {r.status:6s} {r.seconds:5.0f}s  {r.url}{note}", flush=True)


def _wake(urls: List[str], timeout: int) -> int:
    if not urls:
        print("No apps to visit. Add URLs to apps.txt or pass --url.")
        return 0
    print(f"Visiting {len(urls)} app(s), up to {timeout}s each...", flush=True)
    try:
        results = wake_all(urls, timeout, on_result=_print_result)
    except ImportError:
        print("error: Playwright is not installed. Install streamlit-wake with uv or pip.",
              file=sys.stderr)
        return 2
    except Exception as error:
        if "Executable doesn't exist" in str(error):
            print("error: Chromium is missing. Run `streamlit-wake install-browser` once.",
                  file=sys.stderr)
            return 2
        raise
    write_github_summary(results)
    failed = sum(r.status == "failed" for r in results)
    woken = sum(r.status == "woken" for r in results)
    print(f"Done: {len(results) - failed} up ({woken} woken), {failed} failed.")
    return 1 if failed else 0


def cmd_run(args) -> int:
    path = Path(args.file or "apps.txt")
    if args.file and not path.exists():
        print(f"error: {path} not found", file=sys.stderr)
        return 2
    return _wake(collect_urls(path, args.url), args.timeout)


def cmd_check(args) -> int:
    # Only the URLs on the command line; WAKE_URLS is for `run`.
    return _wake(parse_urls("\n".join(args.urls)), args.timeout)


def cmd_list(args) -> int:
    for url in collect_urls(Path(args.file), args.url):
        print(url)
    return 0


def cmd_init(args) -> int:
    # None means "not given on the command line", so a kept workflow can say what was ignored.
    explicit = [f"--{name}" for name in ("every", "timeout", "file")
                if getattr(args, name) is not None]
    every = 6 if args.every is None else args.every
    timeout = DEFAULT_TIMEOUT if args.timeout is None else args.timeout
    apps_file = args.file or "apps.txt"

    if not (24 % every == 0 and 1 <= every <= 12):
        print("error: --every must divide 24 and be at most 12 (e.g. 4, 6, 8, 12)", file=sys.stderr)
        return 2
    if not Path(".git").exists():
        print("warning: this folder is not the root of a git repository.", file=sys.stderr)

    changed = False
    workflow = WORKFLOW_PATH
    if workflow.exists() and not args.force:
        print(f"kept    {workflow}")
        if explicit:
            print(f"note    {', '.join(explicit)} not applied to the existing workflow "
                  "(use --force to rewrite it)")
    else:
        workflow.parent.mkdir(parents=True, exist_ok=True)
        workflow.write_text(WORKFLOW.format(
            minute=17, hours=every, apps_file=apps_file, timeout=timeout))
        print(f"wrote   {workflow}")
        changed = True

    apps = Path(apps_file)
    existing = collect_urls(apps) if apps.exists() else []
    new = [u for u in collect_urls(None, args.url) if u not in existing]
    if not apps.exists():
        apps.write_text(APPS_HEADER + "".join(u + "\n" for u in new))
        print(f"wrote   {apps} ({len(new)} app(s))")
        changed = True
    elif new:
        with apps.open("a") as f:
            f.writelines(u + "\n" for u in new)
        print(f"updated {apps} (+{len(new)} app(s))")
        changed = True
    else:
        print(f"kept    {apps}")

    if changed:
        print("\nNext: commit both files and push. Then open the Actions tab on GitHub and press "
              "'Run workflow' once to try it.")
    else:
        print("Nothing to change.")
    return 0


def cmd_install_browser(args) -> int:
    return subprocess.call([sys.executable, "-m", "playwright", "install", "chromium"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="streamlit-wake",
        description="Keep Streamlit Community Cloud apps awake by waking them in a real browser.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_timeout(p):
        p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, metavar="SECONDS",
                       help=f"how long to wait for each app (default {DEFAULT_TIMEOUT})")

    p = sub.add_parser("run", help="visit every app in a file and wake the sleeping ones")
    p.add_argument("file", nargs="?", help="URL list (default apps.txt, skipped if missing)")
    p.add_argument("--url", action="append", default=[], help="extra URL (repeatable)")
    add_timeout(p)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("check", help="wake specific apps right now")
    p.add_argument("urls", nargs="+", metavar="URL")
    add_timeout(p)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("list", help="print the URLs that `run` would visit")
    p.add_argument("file", nargs="?", default="apps.txt")
    p.add_argument("--url", action="append", default=[])
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("init", help="set up a GitHub Actions schedule in the current repo")
    p.add_argument("url", nargs="*", help="app URLs to add to the list")
    p.add_argument("--every", type=int, metavar="HOURS", help="hours between runs (default 6)")
    p.add_argument("--file", help="URL list to use (default apps.txt)")
    p.add_argument("--force", action="store_true",
                   help="rewrite the workflow if it already exists (otherwise it is kept)")
    p.add_argument("--timeout", type=int, metavar="SECONDS",
                   help=f"how long to wait for each app (default {DEFAULT_TIMEOUT})")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("install-browser", help="download the Chromium build Playwright uses")
    p.set_defaults(func=cmd_install_browser)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    args = build_parser().parse_args(argv)
    return args.func(args)
