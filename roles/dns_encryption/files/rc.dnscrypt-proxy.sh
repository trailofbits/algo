#!/bin/sh

# PROVIDE: dnscrypt-proxy
# REQUIRE: LOGIN
# BEFORE:  securelevel
# KEYWORD: shutdown

# Add the following lines to /etc/rc.conf to enable `dnscrypt-proxy':
#
# dnscrypt_proxy_enable="YES"
# dnscrypt_proxy_flags="<set as needed>"
#
# See rsync(1) for rsyncd_flags
#

. /etc/rc.subr

name="dnscrypt-proxy"
rcvar=dnscrypt_proxy_enable
load_rc_config "$name"
pidfile="/var/run/$name.pid"
start_cmd=dnscrypt_proxy_start
stop_postcmd=dnscrypt_proxy_stop

: ${dnscrypt_proxy_enable="NO"}
: ${dnscrypt_proxy_flags="-config /usr/local/etc/dnscrypt-proxy/dnscrypt-proxy.toml"}

dnscrypt_proxy_start() {
  echo "Starting dnscrypt-proxy..."
  touch ${pidfile}
  /usr/sbin/daemon -cS -T dnscrypt-proxy -p ${pidfile} /usr/dnscrypt-proxy/freebsd-amd64/dnscrypt-proxy ${dnscrypt_proxy_flags}
}

dnscrypt_proxy_stop() {
  [ -f ${pidfile} ] && rm ${pidfile}
}

run_rc_command "$1"
