"""Subprocess worker for audio device discovery."""

import contextlib
import json
import os

TARGET_SOCKET = "unix:/run/lva/audio/pulse/native"


@contextlib.contextmanager
def scoped_pulse_server(socket_path: str):
    """Temporarily set PULSE_SERVER, restoring original value on exit."""
    original = os.environ.get("PULSE_SERVER")
    os.environ["PULSE_SERVER"] = socket_path
    try:
        yield
    finally:
        if original is None:
            os.environ.pop("PULSE_SERVER", None)
        else:
            os.environ["PULSE_SERVER"] = original


if __name__ == "__main__":
    import time

    import soundcard as sc
    from mpv import MPV

    # --- Microphones via soundcard ---
    with scoped_pulse_server(TARGET_SOCKET):
        microphones = [mic.name for mic in sc.all_microphones()]

    # --- Speakers via mpv ---
    # start_event_thread=True is required; without it audio_device_list never populates.
    with scoped_pulse_server(TARGET_SOCKET):
        player = MPV(start_event_thread=True)

    try:
        # Give mpv's event thread time to deliver the device list.
        time.sleep(0.3)
        speakers = [
            s["name"]
            for s in (player.audio_device_list or [])
            if "name" in s
            and (
                s["name"] == "auto"
                or s["name"].startswith("pulse/")
            )
        ]
    finally:
        player.terminate()

    print(json.dumps({"microphones": microphones, "speakers": speakers}))