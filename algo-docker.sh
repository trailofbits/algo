#!/usr/bin/env bash

set -eEo pipefail

ALGO_DIR="/algo"
DATA_DIR="/data"

umask 0077

usage() {
    retcode="${1:-0}"
    echo "To run algo from Docker:"
    echo ""
    echo "docker run --cap-drop=all -it -v <path to configurations>:"${DATA_DIR}" ghcr.io/trailofbits/algo:latest"
    echo ""
    exit ${retcode}
}

if [ ! -f "${DATA_DIR}"/config.cfg ] ; then
  echo "Looks like you're not bind-mounting your config.cfg into this container."
  echo "algo needs a configuration file to run."
  echo ""
  usage -1
fi

if [ ! -e /dev/console ] ; then
  echo "Looks like you're trying to run this container without a TTY."
  echo "If you don't pass `-t`, you can't interact with the algo script."
  echo ""
  usage -1
fi

# To work around problems with bind-mounting Windows volumes, we need to
# copy files out of ${DATA_DIR}, ensure appropriate line endings and permissions,
# then copy the algo-generated files into ${DATA_DIR}.

tr -d '\r' < "${DATA_DIR}"/config.cfg > "${ALGO_DIR}"/config.cfg
test -d "${DATA_DIR}"/configs && rsync -qLktr --delete "${DATA_DIR}"/configs "${ALGO_DIR}"/

"${ALGO_DIR}"/algo "${ALGO_ARGS[@]}"
retcode=${?}

rsync -qLktr --delete "${ALGO_DIR}"/configs "${DATA_DIR}"/
exit ${retcode}
