import re
from difflib import SequenceMatcher

import streamlit as st
import speech_recognition as sr
from commands import commands   # IMPORT


st.set_page_config(page_title="Voice Aircraft Control", page_icon="🎙", layout="centered")

st.markdown("<h1 style='text-align:center;color:white;'>🎙 Voice Command Dashboard</h1>", unsafe_allow_html=True)
st.write("")


# COMMAND LOGIC
def aircraft_response(text: str):
    """Return a tuple (matched_key, response) for the given transcript.

    - If an explicit phrase from `commands` is found as a substring of the
      cleaned transcript, return (phrase, response_string).
    - Otherwise return (None, "⚠️ Command Not Recognized").

    The UI expects a tuple so it can display both the matched phrase and the
    textual response. This keeps behavior explicit for confirmed suggestions
    and exact matches.
    """
    text = (text or "").lower()

    # Prefer explicit commands defined in commands.py
    for key in commands:
        if key in text:
            return key, commands[key]

    # No explicit command found — signal unrecognized so the UI can retry
    return None, "⚠️ Command Not Recognized"


def safe_rerun():
    """Attempt to rerun the Streamlit script in a compatible way across versions.

    Priority:
      1. call st.experimental_rerun() if present
      2. raise the Streamlit RerunException if available
      3. set a session flag and stop the script as a last-resort fallback
    """
    try:
        # Preferred API
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
            return
    except Exception:
        # fall through to other methods
        pass

    # Try raising RerunException (internal API may vary by version)
    try:
        from streamlit.runtime.scriptrunner import RerunException

        raise RerunException("manual rerun requested")
    except Exception:
        # Last resort: set a session flag and stop execution so user can take action
        try:
            st.session_state["_need_rerun"] = True
            st.stop()
        except Exception:
            # give up silently
            return


def do_listen():
    """Record from the microphone and place the transcript into session state.

    This function updates `st.session_state["speech_text"]` and returns True on
    success, False on microphone/recognition error. It does not raise.
    """
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.info("Listening... speak now")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)

        try:
            text = recognizer.recognize_google(audio)
            st.session_state["speech_text"] = text
            return True
        except Exception:
            st.session_state["speech_text"] = "Could not understand audio"
            return False
    except Exception as e:
        st.error(f"Microphone error: {e}")
        return False


def best_match(text: str, commands_dict, min_ratio: float = 0.6):
    """Return the best-matching command key and its score using SequenceMatcher.

    If no command meets min_ratio, returns (None, 0.0).
    """
    clean_text = re.sub(r'[^a-zA-Z ]', ' ', (text or '')).strip()
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


def do_listen_to(target_key: str = "speech_text"):
    """Record one phrase and store the transcript into session_state[target_key].

    Returns True on success, False on failure. Does not raise.
    """
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.info("Listening... speak now")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=6)
        try:
            text = recognizer.recognize_google(audio)
            st.session_state[target_key] = text
            return True
        except Exception:
            st.session_state[target_key] = "Could not understand audio"
            return False
    except Exception as e:
        st.error(f"Microphone error: {e}")
        return False


def best_command_match(text, commands_dict, min_ratio=0.45):
    """Return the best-matching command key and score, or (None, 0) if none match.

    This mirrors the helper in main.py to keep dashboard behavior consistent with
    the CLI: first tries substring match, then fuzzy matching via
    SequenceMatcher.
    """
    clean_text = re.sub(r'[^a-zA-Z ]', ' ', (text or '')).strip()
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


# Auto-retry configuration
MAX_AUTO_RETRIES = 2

# BUTTON TO RECORD AUDIO
if st.button("🎧 Listen Now"):
    # Clear previous run state so the dashboard can be used repeatedly
    st.session_state["retry_attempts"] = 0
    st.session_state["last_listen_ok"] = False
    st.session_state["confirmed_suggestion"] = False
    st.session_state["_need_rerun"] = False
    # clear previous transcript to make UI feedback immediate
    st.session_state["speech_text"] = ""
    # store whether the last listen succeeded (recognition produced text)
    st.session_state["last_listen_ok"] = do_listen()


# SHOW SPEECH TEXT
if "speech_text" in st.session_state:
    st.subheader("Your Speech Text:")
    st.write(st.session_state["speech_text"])

    # RESPONSE (now returns matched_key, response_text)
    matched_key, response = aircraft_response(st.session_state["speech_text"])

    st.subheader("Aircraft Response:")
    # If we have an explicit match show a stronger visual affordance and the
    # canonical phrase that matched.
    if matched_key:
        st.success(f"{matched_key} → {response}")
    else:
        st.success(response)

    # If the command wasn't recognized, try fuzzy matching and then auto-retry
    if matched_key is None and response == "⚠️ Command Not Recognized":
        st.warning("Command not recognized.")

        # Suggest a close command using fuzzy matching (mirror CLI behaviour)
        SUGGEST_THRESHOLD = 0.35
        suggested, score = best_command_match(st.session_state.get("speech_text", ""), commands, min_ratio=0.0)

        # If we have a suggestion above the threshold and it hasn't been confirmed, ask the user
        if suggested and score >= SUGGEST_THRESHOLD and not st.session_state.get("confirmed_suggestion"):
            st.info(f"Did you mean: '{suggested}'? (score {score:.2f})")
            coly, coln, colz = st.columns([1, 1, 1])
            with coly:
                if st.button("Yes — apply suggestion"):
                    st.session_state["confirmed_suggestion"] = True
                    st.session_state["speech_text"] = suggested
                    # Re-run so the new speech_text is processed as an accepted command
                    if hasattr(st, "experimental_rerun"):
                        try:
                            st.experimental_rerun()
                        except Exception:
                            st.session_state["_rerun_requested"] = True
                            st.stop()
                    else:
                        st.session_state["_rerun_requested"] = True
                        st.stop()
            with coln:
                if st.button("No — try again"):
                    # User rejected suggestion, proceed to auto-retry logic below
                    st.session_state["confirmed_suggestion"] = False
            with colz:
                # New: allow spoken confirmation (yes/no) instead of clicking
                if st.button("🎙 Speak Yes/No"):
                    # record one short phrase into a separate key for confirmation
                    ok = do_listen_to("confirm_text")
                    if ok:
                        reply = (st.session_state.get("confirm_text") or "").lower()
                        # accept common yes patterns
                        if any(w in reply for w in ("yes", "yeah", "yep", "affirm", "correct", "sure", "ok")):
                            st.session_state["confirmed_suggestion"] = True
                            st.session_state["speech_text"] = suggested
                            if hasattr(st, "experimental_rerun"):
                                try:
                                    st.experimental_rerun()
                                except Exception:
                                    st.session_state["_rerun_requested"] = True
                                    st.stop()
                            else:
                                st.session_state["_rerun_requested"] = True
                                st.stop()
                        else:
                            # treat any other reply as 'no'
                            st.session_state["confirmed_suggestion"] = False
                # Auto-voice confirmation option
                if st.checkbox("Auto-confirm by voice", value=False, key="auto_confirm_voice"):
                    # only attempt auto-confirm once per suggestion display
                    if not st.session_state.get("voice_confirm_attempted"):
                        st.session_state["voice_confirm_attempted"] = True
                        ok = do_listen_to("confirm_text")
                        if ok:
                            reply = (st.session_state.get("confirm_text") or "").lower()
                            if any(w in reply for w in ("yes", "yeah", "yep", "affirm", "correct", "sure", "ok")):
                                st.session_state["confirmed_suggestion"] = True
                                st.session_state["speech_text"] = suggested
                                if hasattr(st, "experimental_rerun"):
                                    try:
                                        st.experimental_rerun()
                                    except Exception:
                                        st.session_state["_rerun_requested"] = True
                                        st.stop()
                                else:
                                    st.session_state["_rerun_requested"] = True
                                    st.stop()

        else:
            # initialize counters if missing
            if "retry_attempts" not in st.session_state:
                st.session_state["retry_attempts"] = 0
            if "last_listen_ok" not in st.session_state:
                st.session_state["last_listen_ok"] = False

            # If the last listen failed or produced an unrecognized command, and
            # we have remaining attempts, automatically retry once.
            if st.session_state.get("retry_attempts", 0) < MAX_AUTO_RETRIES:
                st.session_state["retry_attempts"] += 1
                attempt = st.session_state["retry_attempts"]
                st.info(f"Auto-retry attempt {attempt} of {MAX_AUTO_RETRIES} — listening again...")
                ok = do_listen()
                st.session_state["last_listen_ok"] = ok
                # After do_listen() sets session_state['speech_text'], Streamlit will
                # rerun the script and re-evaluate the response. We therefore stop this run
                # to allow the UI to refresh with the new transcript.
                if hasattr(st, "experimental_rerun"):
                    try:
                        st.experimental_rerun()
                    except Exception:
                        st.session_state["_rerun_requested"] = True
                        st.stop()
                else:
                    st.session_state["_rerun_requested"] = True
                    st.stop()

            # also show a manual retry button in case auto attempts exhausted
            st.write("")
            if st.button("🔁 Try Again Manually"):
                st.session_state["retry_attempts"] = 0
                st.session_state["last_listen_ok"] = do_listen()
