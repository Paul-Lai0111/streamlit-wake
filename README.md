# streamlit-wake

[![Test](https://github.com/Paul-Lai0111/streamlit-wake/actions/workflows/test.yml/badge.svg)](https://github.com/Paul-Lai0111/streamlit-wake/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**English** · [繁體中文](README.zh-TW.md)

Keep your free Streamlit Community Cloud apps awake, so recruiters, classmates and users never
land on *"Zzzz. This app has gone to sleep due to inactivity."*

A GitHub Actions workflow visits each of your apps every 6 hours in a real (headless) browser.
If an app is asleep, it presses **"Yes, get this app back up!"** just as a visitor would, then
waits until the app has actually loaded. Free, no server, no account other than GitHub, and set
up in about three minutes.

## Why a simple ping does not work

Streamlit Community Cloud puts an app to sleep after about 12 hours without visitors. Uptime
monitors and `curl` cron jobs are the usual suggestion, but they do not help:

- A sleeping app is a normal web page that loads fine, so a ping cannot tell asleep from awake.
- Streamlit restarts the app only when someone presses the wake button in a browser. A ping never
  presses anything.

So this tool behaves like a visitor: it opens the page with [Playwright](https://playwright.dev/)
(headless Chromium), presses the button if it is there, and checks that the app itself has
rendered.

```
GitHub Actions (every 6 h)
  └─ for each URL in apps.txt
       open the page in headless Chromium
       ├─ app already rendered ............ awake  🟢
       ├─ wake button shown → press it,
       │  wait for the app to render ...... woken  🔵
       └─ nothing after 4 minutes ......... failed 🔴  (the run fails and GitHub emails you)
```

## Quick start (3 minutes, no code)

1. Click **Use this template → Create a new repository** at the top of this page. Public or
   private both work (see [Public or private?](#public-or-private)).
2. In your new repository, open `apps.txt`, click the pencil icon, and add your app URLs, one per
   line:

   ```text
   https://your-app-name.streamlit.app/
   https://your-other-app.streamlit.app/
   ```

   Commit the change.
3. Open the **Actions** tab. If GitHub asks, click **I understand my workflows, go ahead and
   enable them**.
4. Click **Wake Streamlit apps → Run workflow** to try it right away. After a minute or two,
   open the run: the summary shows a status for every app.

That's it. From now on it runs by itself every 6 hours.

## Or: add it to a repository you already have

Create `.github/workflows/wake.yml` in any repository (for example your app's own repo):

```yaml
name: Wake Streamlit apps

on:
  schedule:
    - cron: "17 */6 * * *" # every 6 hours (UTC)
  workflow_dispatch:

jobs:
  wake:
    runs-on: ubuntu-latest
    timeout-minutes: 25
    steps:
      - uses: Paul-Lai0111/streamlit-wake@v1
        with:
          urls: |
            https://your-app-name.streamlit.app/
            https://your-other-app.streamlit.app/
```

### Inputs

| Input | Default | What it does |
|---|---|---|
| `urls` | *(empty)* | App URLs, one per line (or separated by spaces or commas). |
| `file` | `apps.txt` | A file in your repository with one URL per line; `#` starts a comment. Needs `actions/checkout` before this step. Skipped if missing. |
| `timeout` | `240` | Seconds to wait for each app to load. Cold starts of large apps can take a few minutes. |

URLs from `urls` and `file` are combined. The step fails when any app ends as `failed`, so
GitHub emails you (Settings → Notifications → Actions controls this).

## Reading the results

Open **Actions → Wake Streamlit apps →** any run. The summary shows:

| Status | Meaning |
|---|---|
| 🟢 `awake` | The app was already running. Nothing to do. |
| 🔵 `woken` | It was asleep; the button was pressed and the app has finished starting. |
| 🔴 `failed` | It did not load within the timeout. Open the URL yourself: the app may have crashed, been deleted, or need a reboot from share.streamlit.io. |

## FAQ

### Public or private?

Both work. The differences are GitHub's rules, not this tool's:

| | Public repository | Private repository |
|---|---|---|
| Actions minutes | Unlimited, free | 2,000 free minutes per month. This workflow uses about 1–2 minutes per run, so roughly 250–400 per month on a 6-hour schedule. |
| 60-day rule | GitHub turns scheduled workflows off after 60 days with no repository activity. The template's last step re-enables the workflow on every run, so you don't need to do anything. | Does not apply. |
| Who sees your URLs | Everyone | Only you |

If you only want to list the apps without showing them publicly, use a private repository.

### Why every 6 hours?

Apps sleep after about 12 hours with no visitors. GitHub sometimes starts scheduled runs late,
especially at the top of the hour, so 6 hours leaves a wide margin. You can use `"17 */4 * * *"`
for every 4 hours, but going more often than that doesn't help.

### The first run happened later than expected

Normal. A new schedule can take up to an hour to start, and scheduled runs are often delayed by
several minutes. Use **Run workflow** to test immediately.

### Does it work for apps that need a login?

No. If a Streamlit app is shared only with specific viewers, the headless browser sees the
sign-in page and the run reports `failed`. It works for public apps.

### Does it work on my own domain or on other hosts?

It looks for Streamlit's own wake button and Streamlit's app container, so it works for any
Streamlit app URL, including Community Cloud apps behind a custom domain. Other hosts that
sleep differently (Render, Hugging Face Spaces, ...) are not supported.

### Run it on your own computer

```bash
pip install -r requirements.txt
python -m playwright install chromium
python wake.py apps.txt
```

## Fair use

Streamlit Community Cloud is a free service. Please use this for your own apps that people
actually visit, such as a portfolio, a class project or a demo, and keep the interval at a few
hours. It is not meant for keeping a large number of idle apps running.

## How it is built

- [`wake.py`](wake.py): reads the URLs, drives Chromium with Playwright, writes the result table
  to the job summary, and exits with 1 if any app failed.
- [`action.yml`](action.yml): a composite action that counts the URLs first (and skips
  installing a browser when there are none), installs Playwright and Chromium, and runs `wake.py`.
- [`.github/workflows/wake.yml`](.github/workflows/wake.yml): the schedule used by the template.
- [`tests/`](tests): unit tests for URL parsing; the `Test` workflow also runs the action against
  a live app on every push.

## License

[MIT](LICENSE) © Paul Lai
