# Base image updated by Renovate, update versionCompatibility on Alpine base bump
FROM ghcr.io/home-assistant/base:3.23-2026.05.0@sha256:3036cd72ba7755263cd103acc77cb0b438462720c2c8c23b7c2b52e52d7f4b50

SHELL ["/bin/ash", "-o", "pipefail", "-c"]

ARG PULSE_VERSION="17.0"

# Install system dependencies and build engines
RUN \
    --mount=type=bind,source=./patches/,target=/usr/src/patches \
    set -x \
    && apk add --no-cache \
        eudev \
        eudev-libs \
        libintl \
        libltdl \
        alsa-utils \
        alsa-lib \
        alsa-plugins-pulse \
        alsa-topology-conf \
        alsa-ucm-conf \
        dbus-libs \
        tdb-libs \
        bluez-libs \
        libsndfile \
        speexdsp \
        openssl \
        fftw \
        soxr \
        sbc \
        python3 \
        py3-pip \
        mpv-libs \ 
        mpv \
    && apk add --no-cache --virtual .build-deps \
        meson \
        build-base \
        tdb-dev \
        alsa-lib-dev \
        dbus-dev \
        glib-dev \
        libsndfile-dev \
        soxr-dev \
        fftw-dev \
        bluez-dev \
        openssl-dev \
        speexdsp-dev \
        eudev-dev \
        sbc-dev \
        libtool \
        git \
        m4 \
        patch \
    \
    # Compile PulseAudio from source with absolute ROOT authorization parameters
    && git clone -b v${PULSE_VERSION} --depth 1 \
        https://github.com/pulseaudio/pulseaudio /usr/src/pulseaudio \
    && cd /usr/src/pulseaudio \
    && for i in /usr/src/patches/*.patch; do \
        patch -d /usr/src/pulseaudio -p 1 < "${i}"; done \
    && meson \
        --prefix=/usr \
        --sysconfdir=/etc \
        --localstatedir=/var \
        --optimization=3 \
        --buildtype=plain \
        -Datomic-arm-linux-helpers=true \
        -Datomic-arm-memory-barrier=false \
        -Dgcov=false \
        -Dman=false \
        -Dtests=false \
        -Dsystem_user=root \
        -Dsystem_group=root \
        -Daccess_group=root \
        -Ddatabase=tdb \
        -Dalsa=enabled \
        -Dasyncns=disabled \
        -Davahi=disabled \
        -Dbluez5=enabled \
        -Ddbus=enabled \
        -Dfftw=enabled \
        -Dglib=enabled \
        -Dgsettings=disabled \
        -Dgtk=disabled \
        -Dhal-compat=false \
        -Dipv6=false \
        -Djack=disabled \
        -Dlirc=disabled \
        -Dopenssl=enabled \
        -Dorc=disabled \
        -Dsamplerate=disabled \
        -Dsoxr=enabled \
        -Dspeex=enabled \
        -Dsystemd=disabled \
        -Dudev=enabled \
        -Dx11=disabled \
        -Ddoxygen=false \
        -Dudevrulesdir=/usr/lib/udev/rules.d \
        . output \
    && ninja -C output \
    && ninja -C output install \
    \
    # Clean up compilation workspace dependencies
    && apk del .build-deps \
    && rm -rf \
        /usr/src/pulseaudio

# Install Python agent core requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --prefer-binary --break-system-packages -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Copy application source and configurations
COPY agent/ /usr/src/lva-audio/agent/
COPY rootfs /

LABEL \
    io.lva.type="audio" \
    org.opencontainers.image.title="LVA Audio" \
    org.opencontainers.image.description="Audio container for LVA-OS — PulseAudio + device agent" \
    org.opencontainers.image.authors="aryanhasgithub" \
    org.opencontainers.image.url="https://github.com/aryanhasgithub/lva-os" \
    org.opencontainers.image.licenses="Apache License 2.0"
