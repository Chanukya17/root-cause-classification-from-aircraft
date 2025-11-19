HEAD
import os, shutil
FFMPEG_BIN = r"C:\Users\seeke\Downloads\ffmpeg-2025-11-02-git-f5eb11a71d-essentials_build\ffmpeg-2025-11-02-git-f5eb11a71d-essentials_build\bin"
os.environ["PATH"] += os.pathsep + FFMPEG_BIN
print("ffmpeg path:", shutil.which("ffmpeg") or "NOT FOUND")

import sounddevice as sd
from scipy.io.wavfile import write
import whisper
from commands import commands
import re

print("Testing audio device...")
print(sd.query_devices())

fs = 44100  # sample rate

print("Recording..... Speak your command")
duration = 4  # seconds
recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
sd.wait()
write("cmd.wav", fs, recording)

print("Converting speech to text...")
model = whisper.load_model("base")
result = model.transcribe("cmd.wav")
text = result["text"].lower()
print("You said:", text)

# command matching
matched = False
clean_text = re.sub(r'[^a-zA-Z ]', '', text)

for phrase in commands:
    if phrase in clean_text:
        print("Cockpit Response:", commands[phrase])
        matched = True
        break

if not matched:
    print("Command not recognized. Try speaking clearer.")

import os
import shutil
import tempfile
import logging
import numpy as np
from scipy.io.wavfile import write

# Optional imports - we import inside try blocks to provide helpful errors
try:
    import sounddevice as sd
except Exception:
    sd = None

try:
    import whisper
except Exception:
    whisper = None

try:
    import xpc
except Exception:
    xpc = None

from commands import commands
import re
import argparse
import sys
from difflib import SequenceMatcher
import requests
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_ffmpeg_on_path():
    """Ensure ffmpeg is available on PATH or log a warning.

    If an environment variable FFMPEG_BIN is set, we'll append it to PATH.
    Otherwise we rely on shutil.which('ffmpeg').
    """
    if shutil.which("ffmpeg"):
        logger.info("ffmpeg found: %s", shutil.which("ffmpeg"))
        return

    env_path = os.environ.get("FFMPEG_BIN")
    if env_path and os.path.isdir(env_path):
        os.environ["PATH"] += os.pathsep + env_path
        if shutil.which("ffmpeg"):
            logger.info("ffmpeg found after adding FFMPEG_BIN: %s", shutil.which("ffmpeg"))
            return

    # If the user provided a known local ffmpeg build path, try to add it.
    # Replace or extend this path with your local installation if different.
    user_ffmpeg = r"C:\Users\seeke\Downloads\ffmpeg-2025-11-02-git-f5eb11a71d-essentials_build\ffmpeg-2025-11-02-git-f5eb11a71d-essentials_build\bin"
    if os.path.isdir(user_ffmpeg):
        os.environ["PATH"] += os.pathsep + user_ffmpeg
        if shutil.which("ffmpeg"):
            logger.info("ffmpeg found after adding user path: %s", shutil.which("ffmpeg"))
            return
        else:
            logger.info("Added user ffmpeg path to PATH but ffmpeg still not found: %s", user_ffmpeg)

    logger.warning("ffmpeg not found on PATH. Some audio backends or transcription models may need ffmpeg installed.")


def record_command(duration=4, fs=44100):
    """Record audio from the default input device and return the filename.

    Writes a temporary WAV file and returns its path. Caller should remove it.
    """
    if sd is None:
        raise RuntimeError("sounddevice is not installed. Install it with: pip install sounddevice")

    logger.info("Recording for %s seconds (fs=%s)", duration, fs)
    try:
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
    except Exception as e:
        raise RuntimeError(f"Failed to record audio: {e}") from e

    # Convert float32 [-1,1] to int16 for WAV
    data = recording
    try:
        data = (data * 32767).astype(np.int16)
    except Exception:
        # fallback: attempt to coerce
        data = np.asarray(data).astype(np.int16)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_name = tmp.name
    tmp.close()
    write(tmp_name, fs, data)
    logger.info("Wrote recorded audio to %s", tmp_name)
    return tmp_name


def transcribe_with_whisper(wav_path: str, model_name: Optional[str] = None) -> str:
    if whisper is None:
        raise RuntimeError("Whisper is not installed. Install via: pip install openai-whisper")
    if model_name is None:
        model_name = os.environ.get("WHISPER_MODEL", "tiny")
    logger.info("Loading Whisper model '%s' (this may take a while)...", model_name)
    model = whisper.load_model(model_name)
    logger.info("Transcribing %s with Whisper", wav_path)
    result = model.transcribe(wav_path)
    text = result.get("text", "").lower()
    logger.info("Whisper transcription result: %s", text)
    return text


def transcribe_with_openai(wav_path: str) -> str:
    """Transcribe audio using OpenAI's speech-to-text API.

    Requires environment variable OPENAI_API_KEY to be set. This avoids
    local model downloads and ffmpeg dependency (OpenAI handles the
    backend). The endpoint used is /v1/audio/transcriptions.
    """
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")

    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {key}"}
    # Use multipart/form-data upload
    with open(wav_path, "rb") as fh:
        files = {"file": (os.path.basename(wav_path), fh, "audio/wav")}
        data = {"model": "whisper-1"}
        logger.info("Sending audio to OpenAI for transcription: %s", wav_path)
        resp = requests.post(url, headers=headers, data=data, files=files, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI transcription failed ({resp.status_code}): {resp.text}")
    obj = resp.json()
    text = obj.get("text", "").lower()
    logger.info("OpenAI transcription result: %s", text)
    return text


def transcribe_file(wav_path: str, backend: str = "openai", model_name: Optional[str] = None) -> str:
    """Dispatch transcription to the selected backend.

    backend: 'openai' or 'whisper'
    """
    backend = (backend or os.environ.get("TRANSCRIBE_BACKEND", "openai")).lower()
    if backend == "openai":
        return transcribe_with_openai(wav_path)
    elif backend == "whisper":
        return transcribe_with_whisper(wav_path, model_name)
    else:
        raise ValueError(f"Unknown transcription backend: {backend}")


def query_xplane_altitude():
    if xpc is None:
        logger.warning("XPlaneConnect (xpc) not installed. Skipping X-Plane position query.")
        return None
    try:
        with xpc.XPlaneConnect() as client:
            posi = client.getPOSI()
            altitude_m = posi[2]
            logger.info("X-Plane altitude: %s m", altitude_m)
            return altitude_m
    except Exception as e:
        logger.warning("Failed to query X-Plane: %s", e)
        return None


def best_command_match(text, commands_dict, min_ratio=0.45):
    """Return the best-matching command key and score, or (None, 0) if none match."""
    clean_text = re.sub(r'[^a-zA-Z ]', ' ', text).strip()
    # First try substring match
    for phrase in commands_dict:
        if phrase in clean_text:
            return phrase, 1.0

    # Otherwise use fuzzy ratio against each phrase
    best = None
    best_score = 0.0
    for phrase in commands_dict:
        score = SequenceMatcher(None, phrase, clean_text).ratio()
        if score > best_score:
            best_score = score
            best = phrase

    if best_score >= min_ratio:
        return best, best_score
    return None, 0.0


def main():
    ensure_ffmpeg_on_path()

    try:
        wav = record_command()
    except Exception as e:
        logger.error("Recording failed: %s", e)
        return

    try:
        text = transcribe_file(wav)
    except Exception as e:
        logger.error("Transcription failed: %s", e)
        text = ""

    # Clean up temporary wav
    try:
        os.remove(wav)
    except Exception:
        pass

    if text:
        print("You said:", text)

    altitude_m = query_xplane_altitude()
    if altitude_m is not None:
        print(f"Altitude: {altitude_m} m")

    matched_key, score = best_command_match(text, commands)
    if matched_key:
        print("Cockpit Response:", commands[matched_key])
    else:
        print("Command not recognized. Try speaking clearer.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Record a short audio clip, transcribe with Whisper, and match commands.")
    parser.add_argument("--model", help="Whisper model to use (tiny, base, etc.). If omitted, WHISPER_MODEL env var or 'tiny' is used.")
    parser.add_argument("--duration", type=float, default=4.0, help="Recording duration in seconds")
    parser.add_argument("--backend", choices=["openai", "whisper"], help="Transcription backend to use (openai or whisper). Defaults to TRANSCRIBE_BACKEND env or 'openai'.")
    parser.add_argument("--debug", action="store_true", help="Show debug info (cleaned transcript, best match and score)")
    args = parser.parse_args()

    # Allow passing model via CLI; otherwise transcribe_file will use env or default
    def main_with_args():
        ensure_ffmpeg_on_path()

        try:
            wav = record_command(duration=args.duration)
        except Exception as e:
            logger.error("Recording failed: %s", e)
            return

        try:
            # pass backend from CLI if provided
            backend = args.backend or os.environ.get("TRANSCRIBE_BACKEND", "openai")
            text = transcribe_file(wav, backend=backend, model_name=args.model)
        except Exception as e:
            logger.error("Transcription failed: %s", e)
            text = ""
            # If OpenAI failed due to quota or other API error, and Whisper is
            # available locally, try falling back to local Whisper to avoid
            # repeated API calls (useful when quota is exceeded).
            err_text = str(e)
            if backend == "openai" and whisper is not None:
                # check if ffmpeg is present for Whisper preprocessing
                if shutil.which("ffmpeg"):
                    logger.info("Falling back to local Whisper because OpenAI backend failed.")
                    try:
                        text = transcribe_with_whisper(wav, model_name=args.model)
                    except Exception as e2:
                        logger.error("Local Whisper fallback also failed: %s", e2)
                else:
                    logger.warning("Cannot fallback to Whisper: ffmpeg not found on PATH.")

        try:
            os.remove(wav)
        except Exception:
            pass
        
        if text:
            print("You said:", text)

        altitude_m = query_xplane_altitude()
        if altitude_m is not None:
            print(f"Altitude: {altitude_m} m")

        # For debugging/suggestion, get best match without enforcing threshold
        best_key, best_score = best_command_match(text, commands, min_ratio=0.0)
        accepted = best_score >= 0.45

        if args.debug:
            clean_text = re.sub(r'[^a-zA-Z ]', ' ', text).strip()
            print("[DEBUG] cleaned transcript:", repr(clean_text))
            print(f"[DEBUG] best match: {best_key!r} score={best_score:.3f}")

        if accepted and best_key:
            print("Cockpit Response:", commands[best_key])
        else:
            if best_key:
                # Interactive confirmation if running in a terminal
                suggestion = best_key
                msg = f"Command not recognized. Closest match: '{suggestion}' (score {best_score:.2f})."
                if sys.stdin and sys.stdin.isatty():
                    msg += f"\nDid you mean '{suggestion}'? [y/N]: "
                    resp = input(msg)
                    if resp.strip().lower().startswith('y'):
                        print("Cockpit Response:", commands[suggestion])
                    else:
                        print("OK — command not executed. Try speaking clearer or add the phrase to commands.py.")
                else:
                    print(msg + " Try speaking clearer or add the phrase to commands.py.")
            else:
                print("Command not recognized. Try speaking clearer.")

    main_with_args()

 57d5769 (Add copilot instructions and improve dashboard match display)
