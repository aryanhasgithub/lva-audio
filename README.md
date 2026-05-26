To run use
```
docker run --rm \
    --privileged \
    -v /run/udev:/run/udev:ro \
    -v /run/lva/audio:/run/lva/audio \
    -v /data/states:/data/states \
    ghcr.io/aryanhasgithub/lva-audio:latest
```
