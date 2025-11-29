#!/bin/bash

echo ""
echo "===================================================="
echo "  VRecommendation Admin Portal - Starting..."
echo "===================================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed or not in PATH."
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Navigate to admin-portal directory
cd "$(dirname "$0")"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "[INFO] Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install dependencies."
        exit 1
    fi
    echo "[INFO] Dependencies installed successfully."
    echo ""
fi

echo "[INFO] Starting Admin Portal on http://127.0.0.1:3456"
echo "[INFO] This portal is ONLY accessible from localhost!"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""

npm start
