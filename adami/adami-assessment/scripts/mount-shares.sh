#!/bin/bash
# Mount Adami corporate shares — run as root
# Usage: sudo ./mount-shares.sh

[ "$EUID" -ne 0 ] && echo "Run as root: sudo $0" && exit 1

mkdir -p /mnt/adami/{dati,lenovo-nas,synology,fileserver-6}

echo "Mounting DATI share (.30)..."
mount.cifs //192.168.1.30/DATI /mnt/adami/dati -o guest,ro,vers=3.0 2>/dev/null && echo "  OK" || echo "  FAILED (try: -o sec=ntlm)"

echo "Mounting Synology NAS (.8)..."
echo "  Requires auth — use: mount.cifs //192.168.1.8/<share> /mnt/adami/synology -o username=USER,password=PASS"

echo "Mounting file server (.6.1)..."
mount.cifs //192.168.6.1/ /mnt/adami/fileserver-6 -o username=adminada,password='Q-2!?H.)S5_t8$Y',ro 2>/dev/null && echo "  OK" || echo "  FAILED (needs VPN or specific VLAN)"

echo ""
echo "Lenovo NAS (.6) shares require auth. Available shares:"
smbclient -L //192.168.1.6/ -N 2>/dev/null | grep Disk | awk '{print "  "$1}'

echo ""
echo "To browse any share interactively:"
echo "  smbclient //IP/SHARE -U username"
