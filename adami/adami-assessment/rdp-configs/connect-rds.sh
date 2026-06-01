#!/bin/bash
echo "Connecting to RDS-SCB.ADAMITRASPORTI.LOCAL (192.168.60.8)..."
echo "Domain credentials required (adamitrasporti\username)"
xfreerdp /v:192.168.60.8 /u:adamitrasporti\\$1 /dynamic-resolution /cert:ignore 2>/dev/null || rdesktop 192.168.60.8 2>/dev/null || echo "Install: sudo apt install freerdp2-x11"
