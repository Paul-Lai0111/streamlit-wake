# streamlit-wake

I host a few side projects on Streamlit Community Cloud, like my
[MLB pitch analytics app](https://paul-mlb-deeppitch-analytics.streamlit.app/), and I got tired
of sending someone the link only for them to see "Zzzz. This app has gone to sleep due to
inactivity." Free Streamlit apps fall asleep after about 12 hours without visitors, and an uptime
ping doesn't help because the app only restarts when someone clicks the wake button in a real
browser. streamlit-wake runs on GitHub Actions every 6 hours, opens each app in headless
Chromium, clicks that button if it's there, and waits until the app has actually loaded.

## Usage

Install it with uv (or `pip install git+...`), then download the browser it drives once:

```bash
uv add "git+https://github.com/Paul-Lai0111/streamlit-wake.git"
uv run streamlit-wake install-browser
```

Wake a couple of apps right now, for example before sending a link to someone:

```bash
uv run streamlit-wake check https://paul-mlb-deeppitch-analytics.streamlit.app/
```

```text
Visiting 1 app(s), up to 240s each...
🟢 awake      5s  https://paul-mlb-deeppitch-analytics.streamlit.app/
Done: 1 up (0 woken), 0 failed.
```

Keep a list of apps in `apps.txt` (one URL per line, `#` for comments) and visit all of them:

```bash
uv run streamlit-wake list            # print the URLs it would visit
uv run streamlit-wake run             # visit everything in apps.txt
uv run streamlit-wake run other.txt --timeout 300
```

The part I actually rely on is the schedule. Inside one of your repos, `init` writes a GitHub
Actions workflow and an `apps.txt`, so GitHub wakes the apps every few hours without your laptop
being on:

```bash
cd my-portfolio
uv run streamlit-wake init https://your-app.streamlit.app/ --every 6
git add .github/workflows/wake.yml apps.txt && git commit -m "Keep my apps awake" && git push
```

Then open the **Actions** tab and press **Run workflow** once to see it work.

| Command | What it does |
|---|---|
| `check URL...` | Wake the given apps now. |
| `run [FILE]` | Wake every app in `FILE` (default `apps.txt`); `--url` adds more. |
| `list [FILE]` | Print the URLs `run` would visit, without opening a browser. |
| `init [URL...]` | Write `.github/workflows/wake.yml` and add the URLs to `apps.txt`. `--every` sets the hours between runs (default 6). |
| `install-browser` | Download the Chromium build Playwright uses. |

`run`, `check` and `init` take `--timeout SECONDS` (default 240), since a big app can take a few
minutes to cold start. `run` and `check` exit with status 1 if any app failed, so a scheduled
run shows up red and GitHub emails you.

### Using the GitHub Action directly

If you'd rather not install anything, use this repo as a template (**Use this template**, list
your URLs in `apps.txt`, enable Actions), or add the action to an existing workflow:

```yaml
- uses: Paul-Lai0111/streamlit-wake@v1
  with:
    urls: |
      https://your-app-name.streamlit.app/
    # file: apps.txt   (default; needs actions/checkout first)
    # timeout: "240"
```

### What the results mean

Every run prints one line per app, and on GitHub Actions it also writes a table to the job
summary:

- `awake`: the app was already up.
- `woken`: it was asleep, the button got clicked, and the app finished starting.
- `failed`: nothing loaded before the timeout. The run fails, so GitHub emails you. Usually the
  app crashed or needs a reboot from share.streamlit.io.

### Things worth knowing

- **Why 6 hours:** apps sleep after ~12 hours, and GitHub often starts scheduled runs late, so 6
  hours leaves plenty of margin. Running more often than every 4 hours doesn't buy anything.
- **Public vs. private repo:** both work. Public repos get unlimited Actions minutes, but GitHub
  disables schedules after 60 days with no commits; the template's last step re-enables the
  workflow on every run so you don't have to think about it. A private repo uses roughly
  250–400 of the 2,000 free minutes a month and keeps your app list hidden.
- **Apps behind a login** won't work, since the browser just sees the sign-in page.
- **Other hosts** (Render, Hugging Face Spaces, ...) sleep differently and aren't supported.
- Please only use this for apps people actually visit, like a portfolio or a class demo.
  Streamlit Cloud is free and I'd rather not be the reason it stops being free.

## License

[MIT](LICENSE)
