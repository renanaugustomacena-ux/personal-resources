#!/bin/bash
# Adami Trasporti VPN — Split Tunnel (keeps internet on local interface)
# Usage: sudo ./connect-adami-vpn.sh
# You'll be prompted for VPN username and password

DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$EUID" -ne 0 ]; then
  echo "Run as root: sudo $0"
  exit 1
fi

echo "Connecting to Adami Trasporti VPN (split tunnel)..."
echo "VPN endpoint: 45.151.15.58:1194/UDP"
echo "You will be prompted for VPN username and password."
echo ""

openvpn \
  --client \
  --dev tun \
  --proto udp4 \
  --remote 45.151.15.58 1194 \
  --resolv-retry infinite \
  --persist-tun \
  --persist-key \
  --cipher AES-128-CBC \
  --data-ciphers AES-128-GCM \
  --auth SHA256 \
  --tls-client \
  --remote-cert-tls server \
  --auth-user-pass \
  --pkcs12 "$DIR/pfSense-UDP4-1194-francescav.p12" \
  --tls-auth "$DIR/pfSense-UDP4-1194-francescav-tls.key" 1 \
  --providers legacy default \
  --route 192.168.1.0 255.255.255.0 \
  --route 192.168.6.0 255.255.255.0 \
  --route 192.168.60.0 255.255.255.0 \
  --route 192.168.192.0 255.255.255.0 \
  --verb 3
