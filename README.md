# Audio

PulseAudio implementation for lva-os.

This container ships the upstream ALSA configs and base settings for PulseAudio.

## How it works

The central audio container handles the ALSA settings and runs a PulseAudio service on top.
The PulseAudio service is exposed to lva and the supervisor over a UNIX sock run by a custom python agent.
