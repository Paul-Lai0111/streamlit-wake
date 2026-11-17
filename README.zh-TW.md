# streamlit-wake

[English](README.md) · **繁體中文**

讓你免費部署在 Streamlit Community Cloud 上的 app 一直保持清醒，面試官、同學或使用者點進來時，
不會看到「*Zzzz. This app has gone to sleep due to inactivity.*」。

這個工具會用 GitHub Actions 每 6 小時用一個真正的（無頭）瀏覽器打開你的每個 app。如果 app 睡著了，
它會像一般訪客一樣按下 **「Yes, get this app back up!」**，並等到 app 真的載入完成。完全免費、
不需要伺服器、只需要 GitHub 帳號，大約三分鐘就能設定好。

## 為什麼單純 ping 沒有用

Streamlit Community Cloud 的 app 約 12 小時沒有訪客就會進入睡眠。網路上常見的建議是用 UptimeRobot
這類監控服務或 `curl` 定時 ping，但這些都沒用：

- 睡著的 app 其實是一個正常可以打開的網頁，所以 ping 分不出它是醒著還是睡著。
- Streamlit 只有在有人用瀏覽器按下喚醒按鈕時才會重新啟動 app，ping 不會按任何東西。

所以這個工具的做法是「假裝成訪客」：用 [Playwright](https://playwright.dev/) 開啟無頭 Chromium
打開頁面，有喚醒按鈕就按下去，最後確認 app 本身真的有畫出來。

```
GitHub Actions（每 6 小時）
  └─ apps.txt 裡的每個網址
       用無頭 Chromium 打開
       ├─ app 已經畫出來 ................. awake  🟢 醒著
       ├─ 出現喚醒按鈕 → 按下去，
       │  等 app 載入完成 ................ woken  🔵 已喚醒
       └─ 4 分鐘後仍沒有反應 ............. failed 🔴 失敗（這次執行會失敗，GitHub 會寄信通知你）
```

## 快速開始（3 分鐘，不用寫程式）

1. 點這個頁面上方的 **Use this template → Create a new repository**。公開或私人都可以
   （請看下方的[公開還是私人？](#公開還是私人)）。
2. 在你的新 repo 裡打開 `apps.txt`，點鉛筆圖示編輯，一行放一個 app 網址：

   ```text
   https://your-app-name.streamlit.app/
   https://your-other-app.streamlit.app/
   ```

   然後 commit。
3. 打開 **Actions** 分頁。如果 GitHub 有詢問，點 **I understand my workflows, go ahead and enable them**。
4. 點 **Wake Streamlit apps → Run workflow** 立刻試跑一次。一兩分鐘後點進那次執行，摘要會列出每個
   app 的狀態。

完成！之後它就會每 6 小時自動執行。

## 或者：加到你現有的 repo

在任何 repo（例如你 app 本身的 repo）建立 `.github/workflows/wake.yml`：

```yaml
name: Wake Streamlit apps

on:
  schedule:
    - cron: "17 */6 * * *" # 每 6 小時（UTC 時間）
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

### 參數

| 參數 | 預設值 | 用途 |
|---|---|---|
| `urls` | （空白） | app 網址，一行一個（也可以用空白或逗號分隔）。 |
| `file` | `apps.txt` | repo 裡的網址清單檔，一行一個，`#` 開頭是註解。這一步之前要先有 `actions/checkout`。檔案不存在就略過。 |
| `timeout` | `240` | 每個 app 最多等幾秒載入。大型 app 冷啟動可能要好幾分鐘。 |

`urls` 和 `file` 的網址會合併。只要有任何一個 app 是 `failed`，這一步就會失敗，GitHub 會寄信通知你
（可以在 Settings → Notifications → Actions 調整）。

## 怎麼看結果

打開 **Actions → Wake Streamlit apps →** 任一次執行，摘要會顯示：

| 狀態 | 意思 |
|---|---|
| 🟢 `awake` | app 本來就醒著，不用做事。 |
| 🔵 `woken` | 原本睡著了，已經按下按鈕，app 也啟動完成。 |
| 🔴 `failed` | 在時間內沒有載入。請自己打開網址看看：app 可能壞掉、被刪除，或需要到 share.streamlit.io 重新啟動（Reboot）。 |

## 常見問題

### 公開還是私人？

都可以。差別來自 GitHub 的規則，不是這個工具：

| | 公開 repo | 私人 repo |
|---|---|---|
| Actions 使用時間 | 無限、免費 | 每月免費 2,000 分鐘。這個 workflow 每次約用 1–2 分鐘，每 6 小時一次大約一個月 250–400 分鐘。 |
| 60 天規則 | repo 60 天沒有任何活動，GitHub 會自動關掉排程。template 的最後一步每次執行都會重新啟用 workflow，所以你什麼都不用做。 | 不適用。 |
| 誰看得到你的網址 | 所有人 | 只有你 |

如果不想公開你的 app 清單，就用私人 repo。

### 為什麼是每 6 小時？

app 約 12 小時沒人造訪就會睡著。GitHub 的排程有時會延遲（整點特別嚴重），每 6 小時留了很大的
緩衝。你也可以改成 `"17 */4 * * *"` 每 4 小時一次，但再更頻繁就沒有幫助了。

### 第一次排程比預期晚執行

這是正常的。新的排程可能要等一小時左右才開始，排程執行也常常延遲幾分鐘。想馬上測試就用 **Run workflow**。

### 需要登入的 app 可以用嗎？

不行。如果 Streamlit app 只分享給特定人，無頭瀏覽器會看到登入頁面，結果會是 `failed`。公開的 app 才適用。

### 自訂網域或其他平台可以用嗎？

它找的是 Streamlit 自己的喚醒按鈕和 app 容器，所以任何 Streamlit 網址都可以，包括掛在自訂網域下的
Community Cloud app。其他睡眠機制不同的平台（Render、Hugging Face Spaces 等）不支援。

### 在自己電腦上執行

```bash
pip install -r requirements.txt
python -m playwright install chromium
python wake.py apps.txt
```

## 合理使用

Streamlit Community Cloud 是免費服務。請只用在真的會有人來看的自己的 app，例如作品集、課堂專案或
demo，並讓間隔維持在幾個小時。這個工具不是用來讓一大堆沒人用的 app 一直開著的。

## 架構

- [`wake.py`](wake.py)：讀取網址、用 Playwright 操作 Chromium、把結果表格寫進 job summary，任何
  app 失敗就以 1 結束。
- [`action.yml`](action.yml)：composite action。先數有幾個網址（沒有就不安裝瀏覽器），再安裝
  Playwright 和 Chromium、執行 `wake.py`。
- [`.github/workflows/wake.yml`](.github/workflows/wake.yml)：template 使用的排程。
- [`tests/`](tests)：網址解析的單元測試；`Test` workflow 每次 push 也會實際對一個線上 app 跑一次這個 action。

## 授權

[MIT](LICENSE) © Paul Lai
