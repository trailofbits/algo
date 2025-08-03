#!/bin/bash
# Enhanced mock systemctl for Docker containers
# Tracks service state and provides realistic responses

STATE_DIR=/var/lib/fake-systemd
LOG_FILE=/var/log/fake-systemd.log
mkdir -p "$STATE_DIR" "$(dirname "$LOG_FILE")"

# Log all operations
echo "[$(date)] systemctl $*" >> "$LOG_FILE"

# Helper functions
is_service_active() {
    local service=$1
    [[ -f "$STATE_DIR/$service.active" ]]
}

is_service_enabled() {
    local service=$1
    [[ -f "$STATE_DIR/$service.enabled" ]]
}

set_service_active() {
    local service=$1
    touch "$STATE_DIR/$service.active"
    echo "[$(date)] Service $service marked as active" >> "$LOG_FILE"
}

set_service_inactive() {
    local service=$1
    rm -f "$STATE_DIR/$service.active"
    echo "[$(date)] Service $service marked as inactive" >> "$LOG_FILE"
}

set_service_enabled() {
    local service=$1
    touch "$STATE_DIR/$service.enabled"
    echo "[$(date)] Service $service marked as enabled" >> "$LOG_FILE"
}

set_service_disabled() {
    local service=$1
    rm -f "$STATE_DIR/$service.enabled"
    echo "[$(date)] Service $service marked as disabled" >> "$LOG_FILE"
}

# Parse systemctl commands
case "$1" in
    start)
        shift
        for service in "$@"; do
            echo "Starting $service..."
            set_service_active "$service"
        done
        ;;
    
    stop)
        shift
        for service in "$@"; do
            echo "Stopping $service..."
            set_service_inactive "$service"
        done
        ;;
    
    restart|reload)
        shift
        for service in "$@"; do
            echo "Restarting $service..."
            set_service_inactive "$service"
            sleep 0.1
            set_service_active "$service"
        done
        ;;
    
    enable)
        shift
        # Handle --now flag
        if [[ "$1" == "--now" ]]; then
            shift
            for service in "$@"; do
                echo "Enabling and starting $service..."
                set_service_enabled "$service"
                set_service_active "$service"
            done
        else
            for service in "$@"; do
                echo "Enabling $service..."
                set_service_enabled "$service"
            done
        fi
        ;;
    
    disable)
        shift
        # Handle --now flag
        if [[ "$1" == "--now" ]]; then
            shift
            for service in "$@"; do
                echo "Disabling and stopping $service..."
                set_service_disabled "$service"
                set_service_inactive "$service"
            done
        else
            for service in "$@"; do
                echo "Disabling $service..."
                set_service_disabled "$service"
            done
        fi
        ;;
    
    is-active)
        shift
        if is_service_active "$1"; then
            echo "active"
            exit 0
        else
            echo "inactive"
            exit 3
        fi
        ;;
    
    is-enabled)
        shift
        if is_service_enabled "$1"; then
            echo "enabled"
            exit 0
        else
            echo "disabled" 
            exit 1
        fi
        ;;
    
    status)
        shift
        service=$1
        if is_service_active "$service"; then
            echo "● $service - Mock Service"
            echo "   Loaded: loaded (/etc/systemd/system/$service.service; $(is_service_enabled "$service" && echo "enabled" || echo "disabled"))"
            echo "   Active: active (running)"
            echo "   Process: 1234 ExecStart=/bin/true (code=exited, status=0/SUCCESS)"
            echo "   Main PID: 1234 (mock)"
        else
            echo "● $service - Mock Service"
            echo "   Loaded: loaded (/etc/systemd/system/$service.service; $(is_service_enabled "$service" && echo "enabled" || echo "disabled"))"
            echo "   Active: inactive (dead)"
        fi
        ;;
    
    daemon-reload)
        echo "Reloading systemd manager configuration..."
        sleep 0.1
        echo "done"
        ;;
    
    list-units)
        echo "UNIT                         LOAD   ACTIVE SUB     DESCRIPTION"
        for state_file in "$STATE_DIR"/*.active; do
            if [[ -f "$state_file" ]]; then
                service=$(basename "$state_file" .active)
                printf "%-28s loaded active running Mock %s Service\n" "$service" "$service"
            fi
        done
        ;;
    
    --version)
        echo "systemd 249 (mock)"
        echo "Mock systemd for Docker containers"
        ;;
    
    # Handle combined operations like: systemctl --system --preset-mode=enable-only preset service.service
    --system)
        shift
        if [[ "$1" == "--preset-mode=enable-only" ]] && [[ "$2" == "preset" ]]; then
            shift 2
            for service in "$@"; do
                echo "Preset operation for $service (mock - no action taken)"
            done
        else
            # Pass through to regular processing
            "$0" "$@"
        fi
        ;;
    
    *)
        echo "Mock systemctl: operation '$1' recorded but not implemented" >&2
        echo "[$(date)] Unhandled operation: $*" >> "$LOG_FILE"
        # Return success to not break provisioning
        exit 0
        ;;
esac

exit 0