#!/usr/bin/env bash

set -euo pipefail

ALGO_DIR="/algo"
DATA_DIR="/data"

umask 0077

usage() {
  retcode="${1:-0}"
  echo "To run algo from Docker:"
  echo ""
  echo "docker run --cap-drop=all -it -v <path to configurations>:${DATA_DIR} ghcr.io/trailofbits/algo:latest"
  echo ""
  exit "${retcode}"
}

if [ ! -f "${DATA_DIR}"/config.cfg ]; then
  echo "Looks like you're not bind-mounting your config.cfg into this container."
  echo "algo needs a configuration file to run."
  echo ""
  usage -1
fi

if [ ! -e /dev/console ]; then
  echo "Looks like you're trying to run this container without a TTY."
  echo "If you don't pass -t, you can't interact with the algo script."
  echo ""
  usage -1
fi

for directory in "${DATA_DIR}" "${DATA_DIR}/configs"; do
  if [[ -d "${directory}" && ! -w "${directory}" ]]; then
    echo "Cannot write generated configurations to ${directory}." >&2
    echo "Grant container UID $(id -u) write access to the host directory before deploying." >&2
    echo "See docs/deploy-from-docker.md for Linux bind-mount permissions." >&2
    exit 1
  fi
done

# To work around problems with bind-mounting Windows volumes, we need to
# copy files out of ${DATA_DIR}, ensure appropriate line endings and permissions,
# then copy the algo-generated files into ${DATA_DIR}.

tr -d '\r' <"${DATA_DIR}"/config.cfg >"${ALGO_DIR}"/config.cfg
# Keep deployment symlinks relative. A small alias file also works on bind
# mounts that cannot create symlinks. Never traverse a link into another tree.
alias_file="${DATA_DIR}/.algo-localhost"
validate_alias() {
  local configs=$1 target=$2
  if [[ ! $target =~ ^[A-Za-z0-9_:.-]+$ || $target == . || $target == .. || $target == localhost ||
        -L "$configs/$target" || ! -d "$configs/$target" ]]; then
    echo "Invalid localhost alias in $configs. Select an existing sibling deployment." >&2
    return 1
  fi
}

if [[ -L ${DATA_DIR}/configs || -L $alias_file ]]; then
  echo "The host configs directory and alias record must reside on the mounted volume." >&2
  exit 1
fi

if [[ -d ${DATA_DIR}/configs ]]; then
  source_configs="${DATA_DIR}/configs"
  source_root=$(realpath "$source_configs")
  while IFS= read -r -d '' link; do
    if [[ $(readlink "$link") = /* ]] || ! resolved=$(realpath "$link") || [[ $resolved != "$source_root/"* ]]; then
      echo "Config symlink $link must point to an existing entry inside the deployment store." >&2
      exit 1
    fi
  done < <(find "$source_configs" -type l -print0)
  target=""
  if [[ -L $source_configs/localhost ]]; then
    target=$(readlink "$source_configs/localhost")
  elif [[ -f $alias_file && ! -L $alias_file ]]; then
    IFS= read -r target < "$alias_file" || [[ -n $target ]]
    validate_alias "$source_configs" "$target"
    if [[ -e $source_configs/localhost ]]; then
      echo "Both a localhost directory and an alias exist in $source_configs. Reconcile them before continuing." >&2
      exit 1
    fi
  elif [[ -f $source_configs/localhost/.config.yml ]]; then
    for config in "$source_configs"/*/.config.yml; do
      if [[ -f $config && $config != "$source_configs/localhost/.config.yml" ]]; then
        echo "Duplicate localhost deployment in $source_configs. Compare the directories and replace the duplicate with a relative symlink." >&2
        exit 1
      fi
    done
  fi
  if [[ -n $target ]]; then validate_alias "$source_configs" "$target"; fi
  rsync -qrlt --safe-links --delete "$source_configs/" "${ALGO_DIR}/configs/"
  if [[ -n $target && ! -L ${ALGO_DIR}/configs/localhost ]]; then
    ln -s "$target" "${ALGO_DIR}/configs/localhost"
  fi
fi

retcode=0
if [[ -n "${ALGO_ARGS:-}" ]]; then
  "${ALGO_DIR}"/algo "$ALGO_ARGS" || retcode=$?
else
  "${ALGO_DIR}"/algo || retcode=$?
fi

if [[ -L ${ALGO_DIR}/configs/localhost ]]; then
  target=$(readlink "${ALGO_DIR}/configs/localhost")
  validate_alias "${ALGO_DIR}/configs" "$target"
  if [[ -e ${DATA_DIR}/configs/localhost && ! -L ${DATA_DIR}/configs/localhost ]]; then
    echo "A physical localhost deployment occupies the alias path in ${DATA_DIR}/configs." >&2
    exit 1
  fi
  rsync -qrlt --safe-links --delete --exclude=/localhost "${ALGO_DIR}/configs/" "${DATA_DIR}/configs/"
  # Write the alias atomically, including on Windows filesystems.
  alias_tmp=$(mktemp "${DATA_DIR}/.algo-localhost.XXXXXX")
  printf '%s\n' "$target" > "$alias_tmp"
  mv -f "$alias_tmp" "$alias_file"
  if [[ -L ${DATA_DIR}/configs/localhost && $(readlink "${DATA_DIR}/configs/localhost") != "$target" ]]; then
    unlink "${DATA_DIR}/configs/localhost"
  fi
  if [[ ! -L ${DATA_DIR}/configs/localhost ]]; then
    ln -s "$target" "${DATA_DIR}/configs/localhost" 2>/dev/null || [[ -f $alias_file ]]
  fi
else
  rsync -qrlt --safe-links --delete "${ALGO_DIR}/configs/" "${DATA_DIR}/configs/"
  if [[ -f $alias_file || -L $alias_file ]]; then unlink "$alias_file"; fi
fi
exit "${retcode}"
