#!/bin/bash
# Adami Trasporti VPN — Full Tunnel (ALL traffic through VPN)
# WARNING: This will redirect ALL internet traffic through the VPN
# Your current SSH/Claude session WILL drop!
DIR="$(cd "$(dirname "$0")" && pwd)"
[ "$EUID" -ne 0 ] && echo "Run as root: sudo $0" && exit 1
openvpn --config "$DIR/../../../Desktop/anexos/pfSense-UDP4-1194-francescav.ovpn" --providers legacy default
