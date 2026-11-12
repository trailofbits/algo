# syntax=docker/dockerfile:1
FROM python:3.12-alpine

ARG VERSION="git"
# Removed rust/cargo (not needed with uv), simplified package list
ARG PACKAGES="bash openssh-client openssl rsync tini"

LABEL name="algo" \
      version="${VERSION}" \
      description="Set up a personal IPsec VPN in the cloud" \
      maintainer="Trail of Bits <https://github.com/trailofbits/algo>" \
      org.opencontainers.image.source="https://github.com/trailofbits/algo" \
      org.opencontainers.image.description="Algo VPN - Set up a personal IPsec VPN in the cloud" \
      org.opencontainers.image.licenses="AGPL-3.0"

# Install system packages in a single layer
RUN apk --no-cache add ${PACKAGES} && \
    adduser -D -H -u 19857 algo && \
    mkdir -p /algo /algo/configs

WORKDIR /algo

# Use the same uv version as CI and keep development tools out of the image.
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /bin/uv
ENV UV_NO_DEV=true

# Copy dependency files and install in single layer for better optimization
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

# Copy application code
COPY . .

# Install Ansible Galaxy collections for cloud provider modules
RUN uv run --locked --no-dev ansible-galaxy collection install -r requirements.yml

# Set executable permissions and prepare runtime
# Note: /algo must remain root-owned for --cap-drop=all compatibility
# (root without CAP_DAC_OVERRIDE cannot write to files owned by others)
RUN chmod 0755 /algo/algo-docker.sh && \
    mkdir -p /data

# Multi-arch support metadata
ARG TARGETPLATFORM
ARG BUILDPLATFORM
RUN printf "Built on: %s\nTarget: %s\n" "${BUILDPLATFORM}" "${TARGETPLATFORM}" > /algo/build-info

# Note: Running as root for bind mount compatibility with algo-docker.sh
# Bind mounts must allow UID 0 to read and write the configuration directory.
# This is a Docker limitation with bind-mounted volumes
USER root

# Health check to ensure container is functional
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD /bin/uv --version || exit 1

VOLUME ["/data"]
CMD [ "/algo/algo-docker.sh" ]
ENTRYPOINT [ "/sbin/tini", "--" ]
