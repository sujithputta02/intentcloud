#!/usr/bin/env bash
# ==============================================================================
# IntentCloud — Raspberry Pi 3B/4B Edge Node Automated Provisioning Script
# Department of Computer Science & Technology, Dayananda Sagar University
# Week 7 / Phase 5 Edge Bring-Up
# ==============================================================================

set -euo pipefail

echo "========================================================="
echo "🚀 IntentCloud: Starting Raspberry Pi Edge Node Setup"
echo "========================================================="

# 1. Update OS packages
echo "📦 Updating apt packages..."
sudo apt-get update -y && sudo apt-get upgrade -y

# 2. Install essential dependencies
echo "📦 Installing build tools and Python 3.11 environment..."
sudo apt-get install -y \
  python3-pip \
  python3-venv \
  python3-dev \
  build-essential \
  git \
  curl \
  wget \
  libopenblas-dev \
  libssl-dev \
  pkg-config \
  htop

# 3. Create virtual environment if missing
INSTALL_DIR="$HOME/intentcloud-api"
if [ ! -d "$INSTALL_DIR" ]; then
  echo "⚠️ $INSTALL_DIR not found, creating directory..."
  mkdir -p "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
if [ ! -d "venv" ]; then
  echo "🐍 Creating Python virtual environment..."
  python3 -m venv venv
fi

# 4. Install Python dependencies with ARM optimizations
echo "⚡ Activating virtual environment & installing requirements..."
source venv/bin/activate
pip install --upgrade pip setuptools wheel
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
fi

# 5. Install Cloudflare Tunnel (ARM64)
echo "🌐 Installing Cloudflare Tunnel (cloudflared)..."
ARCH=$(dpkg --print-architecture)
if ! command -v cloudflared &> /dev/null; then
  if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
    sudo dpkg -i cloudflared-linux-arm64.deb || sudo apt-get install -f -y
    rm -f cloudflared-linux-arm64.deb
  elif [ "$ARCH" = "armhf" ]; then
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-armhf.deb
    sudo dpkg -i cloudflared-linux-armhf.deb || sudo apt-get install -f -y
    rm -f cloudflared-linux-armhf.deb
  fi
  echo "✅ cloudflared installed successfully."
else
  echo "✅ cloudflared is already installed."
fi

# 6. Create systemd service for IntentCloud auto-start
echo "⚙️ Configuring systemd service: intentcloud.service..."
sudo tee /etc/systemd/system/intentcloud.service > /dev/null <<EOF
[Unit]
Description=IntentCloud Cognitive Edge API Daemon
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
echo "✅ systemd service created."
echo ""
echo "========================================================="
echo "🎉 IntentCloud Pi Setup Complete!"
echo "To start IntentCloud backend service:"
echo "  sudo systemctl enable --now intentcloud"
echo ""
echo "To check live status:"
echo "  sudo systemctl status intentcloud"
echo ""
echo "To start public Zero-Trust HTTPS tunnel:"
echo "  cloudflared tunnel --url http://localhost:8000"
echo "========================================================="
