"""Open each Streamlit Community Cloud app in a real browser and wake it if it is asleep.

A sleeping app does not wake up from a plain HTTP request: Streamlit only restarts it when a
visitor presses "Yes, get this app back up!". This script does what that visitor would do. It
opens each page in headless Chromium, presses the button when it is shown, and waits until the
app itself has rendered.

Usage:
    python wake.py [apps.txt]            visit every app listed in the file
    python wake.py --list [apps.txt]     only print the URLs that would be visited

URLs can also be passed in the WAKE_URLS environment variable (one per line, or separated by
spaces or commas); they are added to the ones in the file. WAKE_TIMEOUT sets how many seconds to
wait for each app (default 240).

Exit status is 1 when any app could not be confirmed awake, so a scheduled run fails visibly.
"""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

WAKE_BUTTON = "Yes, get this app back up"
APP_CONTAINER = '[data-testid="stAppViewContainer"]'


def parse_urls(text: str) -> list[str]:
    """URLs from free text: one per line (or comma/space separated), '#' starts a comment."""
    urls: list[str] = []
    for line in text.splitlines():
        line = line.split("#", 1)[0]
        for token in re.split(r"[\s,]+", line):
            if not token:
                continue
            if not token.startswith(("http://", "https://")):
                token = "https://" + token
            if token not in urls:
                urls.append(token)
    return urls


def collect_urls(path: Path | None) -> list[str]:
    text = os.environ.get("WAKE_URLS", "")
    if path is not None and path.exists():
        text = path.read_text() + "\n" + text
    return parse_urls(text)


def app_rendered(page) -> bool:
    """True once the Streamlit app (top page or its iframe) has drawn its main container."""
    for frame in page.frames:
        try:
            if frame.locator(APP_CONTAINER).count() > 0:
                return True
        except Exception:  # frames can detach while the app reloads
            continue
    return False


def check(page, url: str, timeout_s: int) -> tuple[str, str]:
    page.goto(url, wait_until="domcontentloaded", timeout=90_000)
    deadline = time.monotonic() + timeout_s
    clicked = False
    while time.monotonic() < deadline:
        button = page.get_by_role("button", name=WAKE_BUTTON)
        if not clicked and button.count() > 0:
            button.first.click()
            clicked = True
        elif app_rendered(page):
            return ("woken" if clicked else "awake"), ""
        page.wait_for_timeout(3_000)
    state = "wake requested, not loaded yet" if clicked else "no response"
    return "failed", f"{state} after {timeout_s} s"


def write_summary(rows: list[tuple[str, str, str]]) -> None:
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary:
        return
    icon = {"awake": "🟢", "woken": "🔵", "failed": "🔴"}
    with open(summary, "a") as out:
        out.write("| | App | Status | Note |\n|---|---|---|---|\n")
        out.writelines(f"| {icon[s]} | {u} | {s} | {n} |\n" for u, s, n in rows)


def main(argv: list[str]) -> int:
    list_only = "--list" in argv
    args = [a for a in argv if a != "--list"]
    path = Path(args[0]) if args else Path("apps.txt")
    if args and not path.exists():
        print(f"error: {path} not found", file=sys.stderr)
        return 2
    urls = collect_urls(path)

    if list_only:
        print("\n".join(urls))
        return 0
    if not urls:
        print("No apps listed: add URLs to apps.txt (or the `urls` input). Nothing to do.")
        return 0

    from playwright.sync_api import sync_playwright  # only needed for a real run

    timeout_s = int(os.environ.get("WAKE_TIMEOUT") or 240)
    rows: list[tuple[str, str, str]] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for url in urls:
            page = browser.new_page()
            try:
                status, note = check(page, url, timeout_s)
            except Exception as error:  # report every app, even after one fails
                status, note = "failed", type(error).__name__ + ": " + str(error).splitlines()[0]
            finally:
                page.close()
            rows.append((url, status, note))
            print(f"{status:7s} {url} {note}".rstrip(), flush=True)
        browser.close()

    write_summary(rows)
    return 1 if any(s == "failed" for _, s, _ in rows) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
