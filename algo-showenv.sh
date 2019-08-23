#!/usr/bin/env bash
#
# Print information about Algo's invocation environment to aid in debugging.
# This is normally called from Ansible right before a deployment gets underway.

# Skip printing this header if we're just testing with no arguments.
if [[ $# -gt 0 ]]; then
    echo ""
    echo "--> Please include the following block of text when reporting issues:"
    echo ""
fi

if [[ ! -f ./algo ]]; then
    echo "This should be run from the top level Algo directory"
fi

# Determine the operating system.
case "$(uname -s)" in
    Linux)
        OS="Linux ($(uname -r) $(uname -v))"
        if [[ -f /etc/os-release ]]; then
            # shellcheck disable=SC1091
            # I hope this isn't dangerous.
            . /etc/os-release
            if [[ ${PRETTY_NAME} ]]; then
                OS="${PRETTY_NAME}"
            elif [[ ${NAME} ]]; then
                OS="${NAME} ${VERSION}"
            fi
        fi
        STAT="stat -c %y"
        ;;
    Darwin)
        OS="$(sw_vers -productName) $(sw_vers -productVersion)"
        STAT="stat -f %Sm"
        ;;
    *)
        OS="Unknown"
        ;;
esac

# Determine if virtualization is being used with Linux.
VIRTUALIZED=""
if [[ -x $(command -v systemd-detect-virt) ]]; then
    DETECT_VIRT="$(systemd-detect-virt)"
    if [[ ${DETECT_VIRT} != "none" ]]; then
        VIRTUALIZED=" (Virtualized: ${DETECT_VIRT})"
    fi
elif [[ -f /.dockerenv ]]; then
    VIRTUALIZED=" (Virtualized: docker)"
fi

echo "Algo running on: ${OS}${VIRTUALIZED}"

# Determine the currentness of the Algo software.
if [[ -d .git && -x $(command -v git) ]]; then
    ORIGIN="$(git remote get-url origin)"
    COMMIT="$(git log --max-count=1 --oneline --no-decorate --no-color)"
    if [[ ${ORIGIN} == "https://github.com/trailofbits/algo.git" ]]; then
        SOURCE="clone"
    else
        SOURCE="fork"
    fi
    echo "Created from git ${SOURCE}. Last commit: ${COMMIT}"
elif [[ -f LICENSE && ${STAT} ]]; then
    CREATED="$(${STAT} LICENSE)"
    echo "ZIP file created: ${CREATED}"
fi

# The Python version might be useful to know.
if [[ -x ./.env/bin/python3 ]]; then
    ./.env/bin/python3 --version 2>&1
elif [[ -f ./algo ]]; then
    echo ".env/bin/python3 not found: has 'python3 -m virtualenv ...' been run?"
fi

# Just print out all command line arguments, which are expected
# to be Ansible variables.
if [[ $# -gt 0 ]]; then
    echo "Runtime variables:"
    for VALUE in "$@"; do
        echo "    ${VALUE}"
    done
fi

exit 0
