"""Query PulseAudio for available input and output devices via pactl."""
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

PULSE_SERVER = "unix:/run/lva/audio/pulse/native"


async def _run_pactl(*args: str) -> str:
    """Run a pactl command and return stdout."""
    proc = await asyncio.create_subprocess_exec(
        "pactl",
        f"--server={PULSE_SERVER}",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"pactl failed: {stderr.decode().strip()}")
    return stdout.decode()


def _parse_pactl_list(output: str, section: str) -> list[dict[str, str]]:
    """Parse pactl list sinks/sources output into a list of dicts."""
    devices : list[dict[str, str]] = []
    current: dict[str, str] = {}
    in_section = False

    for line in output.splitlines():
        if line.startswith(section):
            if current:
                devices.append(current)
            current = {"name": "", "description": "", "state": ""}
            in_section = True
        elif in_section:
            line = line.strip()
            if line.startswith("Name:"):
                current["name"] = line.split(":", 1)[1].strip()
            elif line.startswith("Description:"):
                current["description"] = line.split(":", 1)[1].strip()
            elif line.startswith("State:"):
                current["state"] = line.split(":", 1)[1].strip()

    if current:
        devices.append(current)

    return [d for d in devices if d["name"]]


async def get_devices() -> dict[str, list[dict[str, str]]] | dict[str, list[dict[str, str]] | str]:
    """Return available input and output audio devices."""
    try:
        sinks_out   = await _run_pactl("list", "sinks")
        sources_out = await _run_pactl("list", "sources")

        outputs = _parse_pactl_list(sinks_out, "Sink #")
        inputs  = _parse_pactl_list(sources_out, "Source #")

        # Filter out monitor sources (loopback devices)
        inputs = [i for i in inputs if not i["name"].endswith(".monitor")]

        return {
            "inputs":  inputs,
            "outputs": outputs,
        }
    except Exception as err: # pylint: disable=broad-exception-caught
        _LOGGER.error("Failed to query audio devices: %s", err)
        return {"inputs": [], "outputs": [], "error": str(err)}