#!/usr/bin/with-contenv bashio
# ==============================================================================
# Initialize file system layout 
# ==============================================================================

mkdir -p /data/external
mkdir -p /data/states
mkdir -p /run/lva/audio/
mkdir -p /run/lva/audio/pulse

chown -R root:root /data/states
chown -R root:root /run/lva/audio