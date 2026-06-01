#!/bin/bash
# Adami Trasporti — Security Assessment Access Toolkit
# Run on LAN (192.168.1.x) or via VPN tunnel
# Author: macena IT Security — 2026-05-28

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
echo -e "${RED}  ADAMI TRASPORTI — Security Assessment Access Toolkit    ${NC}"
echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
echo ""

check_reach() {
  timeout 2 bash -c "echo > /dev/tcp/$1/$2" 2>/dev/null && echo -e "${GREEN}[REACHABLE]${NC} $1:$2" || echo -e "${RED}[BLOCKED]${NC} $1:$2"
}

echo -e "${YELLOW}[1] Network Position${NC}"
LAN_IP=$(ip -4 addr show | grep "192.168.1\." | awk '{print $2}' | head -1)
WIFI_IP=$(ip -4 addr show | grep "192.168.192\." | awk '{print $2}' | head -1)
VPN_IP=$(ip -4 addr show tun0 2>/dev/null | grep inet | awk '{print $2}' | head -1)
[ -n "$LAN_IP" ] && echo -e "  LAN: ${GREEN}$LAN_IP${NC}"
[ -n "$WIFI_IP" ] && echo -e "  WiFi: ${YELLOW}$WIFI_IP${NC} (guest)"
[ -n "$VPN_IP" ] && echo -e "  VPN: ${GREEN}$VPN_IP${NC}"
[ -z "$LAN_IP" ] && [ -z "$VPN_IP" ] && echo -e "  ${RED}NOT on corporate network. Connect LAN or VPN first.${NC}" && exit 1
echo ""

echo -e "${YELLOW}[2] Reachability Check${NC}"
check_reach 192.168.60.2 389    # DC01 LDAP
check_reach 192.168.1.6 445     # Lenovo NAS
check_reach 192.168.1.30 445    # ASUS DATI
check_reach 192.168.1.8 5001    # Synology
check_reach 192.168.1.160 80    # AXIS camera
check_reach 192.168.1.156 80    # NUUO NVR
check_reach 192.168.1.151 21    # Omron PLC
check_reach 192.168.6.1 445     # File server .6.1
echo ""

echo -e "${YELLOW}[3] Quick Actions${NC}"
echo "  a) Mount Lenovo NAS shares   → sudo mount.cifs //192.168.1.6/ITfolder /mnt/it -o guest,ro"
echo "  b) Browse DATI share         → smbclient //192.168.1.30/DATI -N"
echo "  c) List Lenovo NAS shares    → smbclient -L //192.168.1.6/ -N"
echo "  d) Open Synology DSM         → xdg-open https://192.168.1.8:5001/"
echo "  e) Open AXIS camera          → xdg-open http://192.168.1.160/"
echo "  f) Open NUUO NVR             → xdg-open http://192.168.1.156/"
echo "  g) Open Netgear switch       → xdg-open http://192.168.1.25/"
echo "  h) Access .6.1 file server   → smbclient //192.168.6.1/ -U adminada"
echo "  i) Full nmap rescan          → sudo nmap -sS -sV -n --top-ports 200 --open 192.168.1.0/24"
echo ""

read -p "Choose action (a-i) or q to quit: " choice
case $choice in
  a) sudo mkdir -p /mnt/it && sudo mount.cifs //192.168.1.6/ITfolder /mnt/it -o guest,ro && ls /mnt/it/ ;;
  b) smbclient //192.168.1.30/DATI -N ;;
  c) smbclient -L //192.168.1.6/ -N ;;
  d) xdg-open https://192.168.1.8:5001/ ;;
  e) xdg-open http://192.168.1.160/ ;;
  f) xdg-open http://192.168.1.156/ ;;
  g) xdg-open http://192.168.1.25/ ;;
  h) smbclient //192.168.6.1/ -U adminada ;;
  i) sudo nmap -sS -sV -n --top-ports 200 --open 192.168.1.0/24 ;;
  q) exit 0 ;;
  *) echo "Invalid choice" ;;
esac
