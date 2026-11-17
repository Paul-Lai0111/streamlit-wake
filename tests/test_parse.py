import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import wake  # noqa: E402


def test_comments_blanks_and_duplicates():
    text = "# header\n\nhttps://a.streamlit.app/\nhttps://a.streamlit.app/  # again\n"
    assert wake.parse_urls(text) == ["https://a.streamlit.app/"]


def test_separators_and_missing_scheme():
    assert wake.parse_urls("a.streamlit.app, https://b.streamlit.app/ c.streamlit.app") == [
        "https://a.streamlit.app",
        "https://b.streamlit.app/",
        "https://c.streamlit.app",
    ]


def test_template_apps_file_is_empty():
    assert wake.collect_urls(Path(__file__).resolve().parents[1] / "apps.txt") == []


def test_env_urls_are_added(tmp_path, monkeypatch):
    f = tmp_path / "apps.txt"
    f.write_text("https://a.streamlit.app/\n")
    monkeypatch.setenv("WAKE_URLS", "https://b.streamlit.app/")
    assert wake.collect_urls(f) == ["https://a.streamlit.app/", "https://b.streamlit.app/"]


def test_no_apps_is_not_an_error(tmp_path, monkeypatch):
    monkeypatch.delenv("WAKE_URLS", raising=False)
    f = tmp_path / "apps.txt"
    f.write_text("# nothing yet\n")
    assert wake.main([str(f)]) == 0
