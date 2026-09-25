# Run JARVIS locally on Windows

Follow these steps in order. Windows is the tested platform. Use Python **3.12** (recommended) or **3.11**; this project's setup script rejects other versions.

JARVIS opens a desktop window and uses your computer's microphone, speakers, and desktop. You do not need website hosting or a deployment service to run it locally. AI conversations still require an internet connection and provider API access.

## 1. Prepare your computer

- Use a Windows computer with a working microphone and speakers or headphones.
- Connect to the internet for installation and AI requests.
- Open **PowerShell** from the Start menu. Run the commands below there, one block at a time.

## 2. Install Python and Git

Install the **Python install manager** from [Python's Windows downloads page](https://www.python.org/downloads/windows/). Reopen PowerShell, then run:

```powershell
py install 3.12
py -3.12 --version
```

The second command must print `Python 3.12.x`. If you already have a working Python 3.12 installation, you can skip installing it again. If an older Python launcher intercepts `py install`, use `pymanager install 3.12` after installing the manager. See [Python's Windows instructions](https://docs.python.org/3/using/windows.html).

Install [Git for Windows](https://git-scm.com/install/windows), reopen PowerShell, and verify:

```powershell
git --version
```

## 3. Download this repository

These commands put the project in `JARVIS` inside your Windows user folder:

```powershell
Set-Location $env:USERPROFILE
git clone https://github.com/DwijKansagara/JARVIS.git
Set-Location JARVIS
```

If you already cloned it there, use `Set-Location "$env:USERPROFILE\JARVIS"` instead of cloning again. If you chose another location, use that folder's full path. You should see `main.py`, `setup.py`, and `requirements.txt` when you run `Get-ChildItem`.

Alternatively, download **Code → Download ZIP** from the repository, extract it, and open PowerShell in the extracted folder containing `main.py`. ZIP downloads do not support the Git update command in step 12.

## 4. Create a fresh virtual environment

From the project folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

The Python version should again be 3.12.x. Do not reuse a `.venv` copied from another computer. These instructions call the environment's Python directly, so activation and PowerShell execution-policy changes are unnecessary.

## 5. Install packages and browser engines

```powershell
.\.venv\Scripts\python.exe setup.py
```

Wait for **Setup complete!** The script installs `requirements.txt` and downloads Playwright browser engines. Keep the terminal open until it finishes.

For the exact dependency versions previously tested on Windows/Python 3.12, use these commands **instead of** `setup.py`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-windows.lock.txt
.\.venv\Scripts\python.exe -m playwright install
```

## 6. Create your API keys

1. Open [Google AI Studio's API key page](https://aistudio.google.com/apikey), sign in, and create or select a Gemini API key. Follow [Google's API key instructions](https://ai.google.dev/gemini-api/docs/api-key) if you need to configure a project.
2. Open [OpenRouter's API key settings](https://openrouter.ai/settings/keys), sign in, and create an API key.
3. Keep both keys ready for the JARVIS setup screen. They serve different providers; enter each in its matching field.

Provider access, usage limits, model availability, and any charges depend on your accounts. A key alone does not guarantee access to every configured model.

## 7. Check your microphone and speakers

1. In Windows Settings, open **System → Sound** and select your input microphone and output device.
2. Test the microphone using Windows' input test.
3. In Windows microphone privacy settings, enable microphone access for desktop apps. The menu location differs between Windows versions.
4. Use headphones if the assistant's voice feeds back into the microphone.

## 8. Start JARVIS and complete first-run setup

```powershell
.\.venv\Scripts\python.exe main.py
```

In the JARVIS window:

1. Paste your key into **GEMINI API KEY**.
2. Paste your other key into **OPENROUTER API KEY**.
3. Select **Windows** under **OPERATING SYSTEM**.
4. Click **INITIALISE SYSTEMS**.
5. Wait for the terminal's **Connected** message and the application's **JARVIS online** message. The setup screen accepting keys does not itself verify provider connectivity.
6. Try a simple spoken greeting or type a short message in the input box after the connection is established.

The first-run screen saves `config/api_keys.json` locally. The `.gitignore` excludes it, along with personal memory and temporary files. Do not paste real keys into the public repository or issue reports.

The optional `face.png` image is not included. Its absence does not prevent the interface from starting.

## 9. Run the offline checks

Close JARVIS, then run:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Expected results: no broken package requirements, followed by **Ran 9 tests** and **OK**. Tests cover imports, first-run GUI startup, CSV/Excel handling, configuration, transcript integration with a mock, and audio queue handling. They do not verify live API access, record microphone audio, or perform desktop actions.

## 10. Optional: enable audio/video conversion

For features requiring FFmpeg:

1. Open the [official FFmpeg download page](https://ffmpeg.org/download.html) and follow a Windows build link.
2. Extract the downloaded build to a permanent folder, such as `C:\Tools\ffmpeg`.
3. Find the folder containing `ffmpeg.exe` and `ffprobe.exe`, usually its `bin` subfolder.
4. Add that exact folder to your Windows user **Path** environment variable using **Edit environment variables for your account**.
5. Open a new PowerShell window and check:

```powershell
ffmpeg -version
ffprobe -version
```

Restart JARVIS after changing Path. FFmpeg is not required just to open the application.

## 11. Start and stop it next time

If you used the default clone location:

```powershell
Set-Location "$env:USERPROFILE\JARVIS"
.\.venv\Scripts\python.exe main.py
```

Saved keys are reused. You do not need to repeat installation each time. To stop JARVIS, close its window. If it remains running, press **Ctrl+C** in its terminal.

To replace API keys, close the app, edit the local `config/api_keys.json`, and restart. Keep `gemini_api_key`, `openrouter_api_key`, and `os_system` present. The file `config/api_keys.example.json` shows the format without secrets.

## 12. Update an existing Git clone

Close JARVIS and run these commands from its project folder:

```powershell
git pull --ff-only
.\.venv\Scripts\python.exe setup.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe main.py
```

If Git reports local changes or diverging branches, resolve or preserve your edits before updating; do not discard them just to make the command succeed. Local keys and memory are not tracked by Git.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| `py` or `git` is not recognized | Finish installing the corresponding tool and open a new PowerShell window. Check step 2. |
| `py install` tries to open a file named `install` | The legacy Python launcher is active. After installing the Python install manager, use `pymanager install 3.12`. |
| `failed to locate pyvenv.cfg` or Python points to another person's folder | Close JARVIS, rename the old `.venv` to `.venv.old` if that name is unused, then repeat steps 4–5. Virtual environments must be recreated on this machine. |
| Setup says to use Python 3.11 or 3.12 | Recreate the environment using `py -3.12 -m venv .venv` after setting the old environment aside. |
| `ModuleNotFoundError`, including `PyQt6` | Run setup with `.\.venv\Scripts\python.exe setup.py`, then launch using that same Python executable. |
| `No module named pip` | Run `.\.venv\Scripts\python.exe -m ensurepip --upgrade`, then repeat installation. |
| Playwright says its executable does not exist | Run `.\.venv\Scripts\python.exe -m playwright install` and let the download finish. |
| No audio input device / microphone permission error | Check step 7, reconnect the microphone, and restart JARVIS. |
| Invalid API key or 401/403 response | Check the keys in the local configuration and account permissions for the selected provider/model. |
| Rate limit / 429 response | Check provider usage limits and retry after the provider's indicated delay. |
| Model unavailable / 404 response | Check provider model availability. `LIVE_MODEL` in `main.py` selects the Gemini Live audio model; `TEXT_MODELS` and `VISION_MODELS` in `or_client.py` select OpenRouter models. Replacements must support the required feature. |
| Repeated reconnecting | Read the terminal error first; check network access, keys, model access, and microphone/output devices. |
| `ffmpeg` or `ffprobe` not found | Complete step 10, reopen PowerShell, and restart JARVIS. |
| Warning about `google.generativeai` being deprecated | Some inherited actions still use that SDK. This warning is a known limitation; it is different from a failing traceback. |

The automated checks have passed on Windows/Python 3.12. Live conversations, external services, browser control, and system-changing actions still need end-to-end validation on your computer. macOS and Linux have not been validated for this repository.
