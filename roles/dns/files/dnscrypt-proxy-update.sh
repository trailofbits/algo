#! /bin/sh

INSTALL_DIR="/opt/dnscrypt-proxy"
LATEST_URL="https://api.github.com/repos/jedisct1/dnscrypt-proxy/releases/latest"

Update() {
    workdir="$(mktemp -d)"
    curl -sL $(curl -sL "$LATEST_URL" |
        grep dnscrypt-proxy-linux_x86_64- | grep browser_download_url | head -1 | cut -d \" -f 4) |
        tar xz -C "$workdir" -f - linux-x86_64/dnscrypt-proxy &&
        [ -x linux-x86_64/dnscrypt-proxy ] &&
        mv -f "${INSTALL_DIR}/dnscrypt-proxy" "${INSTALL_DIR}/dnscrypt-proxy.old" || : &&
        mv -f "${workdir}/linux-x86_64/dnscrypt-proxy" "${INSTALL_DIR}/" &&
        cd "$INSTALL_DIR" && rm -fr "$workdir" &&
        ./dnscrypt-proxy -check && ./dnscrypt-proxy -service install 2>/dev/null || : &&
        ./dnscrypt-proxy -service restart || ./dnscrypt-proxy -service start
}

lversion=$("${INSTALL_DIR}/dnscrypt-proxy" -version)
rmersion=$(curl -sL "$LATEST_URL" | grep "tag_name" | head -1 | cut -d \" -f 4)
[ -z "$lversion" ] && exit 1
[ -z "$rmersion" ] && exit 1

echo locally installed
echo "$lversion"

echo remote git version
echo "$rmersion"

if [ "$rmersion" != "$lversion" ]; then
    echo "Updating" && Update
else
    echo "No Update Needed"
fi
