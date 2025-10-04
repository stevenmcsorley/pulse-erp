# Raspberry Pi 5 Provisioning Guide

**Card:** C01 - Provision Pi 5 + OS + Docker Setup
**Estimate:** 3 story points
**Priority:** P0 - Critical

This document provides step-by-step instructions for provisioning a Raspberry Pi 5 for the Pulse ERP demo environment.

## Prerequisites

- Raspberry Pi 5 (8GB RAM recommended, 4GB minimum)
- MicroSD card (32GB minimum, Class 10 or better)
- External SSD (250GB+ recommended for production data)
- Power supply (official Pi 5 27W USB-C adapter)
- Ethernet cable (recommended) or WiFi
- Monitor, keyboard (for initial setup)

## Step 1: Install Raspberry Pi OS

### Option A: Using Raspberry Pi Imager (Recommended)

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Insert microSD card into your computer
3. Launch Raspberry Pi Imager
4. Click **"Choose OS"** → **"Raspberry Pi OS (64-bit)"** → **"Raspberry Pi OS Lite (64-bit)"** for headless, or full OS if you want desktop
5. Click **"Choose Storage"** → Select your microSD card
6. Click **Settings icon** (⚙️) to configure:
   - ✅ Enable SSH
   - ✅ Set username: `pi` (or your preference)
   - ✅ Set password
   - ✅ Configure WiFi (if needed)
   - ✅ Set hostname: `pulse-erp` (or your preference)
7. Click **"Write"** and wait for completion

### Option B: Manual Installation

1. Download [Raspberry Pi OS (64-bit)](https://www.raspberrypi.com/software/operating-systems/)
2. Flash to microSD using `dd` or [balenaEtcher](https://www.balena.io/etcher/)
3. Enable SSH by creating empty `ssh` file in boot partition

## Step 2: Initial Boot and Configuration

### Boot the Pi

1. Insert microSD card into Pi 5
2. Connect Ethernet cable (or ensure WiFi is configured)
3. Connect power supply
4. Wait ~60 seconds for first boot

### SSH Connection

```bash
# Find Pi IP address (check your router, or use nmap)
nmap -sn 192.168.1.0/24 | grep -i raspberry

# SSH into Pi
ssh pi@<PI_IP_ADDRESS>
# or
ssh pi@pulse-erp.local
```

### Initial System Update

```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

## Step 3: Configure External SSD

### Format and Mount SSD

```bash
# Identify SSD device (usually /dev/sda)
lsblk

# Create partition (if new SSD)
sudo fdisk /dev/sda
# Type: n (new partition), p (primary), 1, Enter, Enter, w (write)

# Format as ext4
sudo mkfs.ext4 /dev/sda1

# Create mount point
sudo mkdir -p /mnt/ssd

# Get UUID of partition
sudo blkid /dev/sda1
# Note the UUID value

# Add to /etc/fstab for automatic mount
echo "UUID=<YOUR_UUID> /mnt/ssd ext4 defaults,noatime 0 2" | sudo tee -a /etc/fstab

# Mount the SSD
sudo mount -a

# Verify mount
df -h | grep ssd

# Set ownership
sudo chown -R $USER:$USER /mnt/ssd
```

**Example fstab entry:**
```
UUID=12345678-1234-1234-1234-123456789abc /mnt/ssd ext4 defaults,noatime 0 2
```

## Step 4: Install Docker and Docker Compose

### Install Docker

```bash
# Install Docker using convenience script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group
sudo usermod -aG docker $USER

# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Logout and login again for group changes to take effect
exit
# SSH back in
ssh pi@<PI_IP>

# Verify Docker installation
docker --version
docker run hello-world
```

### Install Docker Compose Plugin

```bash
# Install Docker Compose plugin
sudo apt install -y docker-compose-plugin

# Verify installation
docker compose version
```

## Step 5: Configure zram for Swap Optimization

zram creates a compressed swap area in RAM, improving performance on Pi 5.

```bash
# Install zram-tools
sudo apt install -y zram-tools

# Configure zram (edit /etc/default/zramswap)
sudo nano /etc/default/zramswap

# Set these values:
# ALGO=lz4
# PERCENT=50

# Restart zram service
sudo systemctl restart zramswap

# Verify zram is active
sudo swapon --show
```

## Step 6: System Optimizations for ERP Workload

### Increase File Descriptor Limits

```bash
# Edit limits.conf
sudo nano /etc/security/limits.conf

# Add these lines:
* soft nofile 65536
* hard nofile 65536
```

### Configure Kernel Parameters

```bash
# Edit sysctl.conf
sudo nano /etc/sysctl.conf

# Add these lines for better networking and memory management:
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 4096
vm.swappiness = 10
vm.overcommit_memory = 1
```

Apply changes:
```bash
sudo sysctl -p
```

### Disable Unnecessary Services

```bash
# Disable Bluetooth if not needed
sudo systemctl disable bluetooth
sudo systemctl stop bluetooth

# Disable WiFi if using Ethernet
sudo rfkill block wifi
```

## Step 7: Install Additional Dependencies

```bash
# Install essential tools
sudo apt install -y \
    git \
    curl \
    wget \
    vim \
    htop \
    iotop \
    nmap \
    net-tools \
    build-essential

# Install Python (for utility scripts)
sudo apt install -y python3 python3-pip python3-venv
```

## Step 8: Configure Firewall (Optional but Recommended)

```bash
# Install UFW
sudo apt install -y ufw

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS (for Traefik)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

## Step 9: Set Up Project Directory

```bash
# Create project directory
mkdir -p ~/pulse-erp
cd ~/pulse-erp

# Clone repository (when GitHub is configured)
git clone https://github.com/stevenmcsorley/pulse-erp.git .

# Or manually copy files if pushing from development machine
```

## Step 10: Verification Checklist

Run these commands to verify your setup:

```bash
# Check Docker
docker --version
docker compose version
docker ps

# Check SSD mount
df -h | grep /mnt/ssd
ls -la /mnt/ssd

# Check system resources
free -h
lscpu | grep -i "model name\|cpu(s)\|architecture"

# Check zram
swapon --show

# Check network
ip addr show
ping -c 3 8.8.8.8

# Check disk I/O performance
sudo hdparm -Tt /dev/sda1
```

## Step 11: Create Data Directories on SSD

```bash
# Create directories for persistent data
mkdir -p /mnt/ssd/postgres
mkdir -p /mnt/ssd/nats
mkdir -p /mnt/ssd/minio
mkdir -p /mnt/ssd/olap
mkdir -p /mnt/ssd/grafana
mkdir -p /mnt/ssd/prometheus
mkdir -p /mnt/ssd/backups

# Set permissions
chmod -R 755 /mnt/ssd
```

## Expected Outcomes

After completing this guide, you should have:

✅ Raspberry Pi OS 64-bit installed and updated
✅ SSH access configured
✅ External SSD formatted and mounted at `/mnt/ssd`
✅ Docker and Docker Compose installed
✅ zram swap configured
✅ System optimized for ERP workload
✅ Firewall configured (optional)
✅ Data directories created on SSD

## Resource Monitoring

Use these commands to monitor Pi resources during operation:

```bash
# CPU and memory usage
htop

# Disk I/O
sudo iotop

# Docker container stats
docker stats

# System temperature
vcgencmd measure_temp

# Check for throttling (should show 0x0)
vcgencmd get_throttled
```

## Troubleshooting

### SSD not detected
- Check USB connection
- Try different USB port (use USB 3.0 blue ports)
- Check `dmesg | tail` for error messages

### Docker permission denied
- Ensure user is in docker group: `groups $USER`
- Logout and login again
- Reboot if necessary

### Low memory warnings
- Check zram is active: `swapon --show`
- Reduce service memory limits in docker-compose files
- Consider using 8GB Pi 5 model

### Slow performance
- Verify SSD is mounted with `noatime`: `mount | grep ssd`
- Check for thermal throttling: `vcgencmd get_throttled`
- Ensure adequate cooling/heatsink

## Next Steps

After completing Pi provisioning:

1. Proceed to **C02: Base Docker Compose** setup
2. Configure `.env` file with environment variables
3. Start base infrastructure services
4. Run database migrations (C04)

## References

- [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)
- [Docker on Raspberry Pi](https://docs.docker.com/engine/install/debian/)
- [Pi 5 Performance Tuning](https://www.raspberrypi.com/documentation/computers/config_txt.html)

---

**Card Status:** Ready for Implementation
**Acceptance Criteria:**
- [ ] Pi boots and SSH accessible
- [ ] Docker and Compose installed and functional
- [ ] SSD mounted at /mnt/ssd with correct permissions
- [ ] zram configured and active
- [ ] All verification commands pass
- [ ] Data directories created on SSD
