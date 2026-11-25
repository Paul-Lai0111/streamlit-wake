"""Open Streamlit Community Cloud apps in a real browser and wake the ones that are asleep.

A sleeping app does not wake up from a plain HTTP request: Streamlit only restarts it when a
visitor presses "Yes, get this app back up!". This module does what that visitor would do. It
opens each page in headless Chromium, presses the button when it is shown, and waits until the
app itself has rendered.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Callable, Iterable, List, NamedTuple, Optional

WAKE_BUTTON = "Yes, get this app back up"
APP_CONTAINER = '[data-testid="stAppViewContainer"]'
DEFAULT_TIMEOUT = 240

ICONS = {"awake": "🟢", "woken": "🔵", "failed": "🔴"}


class Result(NamedTuple):
    url: str
    status: str  # "awake", "woken" or "failed"
    note: str
    seconds: float


def parse_urls(text: str) -> List[str]:
    """URLs from free text: one per line (or comma/space separated), '#' starts a comment."""
    urls: List[str] = []
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


def collect_urls(path: Optional[Path], extra: Iterable[str] = ()) -> List[str]:
    """URLs from the file (if it exists), then extra ones, then the WAKE_URLS variable."""
    parts = []
    if path is not None and path.exists():
        parts.append(path.read_text())
    parts.extend(extra)
    parts.append(os.environ.get("WAKE_URLS", ""))
    return parse_urls("\n".join(parts))


def _app_rendered(page) -> bool:
    """True once the Streamlit app (top page or its iframe) has drawn its main container."""
    for frame in page.frames:
        try:
            if frame.locator(APP_CONTAINER).count() > 0:
                return True
        except Exception:  # frames can detach while the app reloads
            continue
    return False


def _check_page(page, url: str, timeout_s: int) -> tuple:
    page.goto(url, wait_until="domcontentloaded", timeout=90_000)
    deadline = time.monotonic() + timeout_s
    clicked = False
    while time.monotonic() < deadline:
        button = page.get_by_role("button", name=WAKE_BUTTON)
        if not clicked and button.count() > 0:
            button.first.click()
            clicked = True
        elif _app_rendered(page):
            return ("woken" if clicked else "awake"), ""
        page.wait_for_timeout(3_000)
    state = "wake requested, not loaded yet" if clicked else "no response"
    return "failed", f"{state} after {timeout_s} s"


def wake_all(
    urls: List[str],
    timeout_s: int = DEFAULT_TIMEOUT,
    on_result: Optional[Callable[[Result], None]] = None,
) -> List[Result]:
    """Visit every URL in one browser and return a Result for each, in order."""
    from playwright.sync_api import sync_playwright  # only needed for a real run

    results: List[Result] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for url in urls:
            page = browser.new_page()
            start = time.monotonic()
            try:
                status, note = _check_page(page, url, timeout_s)
            except Exception as error:  # report every app, even after one fails
                status, note = "failed", type(error).__name__ + ": " + str(error).splitlines()[0]
            finally:
                page.close()
            result = Result(url, status, note, time.monotonic() - start)
            results.append(result)
            if on_result is not None:
                on_result(result)
        browser.close()
    return results


def summary_markdown(results: List[Result]) -> str:
    rows = "".join(
        f"| {ICONS[r.status]} | {r.url} | {r.status} | {r.seconds:.0f} s | {r.note} |\n"
        for r in results
    )
    return "| | App | Status | Time | Note |\n|---|---|---|---|---|\n" + rows


def write_github_summary(results: List[Result]) -> None:
    """Append the result table to the Actions job summary, when running inside Actions."""
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as out:
            out.write(summary_markdown(results))
