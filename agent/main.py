"""LVA Audio agent.

Small aiohttp HTTP server on /run/lva/audio/agent.sock.
Used by lva-supervisor to query available audio devices.
"""

import asyncio
import logging
import sys
from pathlib import Path

from aiohttp import web

from .devices import get_devices

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    stream=sys.stdout,
)

_LOGGER = logging.getLogger(__name__)

AGENT_SOCK = Path("/run/lva/audio/agent.sock")


async def handle_devices(request: web.Request) -> web.Response:  # pylint: disable=unused-argument
    """Return available input/output audio devices."""
    devices = await get_devices()
    return web.json_response(devices)


async def handle_health(request: web.Request) -> web.Response:  # pylint: disable=unused-argument
    """Health check endpoint."""
    return web.json_response({"status": "ok"})


async def main() -> None:
    """Start the audio agent."""
    app = web.Application()
    app.router.add_get("/devices", handle_devices)
    app.router.add_get("/health", handle_health)

    # Remove stale socket
    if AGENT_SOCK.exists():
        AGENT_SOCK.unlink()

    runner = web.AppRunner(app, handle_signals=False)
    await runner.setup()

    site = web.UnixSite(runner, path=str(AGENT_SOCK))
    await site.start()

    _LOGGER.info("LVA audio agent listening on %s", AGENT_SOCK)

    # Run forever
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
