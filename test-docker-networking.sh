#!/bin/bash

# Docker Networking Test Script
# Script này kiểm tra xem các container có thể giao tiếp với nhau không

echo "=========================================="
echo "Docker Networking Test"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
    fi
}

# Test 1: Check if containers are running
echo "Test 1: Checking if containers are running..."
echo "---"

containers=("vrecom_api_server" "vrecom_ai_server" "vrecom_frontend" "vrecom_redis" "vrecom_kafka")

for container in "${containers[@]}"; do
    if docker ps | grep -q "$container"; then
        print_result 0 "Container $container is running"
    else
        print_result 1 "Container $container is NOT running"
    fi
done

echo ""

# Test 2: Check container-to-container communication
echo "Test 2: Checking container-to-container communication..."
echo "---"

# Test API Server from Frontend
echo "Testing API Server connectivity from Frontend..."
docker exec vrecom_frontend curl -s http://api_server:2030/api/v1/ping > /dev/null 2>&1
print_result $? "Frontend → API Server (http://api_server:2030)"

# Test AI Server from Frontend
echo "Testing AI Server connectivity from Frontend..."
docker exec vrecom_frontend curl -s http://ai_server:9999/api/v1/health > /dev/null 2>&1
print_result $? "Frontend → AI Server (http://ai_server:9999)"

# Test Redis from API Server
echo "Testing Redis connectivity from API Server..."
docker exec vrecom_api_server curl -s http://redis:6379 > /dev/null 2>&1
print_result $? "API Server → Redis (http://redis:6379)"

echo ""

# Test 3: Check SuperAdmin Security
echo "Test 3: Checking SuperAdmin Security..."
echo "---"

# Test from localhost (should succeed)
echo "Testing SuperAdmin access from localhost..."
docker exec vrecom_api_server curl -s -H "Host: localhost" http://localhost:2030/api/v1/local/whitelist/list > /dev/null 2>&1
print_result $? "SuperAdmin access from localhost"

# Test from external IP (should fail with 403)
echo "Testing SuperAdmin access from external IP (should be denied)..."
response=$(docker exec vrecom_api_server curl -s -w "\n%{http_code}" http://api_server:2030/api/v1/local/whitelist/list)
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" = "403" ]; then
    print_result 0 "SuperAdmin correctly denies external access (HTTP 403)"
else
    print_result 1 "SuperAdmin should deny external access but got HTTP $http_code"
fi

echo ""

# Test 4: Check port mappings
echo "Test 4: Checking port mappings..."
echo "---"

ports=("2030:2030" "9999:9999" "5173:5173" "6379:6379" "9092:9092")

for port in "${ports[@]}"; do
    if docker ps --format "table {{.Ports}}" | grep -q "$port"; then
        print_result 0 "Port $port is mapped"
    else
        print_result 1 "Port $port is NOT mapped"
    fi
done

echo ""

# Test 5: Check network
echo "Test 5: Checking Docker network..."
echo "---"

if docker network ls | grep -q "vrecom_network"; then
    print_result 0 "Network 'vrecom_network' exists"
    
    # List containers in network
    echo ""
    echo "Containers in vrecom_network:"
    docker network inspect vrecom_network --format='{{range .Containers}}{{.Name}} ({{.IPv4Address}}){{println}}{{end}}'
else
    print_result 1 "Network 'vrecom_network' does NOT exist"
fi

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
