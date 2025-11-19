## Purpose

This file tells an AI coding agent how this small project is organized, what the key runtime flows are, and the concrete places to change behavior. Keep advice specific to existing code and discoverable patterns.

## Big-picture architecture

- dashboard.py — Streamlit UI. Reads small text files (altitude.txt, speed.txt, autopilot.txt), listens via the microphone (speech_recognition), shows responses from `commands.py`, and implements auto-retry and voice-confirm flows via `st.session_state`.
- main.py — CLI recorder/transcriber. Records WAV (sounddevice), transcribes (OpenAI Whisper API by default or local Whisper if installed), queries X-Plane via `xpc` if available, and matches phrases from `commands.py` using substring-first then fuzzy matching (difflib.SequenceMatcher).
- commands.py — Canonical phrase → response dictionary. Both dashboard and main use it as the single source of truth for command phrases.
- populate_example_files.py — Creates `altitude.txt`, `speed.txt`, and `autopilot.txt` so the dashboard shows sensible defaults.
- requirements*.txt — `requirements.txt` is the minimal runtime for the dashboard (Streamlit). `requirements-optional.txt` contains optional packages (Whisper, sounddevice, plotly, xpc).

Why this structure
- Single-file components keep the demo simple: UI (dashboard) and CLI/recording (main) are intentionally separated. `commands.py` centralizes phrases so updates affect both flows.

## Key developer workflows (how to run & debug)

- Setup (PowerShell): create/activate venv then install core deps:
  - python -m venv .venv; .\.venv\Scripts\Activate.ps1
  - python -m pip install -r requirements.txt
- Optional (voice/transcription/X-Plane): python -m pip install -r requirements-optional.txt
- Populate example files (one-time): python populate_example_files.py
- Run dashboard (UI): python -m streamlit run dashboard.py
- Run CLI recorder/transcriber: python main.py
  - Useful flags: `--debug` prints cleaned transcript and best-match score. `--model` selects Whisper model (if installed). `--backend` selects `openai` or `whisper`.

Environment variables that matter
- OPENAI_API_KEY — required if using the OpenAI transcription backend in `main.py`.
- TRANSCRIBE_BACKEND — defaults to `openai`; set to `whisper` to force local Whisper.
- WHISPER_MODEL — default model name when using local Whisper (e.g. tiny, base).
- FFMPEG_BIN — if ffmpeg is not on PATH, set this to a folder containing ffmpeg; `main.py` will append it to PATH.

## Project-specific conventions & patterns

- commands.py is authoritative. Add new phrases there as plain lowercase strings mapped to their textual response. Example:
  - "what is the altitude": "Altitude is 15000 feet"
- Matching algorithm (both CLI + UI):
  1. Substring match: if a phrase from `commands.py` is contained verbatim in the cleaned transcript, that wins (score 1.0).
  2. Fuzzy fallback: difflib.SequenceMatcher ratio is used when no substring match is found. Thresholds used in code:
     - `dashboard.best_match()` default min_ratio = 0.6 (stricter for interactive UI suggestions)
     - `best_command_match()` (dashboard + main) default min_ratio = 0.45
  Use `--debug` on `main.py` to print cleaned transcript and best score when tuning phrase wording.

- Streamlit session_state keys the UI relies on (search for these in `dashboard.py`):
  - `speech_text`, `retry_attempts`, `last_listen_ok`, `confirmed_suggestion`, `_need_rerun`, `confirm_text`, `auto_confirm_voice`, `voice_confirm_attempted`
  Editing UI behavior should preserve these keys or update all places that reference them.

- Auto-retry and confirmation patterns:
  - MAX_AUTO_RETRIES = 2 in `dashboard.py` (automatic re-listen up to two times)
  - Voice confirmation accepts common tokens: yes/yeah/yep/affirm/correct/sure/ok

## Integration points & optional dependencies

- sounddevice — local microphone recording in `main.py`. If missing, `main.py` raises a helpful error.
- whisper (local) — optional transcription model. `main.py` supports both local whisper and OpenAI API.
- OpenAI API — `main.py` posts WAV to OpenAI's /v1/audio/transcriptions when backend is `openai` (requires OPENAI_API_KEY).
- xpc (XPlaneConnect) — optional; `main.py` will try to query aircraft position when installed.
- ffmpeg — detected via PATH or `FFMPEG_BIN`. Required by some Whisper/ffmpeg backends.

## Safe places to change behavior

- Add commands: edit `commands.py` (small, low-risk change). Then test with `dashboard.py`'s Listen Now or `python main.py --debug`.
- Tweak matching thresholds: update min_ratio values in `dashboard.py` and `main.py` to keep CLI/UI consistent.
- Add richer responses or structured outputs: consider changing values in `commands.py` into small dicts if you need metadata (but update both `dashboard.py` and `main.py` which expect a string response).

## Files to inspect first when working on a change

- `commands.py` — canonical phrases.
- `dashboard.py` — Streamlit UI, session_state logic, auto-retry, voice-confirm flow.
- `main.py` — recording, transcription backends, fuzzy matching and CLI debug flow.
- `populate_example_files.py` — creates the text files `dashboard.py` reads.
- `requirements-optional.txt` — optional integrations to install for full features.

## Minimal checks an AI agent should run before proposing changes

1. Run `python populate_example_files.py` locally so `dashboard.py` has inputs.
2. Run `python -m streamlit run dashboard.py` and test the Listen flow (or run `python main.py --debug` for CLI verification).
3. If proposing dependency changes, verify `requirements*.txt` is updated and that the project still runs with Streamlit.

---
If anything here is unclear or you'd like me to expand examples (e.g., a small unit test that validates fuzzy matching thresholds, or an example PR that adds a new command), tell me which area to expand and I'll update this file.
