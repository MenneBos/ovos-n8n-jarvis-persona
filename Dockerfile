# OVOS JARVIS Persona – Docker image
# Builds on top of the official OVOS core image and installs this plugin.
FROM smartgic/ovos-core:latest

# Root is needed to install the package system-wide
USER root

# Copy the plugin source into the image
COPY --chown=ovos:ovos . /opt/ovos-n8n-jarvis-persona/

# Install the plugin (and its dependencies) into the existing Python env
RUN pip install --no-cache-dir /opt/ovos-n8n-jarvis-persona/

# Make sure the persona config directory exists for the ovos user
RUN mkdir -p /home/ovos/.config/ovos_persona

# Drop back to the unprivileged user that OVOS expects
USER ovos
