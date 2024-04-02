FROM python:3.11-alpine

ARG VERSION="git"
ARG PACKAGES="bash libffi openssh-client openssl rsync tini gcc libffi-dev linux-headers make musl-dev openssl-dev rust cargo"

LABEL name="algo" \
      version="${VERSION}" \
      description="Set up a personal IPsec VPN in the cloud" \
      maintainer="Trail of Bits <http://github.com/trailofbits/algo>"

RUN apk --no-cache add ${PACKAGES}
RUN adduser -D -H -u 19857 algo
RUN mkdir -p /algo && mkdir -p /algo/configs

WORKDIR /algo
COPY requirements.txt .
RUN python3 -m pip --no-cache-dir install -U pip && \
    python3 -m pip --no-cache-dir install virtualenv && \
    python3 -m virtualenv .env && \
    source .env/bin/activate && \
    python3 -m pip --no-cache-dir install -r requirements.txt
COPY . .
RUN chmod 0755 /algo/algo-docker.sh

# Because of the bind mounting of `configs/`, we need to run as the `root` user
# This may break in cases where user namespacing is enabled, so hopefully Docker
# sorts out a way to set permissions on bind-mounted volumes (`docker run -v`)
# before userns becomes default
# Note that not running as root will break if we don't have a matching userid
# in the container. The filesystem has also been set up to assume root.
USER root
CMD [ "/algo/algo-docker.sh" ]
ENTRYPOINT [ "/sbin/tini", "--" ]
