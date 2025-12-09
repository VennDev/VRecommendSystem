#!/bin/bash

# VRecommendation - LAN Access Setup Script for Linux/macOS

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "===================================================================="
echo "   VRecommendation - LAN Access Configuration Setup"
echo "===================================================================="
echo ""

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}[INFO]${NC} Detecting network configuration..."
echo ""

# Detect OS and get IP addresses
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    IPS=($(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'))
else
    # Linux
    IPS=($(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127.0.0.1))
    if [ ${#IPS[@]} -eq 0 ]; then
        # Fallback for older systems
        IPS=($(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | cut -d: -f2))
    fi
fi

if [ ${#IPS[@]} -eq 0 ]; then
    echo -e "${RED}[ERROR]${NC} No IPv4 address found. Please check your network connection."
    exit 1
fi

echo "Found ${#IPS[@]} IPv4 address(es):"
echo ""

# Display all IPs
for i in "${!IPS[@]}"; do
    echo "  [$((i+1))] ${IPS[$i]}"
done
echo ""

# Auto-select if only one IP, otherwise ask user
if [ ${#IPS[@]} -eq 1 ]; then
    SELECTED_IP="${IPS[0]}"
    echo -e "${BLUE}[INFO]${NC} Auto-selected: $SELECTED_IP"
else
    read -p "Select IP address number [1-${#IPS[@]}] or enter custom IP: " IP_CHOICE

    # Check if it's a number within range
    if [[ "$IP_CHOICE" =~ ^[0-9]+$ ]] && [ "$IP_CHOICE" -ge 1 ] && [ "$IP_CHOICE" -le ${#IPS[@]} ]; then
        SELECTED_IP="${IPS[$((IP_CHOICE-1))]}"
    else
        # Assume user entered custom IP
        SELECTED_IP="$IP_CHOICE"
    fi
fi

echo ""
echo -e "${BLUE}[INFO]${NC} Using IP address: $SELECTED_IP"
echo ""

# Validate IP format
if ! [[ $SELECTED_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}[ERROR]${NC} Invalid IP address format: $SELECTED_IP"
    exit 1
fi

# Confirm with user
read -p "Continue with this IP? (y/n): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}[CANCELLED]${NC} Setup cancelled by user."
    exit 0
fi

echo ""
echo -e "${BLUE}[INFO]${NC} Updating .env file for LAN access..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}[ERROR]${NC} .env file not found!"
    echo ""
    echo "Please create .env file first:"
    echo "  - Copy from .env.example or example-env"
    echo "  - Or run dev-setup.cmd"
    echo ""
    exit 1
fi

# Backup existing .env
echo -e "${BLUE}[INFO]${NC} Backing up existing .env to .env.backup"
cp ".env" ".env.backup"

# Update HOST_IP using sed
echo -e "${BLUE}[INFO]${NC} Updating HOST_IP to $SELECTED_IP"
sed -i.bak "s|^HOST_IP=.*|HOST_IP=$SELECTED_IP|g" ".env" 2>/dev/null || \
sed -i '' "s|^HOST_IP=.*|HOST_IP=$SELECTED_IP|g" ".env"

# Update VITE_API_SERVER_URL
echo -e "${BLUE}[INFO]${NC} Updating VITE_API_SERVER_URL"
sed -i.bak "s|^VITE_API_SERVER_URL=.*|VITE_API_SERVER_URL=http://$SELECTED_IP:2030|g" ".env" 2>/dev/null || \
sed -i '' "s|^VITE_API_SERVER_URL=.*|VITE_API_SERVER_URL=http://$SELECTED_IP:2030|g" ".env"

# Update VITE_AI_SERVER_URL
echo -e "${BLUE}[INFO]${NC} Updating VITE_AI_SERVER_URL"
sed -i.bak "s|^VITE_AI_SERVER_URL=.*|VITE_AI_SERVER_URL=http://$SELECTED_IP:9999|g" ".env" 2>/dev/null || \
sed -i '' "s|^VITE_AI_SERVER_URL=.*|VITE_AI_SERVER_URL=http://$SELECTED_IP:9999|g" ".env"

# Remove backup files
rm -f ".env.bak" 2>/dev/null

echo -e "${GREEN}[SUCCESS]${NC} .env file updated successfully for LAN access!"
echo ""

# Ask if user wants to rebuild Docker
echo "===================================================================="
echo "   Next Steps"
echo "===================================================================="
echo ""
echo "To apply changes, you need to rebuild the Docker containers:"
echo ""
echo "  docker-compose down"
echo "  docker-compose build --no-cache frontend"
echo "  docker-compose up -d"
echo ""

read -p "Do you want to rebuild Docker now? (y/n): " REBUILD
if [[ "$REBUILD" =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}[INFO]${NC} Stopping containers..."
    docker-compose down

    echo ""
    echo -e "${BLUE}[INFO]${NC} Rebuilding frontend..."
    docker-compose build --no-cache frontend

    echo ""
    echo -e "${BLUE}[INFO]${NC} Starting containers..."
    docker-compose up -d

    echo ""
    echo -e "${GREEN}[SUCCESS]${NC} Docker containers rebuilt and started!"
fi

echo ""
echo "===================================================================="
echo "   Configuration Complete!"
echo "===================================================================="
echo ""
echo "Your VRecommendation system is now configured for LAN access."
echo ""
echo "Access URLs:"
echo "  Frontend:    http://$SELECTED_IP:5173"
echo "  API Server:  http://$SELECTED_IP:2030"
echo "  AI Server:   http://$SELECTED_IP:9999"
echo "  Kafka UI:    http://$SELECTED_IP:8080"
echo ""
echo -e "${YELLOW}NOTE:${NC} SuperAdmin features are ONLY accessible from localhost!"
echo "      Use Admin Portal (admin-portal/start.sh) on this machine."
echo ""
echo "===================================================================="
echo ""

# Open firewall ports (Linux only)
if [[ "$OSTYPE" != "darwin"* ]]; then
    read -p "Do you want to open firewall ports (requires sudo)? (y/n): " FIREWALL
    if [[ "$FIREWALL" =~ ^[Yy]$ ]]; then
        echo ""
        echo -e "${BLUE}[INFO]${NC} Opening firewall ports..."

        # Try ufw first (Ubuntu/Debian)
        if command -v ufw &> /dev/null; then
            sudo ufw allow 5173/tcp comment "VRecom Frontend"
            sudo ufw allow 2030/tcp comment "VRecom API"
            sudo ufw allow 9999/tcp comment "VRecom AI"
            sudo ufw allow 8080/tcp comment "VRecom Kafka UI"
            echo -e "${GREEN}[SUCCESS]${NC} UFW firewall rules added!"
        # Try firewalld (CentOS/RHEL/Fedora)
        elif command -v firewall-cmd &> /dev/null; then
            sudo firewall-cmd --permanent --add-port=5173/tcp
            sudo firewall-cmd --permanent --add-port=2030/tcp
            sudo firewall-cmd --permanent --add-port=9999/tcp
            sudo firewall-cmd --permanent --add-port=8080/tcp
            sudo firewall-cmd --reload
            echo -e "${GREEN}[SUCCESS]${NC} Firewalld rules added!"
        else
            echo -e "${YELLOW}[WARNING]${NC} No known firewall manager found. Please open ports manually."
        fi
    fi
fi

echo ""
echo "Setup complete!"
