#!/bin/bash
# Test script to verify mock systemctl behavior

echo "Testing mock systemctl..."

# Test starting a service
systemctl start test-service
if systemctl is-active test-service; then
    echo "✓ Service start works"
else
    echo "✗ Service start failed"
fi

# Test stopping a service
systemctl stop test-service
if ! systemctl is-active test-service; then
    echo "✓ Service stop works"
else
    echo "✗ Service stop failed"
fi

# Test enabling a service
systemctl enable test-service
if systemctl is-enabled test-service; then
    echo "✓ Service enable works"
else
    echo "✗ Service enable failed"
fi

# Test restart
systemctl start test-service
systemctl restart test-service
if systemctl is-active test-service; then
    echo "✓ Service restart works"
else
    echo "✗ Service restart failed"
fi

# Test daemon-reload
if systemctl daemon-reload; then
    echo "✓ daemon-reload works"
else
    echo "✗ daemon-reload failed"
fi

# Test status
echo "Testing status output:"
systemctl status test-service

# Test list-units
echo -e "\nActive units:"
systemctl list-units

echo -e "\nFake systemd log:"
cat /var/log/fake-systemd.log | tail -10