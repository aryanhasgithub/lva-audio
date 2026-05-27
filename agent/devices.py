import asyncio
import contextlib
import logging
import os
import soundcard as sc
from mpv import MPV

_LOGGER = logging.getLogger(__name__)
TARGET_SOCKET = "unix:/run/lva/audio/pulse/native"

@contextlib.contextmanager
def scoped_pulse_server(socket_path: str):
    """Safely isolates the custom socket within a thread-safe window, restoring state afterwards."""
    original_value = os.environ.get("PULSE_SERVER")
    os.environ["PULSE_SERVER"] = socket_path
    try:
        yield
    finally:
        if original_value is None:
            os.environ.pop("PULSE_SERVER", None)
        else:
            os.environ["PULSE_SERVER"] = original_value


def _fetch_microphones_sync() -> list[str]:
    # soundcard scans the environment context dynamically inside this block
    with scoped_pulse_server(TARGET_SOCKET):
        return [mic.name for mic in sc.all_microphones()]


async def _get_microphones() -> list[str]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _fetch_microphones_sync)


async def _get_speakers() -> list[str]:
    # mpv captures the environment *only* during instantiation
    with scoped_pulse_server(TARGET_SOCKET):
        player = MPV(start_event_thread=False)
        
    try:
        await asyncio.sleep(0.05)
        speakers = player.audio_device_list
        return [speaker["name"] for speaker in speakers if "name" in speaker]
    finally:
        player.terminate()


async def get_devices() -> dict[str, list[str] | str]:
    """Concurrent, environment-safe discovery pipeline."""
    try:
        async with asyncio.TaskGroup() as tg:
            mic_task = tg.create_task(_get_microphones())
            speaker_task = tg.create_task(_get_speakers())
            
        return {
            "microphones": mic_task.result(),
            "speakers": speaker_task.result(),
        }
    except Exception as err: # pylint: disable=broad-exception-caught
        _LOGGER.error("Failed to query audio devices: %s", err)
        return {"microphones": [], "speakers": [], "error": str(err)}
