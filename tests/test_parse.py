from pathlib import Path

from streamlit_wake.core import collect_urls, parse_urls

ROOT = Path(__file__).resolve().parents[1]


def test_comments_blanks_and_duplicates():
    text = "# header\n\nhttps://a.streamlit.app/\nhttps://a.streamlit.app/  # again\n"
    assert parse_urls(text) == ["https://a.streamlit.app/"]


def test_separators_and_missing_scheme():
    assert parse_urls("a.streamlit.app, https://b.streamlit.app/ c.streamlit.app") == [
        "https://a.streamlit.app",
        "https://b.streamlit.app/",
        "https://c.streamlit.app",
    ]


def test_template_apps_file_is_empty(monkeypatch):
    monkeypatch.delenv("WAKE_URLS", raising=False)
    assert collect_urls(ROOT / "apps.txt") == []


def test_file_then_extra_then_env(tmp_path, monkeypatch):
    f = tmp_path / "apps.txt"
    f.write_text("https://a.streamlit.app/\n")
    monkeypatch.setenv("WAKE_URLS", "https://c.streamlit.app/")
    assert collect_urls(f, ["https://b.streamlit.app/"]) == [
        "https://a.streamlit.app/",
        "https://b.streamlit.app/",
        "https://c.streamlit.app/",
    ]
