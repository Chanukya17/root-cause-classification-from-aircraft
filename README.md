 HEAD
# Voice Command Based Aircraft Cockpit Assistant using Speech Recognition

This project converts pilot voice commands into cockpit actions using Speech Recognition (Whisper model).  
The system listens from mic, converts speech to text and responds with aircraft status like altitude, speed, fuel, landing gear etc.  
Domain is Aerospace and core tech used is Speech Recognition.  
This project aims to make cockpit control more hands-free and intelligent using AI.

# Voice Command Based Aircraft (AI Cockpit Assistant)

Voice Command Based Aircraft Cockpit Assistant using Speech Recognition

This project converts pilot voice commands into cockpit actions using speech recognition (Whisper model) and local control logic. The system listens from the microphone, converts speech to text, and responds with aircraft status like altitude, speed, fuel, and landing gear. The goal is to make cockpit interaction more hands-free and intelligent using AI.

What this repo provides

This repository contains:
- `dashboard.py` — Streamlit dashboard showing altitude, airspeed, and autopilot status. If `plotly` is installed, the dashboard uses Plotly gauges for nicer visuals; otherwise it falls back to a basic gauge implementation.
- `main.py` — Records audio, transcribes with Whisper (optional), queries X-Plane (optional), and matches commands from `commands.py`.
- `commands.py` — A dictionary mapping spoken phrases to responses. Easy to extend.
- `populate_example_files.py` — Helper that creates `altitude.txt`, `speed.txt`, and `autopilot.txt` with sensible defaults.
- `requirements.txt` — Core requirement for the dashboard (pinned Streamlit).
- `requirements-optional.txt` — Optional dependencies for voice transcription and X-Plane integration (includes `plotly`).
- `requirements-full.txt` — Fully pinned list of packages currently installed in the provided venv for exact reproducibility.

What is included
- `dashboard.py` — Streamlit dashboard showing altitude, airspeed, and autopilot status. Uses a small fallback gauge if a third-party `st_gauge` is not available.
- `main.py` — Records audio, transcribes with Whisper (optional), queries X-Plane (optional), and matches commands from `commands.py`.
- `commands.py` — A dictionary mapping spoken phrases to responses.
- `populate_example_files.py` — Helper that creates `altitude.txt`, `speed.txt`, and `autopilot.txt` with sensible defaults so the dashboard shows values immediately.
- `requirements.txt` — Core requirement for the dashboard (pinned Streamlit).
- `requirements-optional.txt` — Optional dependencies for voice transcription and X-Plane integration.

Quick start (recommended)

1. Create and activate a virtual environment (PowerShell):

```powershell
cd "C:\Users\seeke\OneDrive\Desktop\voice command based aircraft"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script, run (one-time) or use the venv Python directly (see notes below).

2. Install core requirements (dashboard):

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. (Optional) Install voice/transcription/X-Plane dependencies:

```powershell
python -m pip install -r requirements-optional.txt
```

4. Populate example files (one-time):

```powershell
python populate_example_files.py
```

5. Run the dashboard:

```powershell
python -m streamlit run dashboard.py
```

Run `main.py` (voice capture & transcription)
- `main.py` depends on optional packages. If you installed the optional requirements, run:

```powershell
python main.py
```

Notes and troubleshooting
- If you cannot run `Activate.ps1` due to execution policies, either run the venv python directly (`.\.venv\Scripts\python.exe -m streamlit run dashboard.py`) or set the `CurrentUser` ExecutionPolicy to `RemoteSigned`.
- `main.py` will attempt to detect `ffmpeg` on PATH. If Whisper requires ffmpeg and it's not installed, install ffmpeg or set the `FFMPEG_BIN` environment variable pointing to the ffmpeg `bin` folder.
- If you see "sounddevice is not installed" or similar, install the optional dependencies.

Contributing

Small, self-contained improvements (better matching, nicer gauges, additional commands) are welcome. Open a PR with changes and brief test notes.

Security & privacy

The project records audio locally and writes temporary WAV files; no audio is uploaded by default. If you enable cloud transcription or external services, review their privacy and security policies.
 57d5769 (Add copilot instructions and improve dashboard match display)
