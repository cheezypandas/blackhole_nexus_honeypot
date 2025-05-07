#!/bin/bash
# blackhole-nexus/setup.sh - Automated Docker/WSL2 Honeypot Setup

set -e  # Exit on error

echo "🔧 Starting Blackhole Nexus Honeypot Setup 🔧"

# ====================
# 1. WSL2 Configuration
# ====================
echo -e "\n[1/5] Configuring WSL2..."
if ! command -v wsl &> /dev/null; then
    echo "❌ WSL2 not found. Enable via:"
    echo "   PowerShell (Admin): wsl --install"
    exit 1
fi

# ==================
# 2. Docker Setup
# ==================
echo -e "\n[2/5] Installing Docker..."
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# ==================
# 3. Permissions
# ==================
echo -e "\n[3/5] Setting permissions..."
sudo usermod -aG docker $USER
newgrp docker <<EOF
echo "✅ Docker permissions updated"
EOF

# ==================
# 4. Start Services
# ==================
echo -e "\n[4/5] Launching honeypot containers..."
docker compose -f honeypots/cowrie/docker-compose.yml up -d
docker compose -f logging/elk/docker-compose.yml up -d

# ==================
# 5. Verification
# ==================
echo -e "\n[5/5] Verifying setup..."
echo -e "\n🛡️ Running Containers:"
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"

echo -e "\n🔌 Connection Test:"
echo "Try this in Windows PowerShell:"
echo "  ssh root@localhost -p 2222 (password: 'password')"

echo -e "\n📊 Logs Location:"
echo "Live attack logs: /var/lib/docker/volumes/cowrie_log/_data/cowrie.json"
echo "Kibana dashboard: http://localhost:5601 (wait 5 mins for startup)"

echo -e "\n✅ Setup Complete! Monitor attacks with:"
echo "  tail -f /var/lib/docker/volumes/cowrie_log/_data/cowrie.json"