#!/bin/bash
#
# Pulse ERP - Raspberry Pi 5 Setup Script
# Automates provisioning steps from PI_PROVISIONING.md
#
# Usage: ./scripts/setup-pi.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Pulse ERP - Pi 5 Setup Script      ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo -e "${YELLOW}⚠ Warning: This doesn't appear to be a Raspberry Pi${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}Step 1: Updating system...${NC}"
sudo apt update && sudo apt upgrade -y

echo -e "${GREEN}Step 2: Installing essential packages...${NC}"
sudo apt install -y \
    git \
    curl \
    wget \
    vim \
    htop \
    iotop \
    nmap \
    net-tools \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    zram-tools

echo -e "${GREEN}Step 3: Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh

    # Add current user to docker group
    sudo usermod -aG docker $USER
    echo -e "${YELLOW}⚠ You'll need to logout and login again for docker group changes to take effect${NC}"
else
    echo -e "${YELLOW}Docker already installed${NC}"
fi

echo -e "${GREEN}Step 4: Installing Docker Compose plugin...${NC}"
if ! docker compose version &> /dev/null; then
    sudo apt install -y docker-compose-plugin
else
    echo -e "${YELLOW}Docker Compose already installed${NC}"
fi

echo -e "${GREEN}Step 5: Configuring zram...${NC}"
if [ -f /etc/default/zramswap ]; then
    sudo sed -i 's/#ALGO=lz4/ALGO=lz4/' /etc/default/zramswap
    sudo sed -i 's/#PERCENT=50/PERCENT=50/' /etc/default/zramswap
    sudo systemctl restart zramswap
    echo -e "${GREEN}✓ zram configured${NC}"
else
    echo -e "${YELLOW}⚠ zramswap config not found, skipping${NC}"
fi

echo -e "${GREEN}Step 6: Setting up external SSD...${NC}"
# Check if SSD is already mounted
if mountpoint -q /mnt/ssd; then
    echo -e "${YELLOW}SSD already mounted at /mnt/ssd${NC}"
else
    # Try to detect SSD
    if [ -b /dev/sda1 ]; then
        echo -e "${YELLOW}Found /dev/sda1. Setting up mount point...${NC}"
        sudo mkdir -p /mnt/ssd

        # Get UUID
        UUID=$(sudo blkid -s UUID -o value /dev/sda1)

        # Check if already in fstab
        if ! grep -q "/mnt/ssd" /etc/fstab; then
            echo "UUID=$UUID /mnt/ssd ext4 defaults,noatime 0 2" | sudo tee -a /etc/fstab
            sudo mount -a
            echo -e "${GREEN}✓ SSD mounted at /mnt/ssd${NC}"
        else
            echo -e "${YELLOW}SSD already configured in fstab${NC}"
            sudo mount -a
        fi

        # Set ownership
        sudo chown -R $USER:$USER /mnt/ssd
    else
        echo -e "${RED}✗ No SSD detected at /dev/sda1${NC}"
        echo -e "${YELLOW}⚠ Please connect SSD and run: sudo mkfs.ext4 /dev/sda1${NC}"
        echo -e "${YELLOW}⚠ Then re-run this script${NC}"
    fi
fi

echo -e "${GREEN}Step 7: Creating data directories on SSD...${NC}"
if [ -d /mnt/ssd ]; then
    mkdir -p /mnt/ssd/{postgres,nats,minio,olap,grafana,prometheus,backups}
    chmod -R 755 /mnt/ssd
    echo -e "${GREEN}✓ Data directories created${NC}"
else
    echo -e "${YELLOW}⚠ SSD not mounted, creating directories in home${NC}"
    mkdir -p ~/pulse-erp-data/{postgres,nats,minio,olap,grafana,prometheus,backups}
fi

echo -e "${GREEN}Step 8: Configuring system parameters...${NC}"

# File descriptor limits
if ! grep -q "nofile 65536" /etc/security/limits.conf; then
    echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
    echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
fi

# Kernel parameters
if ! grep -q "net.core.somaxconn" /etc/sysctl.conf; then
    cat << 'EOF' | sudo tee -a /etc/sysctl.conf

# Pulse ERP optimizations
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 4096
vm.swappiness = 10
vm.overcommit_memory = 1
EOF
    sudo sysctl -p
fi

echo -e "${GREEN}Step 9: Disabling unnecessary services...${NC}"
sudo systemctl disable bluetooth || true
sudo systemctl stop bluetooth || true

echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Setup Complete!                     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ System updated${NC}"
echo -e "${GREEN}✓ Docker installed${NC}"
echo -e "${GREEN}✓ Docker Compose installed${NC}"
echo -e "${GREEN}✓ zram configured${NC}"
echo -e "${GREEN}✓ Data directories created${NC}"
echo -e "${GREEN}✓ System optimized${NC}"
echo ""
echo -e "${YELLOW}⚠ IMPORTANT: You need to logout and login again for docker group changes to take effect${NC}"
echo ""
echo "Next steps:"
echo "1. Logout: exit"
echo "2. SSH back in"
echo "3. Verify Docker: docker run hello-world"
echo "4. Start infrastructure: docker compose -f docker-compose.base.yml up -d"
echo ""
echo "For more details, see docs/PI_PROVISIONING.md"
