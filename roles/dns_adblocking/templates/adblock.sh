#!/bin/sh
# Block ads, malware, etc..

# Redirect endpoint
ENDPOINT_IP4="0.0.0.0"
ENDPOINT_IP6="::"
IPV6="Y"
TEMP=`mktemp`
TEMP_SORTED=`mktemp`

#Delete the old block.hosts to make room for the updates
rm -f /var/lib/dnsmasq/block.hosts

echo 'Downloading hosts lists...'
#Download and process the files needed to make the lists (enable/add more, if you want)
wget -qO- http://winhelp2002.mvps.org/hosts.txt| awk -v r="$ENDPOINT_IP4" '{sub(/^0.0.0.0/, r)} $0 ~ "^"r' > "$TEMP"
wget -qO- "https://adaway.org/hosts.txt"|awk -v r="$ENDPOINT_IP4" '{sub(/^127.0.0.1/, r)} $0 ~ "^"r' >> "$TEMP"
wget -qO- https://www.malwaredomainlist.com/hostslist/hosts.txt|awk -v r="$ENDPOINT_IP4" '{sub(/^127.0.0.1/, r)} $0 ~ "^"r' >> "$TEMP"
wget -qO- "https://hosts-file.net/.\ad_servers.txt"|awk -v r="$ENDPOINT_IP4" '{sub(/^127.0.0.1/, r)} $0 ~ "^"r' >> "$TEMP"

#Add black list, if non-empty
if [ -s "/var/lib/dnsmasq/black.list" ]
then
    echo 'Adding blacklist...'
    awk -v r="$ENDPOINT_IP4" '/^[^#]/ { print r,$1 }' /var/lib/dnsmasq/black.list >> "$TEMP"
fi

#Sort the download/black lists
awk '{sub(/\r$/,"");print $1,$2}' "$TEMP"|sort -u > "$TEMP_SORTED"

#Filter (if applicable)
if [ -s "/var/lib/dnsmasq/white.list" ]
then
    #Filter the blacklist, suppressing whitelist matches
    #  This is relatively slow =-(
    echo 'Filtering white list...'
    egrep -v "^[[:space:]]*$" /var/lib/dnsmasq/white.list | awk '/^[^#]/ {sub(/\r$/,"");print $1}' | grep -vf - "$TEMP_SORTED" > /var/lib/dnsmasq/block.hosts
else
    cat "$TEMP_SORTED" > /var/lib/dnsmasq/block.hosts
fi

if [ "$IPV6" = "Y" ]
then
    safe_pattern=$(printf '%s\n' "$ENDPOINT_IP4" | sed 's/[[\.*^$(){}?+|/]/\\&/g')
    safe_addition=$(printf '%s\n' "$ENDPOINT_IP6" | sed 's/[\&/]/\\&/g')
    echo 'Adding ipv6 support...'
    sed -i -re "s/^(${safe_pattern}) (.*)$/\1 \2\n${safe_addition} \2/g" /var/lib/dnsmasq/block.hosts
fi

service dnsmasq restart

exit 0
