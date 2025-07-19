#!/bin/sh

# PROVIDE: wireguard
# REQUIRE: LOGIN
# BEFORE:  securelevel
# KEYWORD: shutdown

. /etc/rc.subr

name="wg"
# shellcheck disable=SC2034
rcvar=wg_enable

command="/usr/local/bin/wg-quick"
# shellcheck disable=SC2034
start_cmd=wg_up
# shellcheck disable=SC2034
stop_cmd=wg_down
# shellcheck disable=SC2034
status_cmd=wg_status
pidfile="/var/run/$name.pid"
load_rc_config "$name"

: ${wg_enable="NO"}
: ${wg_interface="wg0"}

wg_up() {
  echo "Starting WireGuard..."
  /usr/sbin/daemon -cS -p ${pidfile} ${command} up ${wg_interface}
}

wg_down() {
  echo "Stopping WireGuard..."
  ${command} down ${wg_interface}
}

wg_status () {
  not_running () {
    echo "WireGuard is not running on $wg_interface" && exit 1
  }
  /usr/local/bin/wg show wg0 && echo "WireGuard is running on $wg_interface" || not_running
}

run_rc_command "$1"
