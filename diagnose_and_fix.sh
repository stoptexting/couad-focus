#!/bin/bash
# Diagnostic and fix script for Focus Raspberry Pi setup
# Run this on the Raspberry Pi to diagnose and fix ngrok connection issues

set -e

echo "========================================"
echo "Focus System Diagnostic & Fix Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "1. Checking nginx installation..."
if command -v nginx &> /dev/null; then
    print_status 0 "nginx is installed"
    nginx -v
else
    print_status 1 "nginx is NOT installed"
    print_warning "Install with: sudo apt-get install nginx"
    exit 1
fi

echo ""
echo "2. Checking nginx status..."
if systemctl is-active --quiet nginx; then
    print_status 0 "nginx is running"
else
    print_status 1 "nginx is NOT running"
    echo "   Attempting to start nginx..."
    sudo systemctl start nginx
    if systemctl is-active --quiet nginx; then
        print_status 0 "nginx started successfully"
    else
        print_status 1 "nginx failed to start"
        echo "   Checking nginx error logs:"
        sudo journalctl -u nginx -n 20 --no-pager
        exit 1
    fi
fi

echo ""
echo "3. Checking ports..."
echo "   Port 80 (nginx):"
if sudo lsof -i :80 -P -n | grep LISTEN; then
    print_status 0 "Something is listening on port 80"
else
    print_status 1 "Nothing listening on port 80 - nginx may not be configured"
fi

echo ""
echo "   Port 3000 (frontend):"
if lsof -i :3000 -P -n | grep LISTEN; then
    print_status 0 "Frontend is running on port 3000"
else
    print_status 1 "Frontend is NOT running on port 3000"
    print_warning "Frontend needs to be started"
fi

echo ""
echo "   Port 5001 (backend):"
if lsof -i :5001 -P -n | grep LISTEN; then
    print_status 0 "Backend is running on port 5001"
else
    print_status 1 "Backend is NOT running on port 5001"
    print_warning "Backend needs to be started"
fi

echo ""
echo "4. Checking nginx configuration..."
if [ -f /etc/nginx/sites-available/focus ]; then
    print_status 0 "Focus nginx config exists"
    echo "   Config content:"
    sudo cat /etc/nginx/sites-available/focus | grep -E "(listen|proxy_pass|location)" | head -15
else
    print_status 1 "Focus nginx config NOT found at /etc/nginx/sites-available/focus"
    print_warning "Bootmanager should create this config automatically"
fi

echo ""
if [ -L /etc/nginx/sites-enabled/focus ]; then
    print_status 0 "Focus nginx config is enabled"
else
    print_status 1 "Focus nginx config NOT enabled"
    if [ -f /etc/nginx/sites-available/focus ]; then
        echo "   Enabling config..."
        sudo ln -sf /etc/nginx/sites-available/focus /etc/nginx/sites-enabled/focus
        sudo nginx -t && sudo systemctl reload nginx
        print_status 0 "Config enabled and nginx reloaded"
    fi
fi

echo ""
echo "5. Testing nginx configuration..."
if sudo nginx -t; then
    print_status 0 "nginx configuration is valid"
else
    print_status 1 "nginx configuration has errors"
    exit 1
fi

echo ""
echo "6. Checking bootmanager service..."
if systemctl is-active --quiet bootmanager; then
    print_status 0 "bootmanager service is running"
    echo "   Recent logs:"
    sudo journalctl -u bootmanager -n 10 --no-pager | tail -5
else
    print_status 1 "bootmanager service is NOT running"
    print_warning "Start with: sudo systemctl start bootmanager"
fi

echo ""
echo "7. Testing local connectivity..."
echo "   Testing port 80 (nginx):"
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:80 > /tmp/curl_result.txt 2>&1; then
    status_code=$(cat /tmp/curl_result.txt)
    if [ "$status_code" != "000" ]; then
        print_status 0 "Port 80 responds (HTTP $status_code)"
    else
        print_status 1 "Port 80 connection failed"
    fi
else
    print_status 1 "Cannot connect to port 80"
    print_warning "This is why ngrok shows ERR_NGROK_8012"
fi

echo ""
echo "8. Checking ngrok processes..."
if pgrep -f "ngrok http" > /dev/null; then
    print_status 0 "ngrok HTTP tunnel is running"
    echo "   Ngrok processes:"
    ps aux | grep ngrok | grep -v grep
else
    print_status 1 "ngrok HTTP tunnel is NOT running"
fi

echo ""
echo "========================================"
echo "SUMMARY & RECOMMENDATIONS"
echo "========================================"

# Check if everything is working
ALL_OK=true

if ! systemctl is-active --quiet nginx; then
    ALL_OK=false
    echo "• Nginx is not running - this is the main issue!"
    echo "  Fix: sudo systemctl start nginx"
fi

if ! lsof -i :80 -P -n | grep LISTEN > /dev/null 2>&1; then
    ALL_OK=false
    echo "• Nothing is listening on port 80"
    echo "  Fix: Ensure nginx is running and configured correctly"
fi

if ! lsof -i :3000 -P -n | grep LISTEN > /dev/null 2>&1; then
    ALL_OK=false
    echo "• Frontend is not running on port 3000"
    echo "  Fix: The bootmanager should start this automatically"
fi

if ! lsof -i :5001 -P -n | grep LISTEN > /dev/null 2>&1; then
    ALL_OK=false
    echo "• Backend is not running on port 5001"
    echo "  Fix: The bootmanager should start this automatically"
fi

if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}All services appear to be running correctly!${NC}"
    echo "If ngrok is still showing errors, try restarting the HTTP tunnel:"
    echo "  1. Stop bootmanager: sudo systemctl stop bootmanager"
    echo "  2. Start bootmanager: sudo systemctl start bootmanager"
else
    echo ""
    echo "RECOMMENDED ACTIONS:"
    echo "1. Restart bootmanager to start all services:"
    echo "   sudo systemctl restart bootmanager"
    echo ""
    echo "2. Monitor the startup process:"
    echo "   sudo journalctl -u bootmanager -f"
    echo ""
    echo "3. After services start, check this script again:"
    echo "   bash diagnose_and_fix.sh"
fi

echo ""
echo "========================================"
