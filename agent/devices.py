"""Audio device discovery for the LVA audio agent.

Spawns worker.py as a subprocess so that blocking libmpv/soundcard calls
cannot freeze the asyncio event loop.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

_LOGGER = logging.getLogger(__name__)

# worker.py lives alongside this file
_WORKER = Path(__file__).parent / "worker.py"


async def get_devices() -> dict[str, list[str] | str]:
    """Return available input/output audio devices.

    Spawns a subprocess to isolate blocking native library calls (libmpv,
    soundcard) from the agent event loop. A 10-second timeout guards against
    PulseAudio hangs.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(_WORKER),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=10.0
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            _LOGGER.error("Device discovery subprocess timed out")
            return {"microphones": [], "speakers": [], "error": "timeout"}

        if proc.returncode != 0:
            err = stderr.decode().strip()
            _LOGGER.error("Device discovery subprocess failed: %s", err)
            return {"microphones": [], "speakers": [], "error": err}

        return json.loads(stdout.decode())  # type: ignore[no-any-return]

    except Exception as err:  # pylint: disable=broad-exception-caught
        _LOGGER.error("Failed to query audio devices: %s", err)
        return {"microphones": [], "speakers": [], "error": str(err)}