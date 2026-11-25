# streamlit-wake

I host a few side projects on Streamlit Community Cloud, like my
[MLB pitch analytics app](https://paul-mlb-deeppitch-analytics.streamlit.app/), and I got tired
of sending someone the link only for them to see "Zzzz. This app has gone to sleep due to
inactivity." Free Streamlit apps fall asleep after about 12 hours without visitors, and an uptime
ping doesn't help because the app only restarts when someone clicks the wake button in a real
browser. streamlit-wake runs on GitHub Actions every 6 hours, opens each app in headless
Chromium, clicks that button if it's there, and waits until the app has actually loaded.

## Usage

### Start from this repo

1. Click **Use this template → Create a new repository**.
2. Edit `apps.txt` in the new repo and put one app URL per line:

   ```text
   https://your-app-name.streamlit.app/
   https://your-other-app.streamlit.app/
   ```

3. Go to the **Actions** tab and enable workflows if GitHub asks.
4. Run **Wake Streamlit apps → Run workflow** once to check it works. After that it runs on its
   own every 6 hours.

### Add it to a repo you already have

Put this in `.github/workflows/wake.yml` (in your app's own repo, for example):

```yaml
name: Wake Streamlit apps

on:
  schedule:
    - cron: "17 */6 * * *" # every 6 hours, UTC
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
```

The action takes three inputs:

- `urls`: app URLs, one per line (spaces or commas also work).
- `file`: a file in the repo with one URL per line, `#` for comments. Defaults to `apps.txt`
  and is skipped if it doesn't exist. You need `actions/checkout` before the step to use it.
- `timeout`: seconds to wait for each app, default `240`. Big apps can take a few minutes to
  cold start.

### Run it on your own machine

```bash
pip install -r requirements.txt
python -m playwright install chromium
python wake.py apps.txt          # visit every app in the file
python wake.py --list apps.txt   # just print the URLs it would visit
```

### What the results mean

Each run writes a table to the job summary:

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
