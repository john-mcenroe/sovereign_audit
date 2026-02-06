#!/bin/bash

echo "🔍 Cursor Network Diagnostic Tool"
echo "=================================="
echo ""

echo "1. Checking internet connectivity..."
if ping -c 2 google.com &> /dev/null; then
    echo "   ✅ Internet connection is working"
else
    echo "   ❌ Internet connection failed"
fi

echo ""
echo "2. Checking DNS resolution for api2.cursor.sh..."
if nslookup api2.cursor.sh &> /dev/null; then
    echo "   ✅ DNS resolution successful"
    nslookup api2.cursor.sh | grep -A 2 "Name:"
else
    echo "   ❌ DNS resolution failed"
    echo "   Trying alternative DNS (8.8.8.8)..."
    if nslookup api2.cursor.sh 8.8.8.8 &> /dev/null; then
        echo "   ✅ DNS works with Google DNS (8.8.8.8)"
        echo "   💡 Consider changing your DNS settings"
    else
        echo "   ❌ DNS still fails with Google DNS"
    fi
fi

echo ""
echo "3. Checking current DNS servers..."
if [ "$(uname)" == "Darwin" ]; then
    echo "   Current DNS servers:"
    networksetup -getdnsservers Wi-Fi 2>/dev/null || networksetup -getdnsservers Ethernet 2>/dev/null || echo "   (Could not detect DNS servers)"
fi

echo ""
echo "4. Testing HTTPS connection to api2.cursor.sh..."
if curl -I --connect-timeout 5 https://api2.cursor.sh 2>&1 | head -1; then
    echo "   ✅ HTTPS connection successful"
else
    echo "   ❌ HTTPS connection failed"
fi

echo ""
echo "5. Checking for proxy settings..."
if [ -n "$http_proxy" ] || [ -n "$HTTP_PROXY" ]; then
    echo "   ⚠️  Proxy detected: $http_proxy$HTTP_PROXY"
else
    echo "   ✅ No proxy configured"
fi

echo ""
echo "=================================="
echo "Diagnostic complete!"
