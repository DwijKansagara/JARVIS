# JARVIS web app

The web app lives in `web/`; the desktop app still starts with `main.py`. Both are kept in this repository. The web app does not import or expose desktop actions.

## Use the web app

1. Open **[JARVIS Web](https://dwij-jarvis.antideploy.com)**.
2. Click **Add API key** or **Connection settings**.
3. Enter your own [OpenRouter API key](https://openrouter.ai/settings/keys) and click **Connect JARVIS**.
4. Type a message and press Enter or the send arrow. Shift+Enter inserts a newline.
5. Use the microphone button to dictate in a supported browser. Allow microphone access, review the text, and send it. Dictation does not automatically send messages.
6. Enable **Read aloud** to hear replies. The first 3,500 characters are read for long replies. Toggle it off to stop speech.
7. Use **Stop** to cancel a pending reply, **Copy** to copy a response, and **New conversation** to clear the current chat.
8. Leave **Remember on this device** checked to keep the key for future visits on this browser. Use **Disconnect** to erase the saved key. **New conversation** clears the saved conversation history; reloading keeps it.

The app uses free conversational OpenRouter models with provider-side fallback. Availability and account limits still apply. A connection badge means a key was entered; sending a message verifies whether the provider accepts it.

## Privacy and capabilities

- When **Remember on this device** is enabled, the key and history are stored in this browser's local storage on this device. They are not sent to this repository or stored in Antideploy's environment. Turn it off on a shared computer; use **Disconnect** to erase the saved key.
- Chat requests go directly to OpenRouter and its selected model provider. Their data-handling policies apply. Browser dictation may use the browser vendor's speech service.
- Context is bounded to the latest 20 messages and approximately 60,000 characters. Older messages remain visible until you clear the conversation or reload.
- Web features include conversation, planning, learning, writing, and coding help. The web app cannot search the web, open local files, run commands, or control your desktop.
- The [desktop app](RUN_LOCALLY.md) retains local computer-control and Gemini Live voice features. There is no remote-desktop bridge or history synchronization between editions.
- Voice availability depends on the browser. Text chat works without dictation. Use HTTPS or localhost for microphone and clipboard features.

## Run locally

From the repository root, with Python installed:

```powershell
py -3.12 -m http.server 8765 --bind 127.0.0.1 --directory web
```

Open **http://127.0.0.1:8765**. No desktop Python packages or frontend build tools are required. Do not open `index.html` directly as a `file://` URL. Stop the server with Ctrl+C.

## Test

The desktop environment already includes Playwright:

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m unittest discover -s tests_web -v
```

Eleven browser tests cover setup, remembered keys, persisted history, chat context, safe rendering, cancellation, authentication failures, rate limits, retries, mobile layout, and voice controls. Provider and speech responses are mocked. GitHub Actions runs these separately from the ten desktop checks. A real browser-to-OpenRouter chat and a Gemini Live audio response were also verified during implementation. Physical microphone input and audible playback were not tested.

## Deploy on Antideploy

Deploy **the contents of `web/`** as the project's root. It is a static website: no backend, build command, database, or shared API key is needed. Do not upload the repository root, virtual environment, `config/api_keys.json`, or personal memory.

`.antideploy.json` identifies the application. The account token belongs in `~/.antideploy/config.json`, outside this repository. Use [Antideploy's terminal-login flow](https://antideploy.com/docs/api/terminal-login) when a token is absent; never commit or paste it into chat.

With an authenticated account:

```powershell
py -3.12 scripts/deploy_web.py
```

The script uploads only web assets and waits for the deployment result. GitHub pushes run checks but do not automatically publish. The desktop app runs locally and is not uploaded to hosting.
