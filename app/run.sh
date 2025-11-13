#!/usr/bin/env bash

set -e

ALGO_DIR="/algo"
DATA_DIR="/data"

if [ -z ${VIRTUAL_ENV+x} ]
then
  ACTIVATE_SCRIPT="/algo/.env/bin/activate"
  if [ -f "$ACTIVATE_SCRIPT" ]
  then
    # shellcheck source=/dev/null
    source "$ACTIVATE_SCRIPT"
  else
    echo "$ACTIVATE_SCRIPT not found.  Did you follow documentation to install dependencies?"
    exit 1
  fi
fi

tr -d '\r' < "${DATA_DIR}"/config.cfg > "${ALGO_DIR}"/config.cfg
test -d "${DATA_DIR}"/configs && rsync -qLktr --delete "${DATA_DIR}"/configs "${ALGO_DIR}"/
python app/server.py
rsync -qLktr --delete "${ALGO_DIR}"/configs "${DATA_DIR}"/
exit ${retcode}
