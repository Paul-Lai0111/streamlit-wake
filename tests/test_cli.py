from streamlit_wake import cli
from streamlit_wake.cli import main


def test_run_with_no_apps_is_not_an_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("WAKE_URLS", raising=False)
    assert main(["run"]) == 0
    assert "No apps" in capsys.readouterr().out


def test_run_with_missing_file_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["run", "nope.txt"]) == 2


def test_list_prints_urls(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("WAKE_URLS", raising=False)
    (tmp_path / "apps.txt").write_text("a.streamlit.app\n")
    assert main(["list", "--url", "b.streamlit.app"]) == 0
    assert capsys.readouterr().out.split() == ["https://a.streamlit.app", "https://b.streamlit.app"]


def test_init_writes_workflow_and_apps(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "my-app.streamlit.app", "--every", "4"]) == 0
    workflow = (tmp_path / ".github/workflows/wake.yml").read_text()
    assert 'cron: "17 */4 * * *"' in workflow
    assert "${{ github.token }}" in workflow
    assert "https://my-app.streamlit.app" in (tmp_path / "apps.txt").read_text()


def test_init_keeps_existing_workflow_and_adds_urls(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "a.streamlit.app", "--every", "4"]) == 0
    workflow = tmp_path / ".github/workflows/wake.yml"
    before = workflow.read_text()
    capsys.readouterr()

    assert main(["init", "a.streamlit.app", "b.streamlit.app"]) == 0
    out = capsys.readouterr().out
    assert "kept    .github/workflows/wake.yml" in out
    assert "not applied" not in out
    assert workflow.read_text() == before
    apps = (tmp_path / "apps.txt").read_text()
    assert apps.count("https://a.streamlit.app") == 1 and "https://b.streamlit.app" in apps


def test_init_with_nothing_new_says_so(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "a.streamlit.app"]) == 0
    assert "Next:" in capsys.readouterr().out
    assert main(["init", "a.streamlit.app"]) == 0
    out = capsys.readouterr().out
    assert "Nothing to change." in out
    assert "Next:" not in out


def test_init_says_when_options_are_not_applied(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init"]) == 0
    capsys.readouterr()
    assert main(["init", "--every", "12", "--timeout", "300"]) == 0
    out = capsys.readouterr().out
    assert "--every, --timeout not applied" in out and "--force" in out
    assert 'cron: "17 */6 * * *"' in (tmp_path / ".github/workflows/wake.yml").read_text()


def test_init_force_rewrites_workflow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["init"]) == 0
    assert main(["init", "--every", "12", "--force"]) == 0
    assert 'cron: "17 */12 * * *"' in (tmp_path / ".github/workflows/wake.yml").read_text()


def test_init_rejects_bad_interval(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "--every", "5"]) == 2


def test_check_ignores_wake_urls(monkeypatch):
    monkeypatch.setenv("WAKE_URLS", "https://from-env.streamlit.app/")
    visited = []
    monkeypatch.setattr(cli, "_wake", lambda urls, timeout: visited.extend(urls) or 0)
    assert main(["check", "a.streamlit.app"]) == 0
    assert visited == ["https://a.streamlit.app"]
