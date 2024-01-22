ARG PYTHON_VERISON=3.12

FROM mcr.microsoft.com/devcontainers/python:${PYTHON_VERISON}

ARG DEVCONTAINER_USER=vscode

USER ${DEVCONTAINER_USER}

# Pre-create volumes
RUN mkdir -p /home/${DEVCONTAINER_USER}/workspace && \
    mkdir -p /home/${DEVCONTAINER_USER}/.config/fish && \
    mkdir -p /home/${DEVCONTAINER_USER}/.local/share/fish
