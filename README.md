# streamlit-wake

Free Streamlit Community Cloud apps go to sleep after about 12 hours without visitors, so the
next person who clicks your link sees "This app has gone to sleep due to inactivity" and usually
closes the tab. streamlit-wake opens your apps in a headless browser, presses the wake button when
it's there, and can set up a GitHub Actions schedule that keeps them awake on its own.

## Usage

### Installation

The tool is a Python package managed with `uv`. Add it to a project:

```bash
uv add "git+https://github.com/Paul-Lai0111/streamlit-wake.git"
```

or install it as a standalone command:

```bash
uv tool install "git+https://github.com/Paul-Lai0111/streamlit-wake.git"
```

It needs a copy of Chromium the first time (about 100 MB):

```bash
uv run streamlit-wake install-browser
```

The examples below use `uv run streamlit-wake`. After `uv tool install`, the `uv run` prefix can
be dropped.

### Wake an app right now: `check`

`check` takes one or more URLs and wakes them immediately. It is handy right before a demo, an
interview or pasting a link into a chat, so the app is already warm when the other person opens it.

```bash
uv run streamlit-wake check https://paul-mlb-deeppitch-analytics.streamlit.app/
```

```text
Visiting 1 app(s), up to 240s each...
🟢 awake      5s  https://paul-mlb-deeppitch-analytics.streamlit.app/
Done: 1 up (0 woken), 0 failed.
```

If the app had been asleep, the line would read `🔵 woken` instead, usually after 30 to 90
seconds while the app boots.

### Keep a list of apps: `list` and `run`

For more than one app, the URLs go in a text file, `apps.txt` by default. Each line holds one
URL. Lines starting with `#` are comments, and `https://` can be left out.

```text
# Streamlit apps to keep awake
https://paul-mlb-deeppitch-analytics.streamlit.app/
ocean-soundscape-ml-paullai.streamlit.app
```

`list` prints the URLs that would be visited, without opening a browser, which is a quick way to
check the file:

```bash
uv run streamlit-wake list
```

`run` visits every app in the file:

```bash
uv run streamlit-wake run                    # uses apps.txt
uv run streamlit-wake run my-apps.txt        # a different file
uv run streamlit-wake run --url https://another-app.streamlit.app/ --timeout 300
```

`--url` adds an app on top of the ones in the file (it can be repeated), and `--timeout` sets how
many seconds to wait for each app. The default is 240, since a large app can take a few minutes
to cold start.

### Run it on a schedule: `init`

Running `check` by hand only helps at that moment. What actually keeps the apps awake is a
schedule, and `init` sets one up on GitHub Actions so it runs without anyone's laptop being on.
Inside any GitHub repository you own (a portfolio repo, or the app's own repo):

```bash
cd my-portfolio
uv run streamlit-wake init https://paul-mlb-deeppitch-analytics.streamlit.app/ --every 6
```

```text
wrote   .github/workflows/wake.yml
wrote   apps.txt (1 app(s))

Next: commit both files and push. Then open the Actions tab on GitHub and press 'Run workflow' once to try it.
```

`init` writes a workflow file and adds the URLs to `apps.txt` (creating it if needed, and never
adding the same URL twice). `--every` sets the hours between runs and must divide 24 (4, 6, 8 or
12; the default is 6). Running `init` again is safe: an existing workflow is kept as it is and
only new URLs are added to `apps.txt`. To change the schedule or timeout of an existing workflow,
add `--force`. After that, the two files are committed and pushed:

```bash
git add .github/workflows/wake.yml apps.txt
git commit -m "Keep my Streamlit apps awake"
git push
```

From then on GitHub wakes the apps every 6 hours. Each run writes a table to the job summary
showing every app and its status, and a failed run makes GitHub send an email.

### Use it as a GitHub Action without installing anything

The repository is also a GitHub Action, so the CLI is optional. One step in any workflow is
enough:

```yaml
- uses: Paul-Lai0111/streamlit-wake@v1
  with:
    urls: |
      https://your-app-name.streamlit.app/
```

The action accepts `urls` (one per line), `file` (a URL list in the repository, `apps.txt` by
default; needs `actions/checkout` first) and `timeout` (seconds per app, default `240`). Another
option is to click **Use this template** on this repository, list the URLs in `apps.txt`, and
enable Actions.

### Commands at a glance

| Command | What it does |
|---|---|
| `check URL...` | Wake the given apps now. |
| `run [FILE]` | Wake every app in `FILE` (default `apps.txt`). `--url` adds more. |
| `list [FILE]` | Print the URLs `run` would visit, without opening a browser. |
| `init [URL...]` | Write `.github/workflows/wake.yml` (kept if it exists) and add the URLs to `apps.txt`. Options: `--every HOURS`, `--file`, `--force` to rewrite the workflow. |
| `install-browser` | Download the Chromium build that Playwright uses. |

`run`, `check` and `init` accept `--timeout SECONDS`. `streamlit-wake --help` and
`streamlit-wake <command> --help` show every option.

### Reading the results

| Status | Meaning |
|---|---|
| 🟢 `awake` | The app was already running. |
| 🔵 `woken` | It was asleep; the button was pressed and the app finished starting. |
| 🔴 `failed` | Nothing loaded before the timeout. The app may have crashed or need a reboot from share.streamlit.io. |

`run` and `check` exit with status 1 if any app failed. That is what turns a scheduled run red
and triggers GitHub's email.

### Notes and limits

- A plain HTTP ping can't wake an app: the sleep page returns 200, and only pressing the wake
  button restarts it.
- **Why every 6 hours:** apps sleep after about 12 hours, and GitHub often starts scheduled runs
  a few minutes late, so 6 hours leaves a wide margin. Running more often than every 4 hours
  adds nothing.
- **Public or private repository:** both work. Public repositories get unlimited Actions minutes,
  but GitHub turns off schedules after 60 days without commits; the generated workflow re-enables
  itself on every run to avoid that. A private repository uses roughly 250 to 400 of its 2,000 free
  minutes a month and keeps the app list hidden.
- Apps that require a Streamlit login show a sign-in page, so they always come back as `failed`.
- Hosts that sleep differently, such as Render or Hugging Face Spaces, are not supported.
- Streamlit Community Cloud is a free service. The tool is meant for apps people actually visit,
  like a portfolio or a class demo, not for keeping a large number of idle apps running.

More examples and screenshots are on the project page:
https://paul-lai0111.github.io/streamlit-wake/

## License

[MIT](LICENSE)
