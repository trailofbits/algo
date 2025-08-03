#!/bin/bash
# Mock service command that delegates to mock systemctl

# The service command has syntax: service <name> <action>
# We need to convert it to: systemctl <action> <name>

if [[ $# -lt 2 ]]; then
    echo "Usage: service <name> <action>" >&2
    exit 1
fi

SERVICE_NAME=$1
ACTION=$2

# Map service actions to systemctl
case "$ACTION" in
    start|stop|restart|reload|status)
        exec /usr/bin/systemctl "$ACTION" "$SERVICE_NAME"
        ;;
    enable|disable)
        exec /usr/bin/systemctl "$ACTION" "$SERVICE_NAME"
        ;;
    *)
        echo "Unknown action: $ACTION" >&2
        exit 1
        ;;
esac