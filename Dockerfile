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

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Copy uv binary from official image (using latest tag for automatic updates)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Set executable permissions and prepare runtime
RUN chmod 0755 /algo/algo-docker.sh && \
    chown -R algo:algo /algo && \
    # Create volume mount point with correct ownership
    mkdir -p /data && \
    chown algo:algo /data

# Multi-arch support metadata
ARG TARGETPLATFORM
ARG BUILDPLATFORM
RUN printf "Built on: %s\nTarget: %s\n" "${BUILDPLATFORM}" "${TARGETPLATFORM}" > /algo/build-info

# Note: Running as root for bind mount compatibility with algo-docker.sh
# The script handles /data volume permissions and needs root access
# This is a Docker limitation with bind-mounted volumes
USER root

# Health check to ensure container is functional
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD /bin/uv --version || exit 1

VOLUME ["/data"]
CMD [ "/algo/algo-docker.sh" ]
ENTRYPOINT [ "/sbin/tini", "--" ]
