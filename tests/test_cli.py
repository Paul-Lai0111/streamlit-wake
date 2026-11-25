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


def test_init_refuses_to_overwrite_and_merges_apps(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "a.streamlit.app"]) == 0
    assert main(["init", "b.streamlit.app"]) == 2
    assert main(["init", "a.streamlit.app", "b.streamlit.app", "--force"]) == 0
    apps = (tmp_path / "apps.txt").read_text()
    assert apps.count("https://a.streamlit.app") == 1 and "https://b.streamlit.app" in apps


def test_init_rejects_bad_interval(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "--every", "5"]) == 2
