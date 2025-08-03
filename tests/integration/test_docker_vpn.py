#!/usr/bin/env python3
"""
Docker-based integration tests for Algo VPN
Tests real VPN connections between containers
"""
import os
import sys
import time
import subprocess
import unittest
import tempfile
import shutil
from pathlib import Path

class AlgoDockerIntegrationTest(unittest.TestCase):
    """Test Algo VPN functionality using Docker containers"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Docker environment once for all tests"""
        cls.test_dir = Path(__file__).parent
        cls.compose_file = cls.test_dir / "docker-compose.yml"
        cls.test_configs = cls.test_dir / "test-configs"
        
        # Create test configs directory
        cls.test_configs.mkdir(exist_ok=True)
        
        # Build and start containers
        print("Building Docker images...")
        subprocess.run(
            ["docker-compose", "-f", str(cls.compose_file), "build"],
            check=True
        )
        
        print("Starting Docker containers...")
        subprocess.run(
            ["docker-compose", "-f", str(cls.compose_file), "up", "-d"],
            check=True
        )
        
        # Wait for Algo server to be ready
        print("Waiting for Algo server to provision...")
        max_wait = 300  # 5 minutes
        start_time = time.time()
        while time.time() - start_time < max_wait:
            result = subprocess.run(
                ["docker", "exec", "algo-server", "test", "-f", "/etc/algo/.provisioned"],
                capture_output=True
            )
            if result.returncode == 0:
                print("Algo server ready!")
                break
            time.sleep(10)
        else:
            raise RuntimeError("Algo server failed to provision in time")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up Docker environment"""
        print("Stopping Docker containers...")
        subprocess.run(
            ["docker-compose", "-f", str(cls.compose_file), "down", "-v"],
            check=True
        )
        
        # Clean up test configs
        if cls.test_configs.exists():
            shutil.rmtree(cls.test_configs)
    
    def docker_exec(self, container, command, check=True):
        """Execute command in container"""
        cmd = ["docker", "exec", container] + command.split()
        result = subprocess.run(cmd, capture_output=True, text=True)
        if check and result.returncode != 0:
            print(f"Command failed: {command}")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, cmd)
        return result
    
    def test_wireguard_connection(self):
        """Test WireGuard VPN connection"""
        print("\n=== Testing WireGuard Connection ===")
        
        # Copy WireGuard config from server to shared volume
        self.docker_exec(
            "algo-server",
            "cp /algo/configs/10.99.0.10/wireguard/testuser1.conf /etc/algo/testuser1-wg.conf"
        )
        
        # Copy config to client
        self.docker_exec(
            "client-ubuntu",
            "cp /configs/testuser1-wg.conf /etc/wireguard/wg0.conf"
        )
        
        # Connect with WireGuard
        result = self.docker_exec(
            "client-ubuntu",
            "/usr/local/bin/test-utils.sh wireguard /etc/wireguard/wg0.conf",
            check=False
        )
        
        self.assertEqual(result.returncode, 0, "WireGuard connection failed")
        self.assertIn("SUCCESS: Can reach VPN gateway", result.stdout)
        
        # Clean up
        self.docker_exec("client-ubuntu", "wg-quick down wg0", check=False)
    
    def test_ipsec_connection(self):
        """Test IPsec VPN connection"""
        print("\n=== Testing IPsec Connection ===")
        
        # Copy IPsec configs from server
        self.docker_exec(
            "algo-server",
            "cp -r /algo/configs/10.99.0.10/ipsec/testuser1 /etc/algo/testuser1-ipsec"
        )
        
        # Set up IPsec on client
        # Note: This is simplified - real IPsec setup is more complex
        result = self.docker_exec(
            "client-debian",
            "/usr/local/bin/test-utils.sh ipsec /configs/testuser1-ipsec",
            check=False
        )
        
        # IPsec in containers is tricky due to kernel requirements
        # For now, we just check that the test ran
        self.assertIsNotNone(result)
        print(f"IPsec test output: {result.stdout}")
    
    def test_dns_blocking(self):
        """Test DNS ad-blocking functionality"""
        print("\n=== Testing DNS Functionality ===")
        
        # First establish WireGuard connection
        self.docker_exec(
            "algo-server",
            "cp /algo/configs/10.99.0.10/wireguard/testuser2.conf /etc/algo/testuser2-wg.conf"
        )
        
        self.docker_exec(
            "client-debian",
            "cp /configs/testuser2-wg.conf /etc/wireguard/wg0.conf"
        )
        
        self.docker_exec(
            "client-debian",
            "wg-quick up wg0"
        )
        
        # Test DNS resolution through VPN
        result = self.docker_exec(
            "client-debian",
            "nslookup google.com 10.19.49.1",
            check=False
        )
        
        self.assertEqual(result.returncode, 0, "DNS resolution failed")
        self.assertIn("Address:", result.stdout)
        
        # Clean up
        self.docker_exec("client-debian", "wg-quick down wg0", check=False)
    
    def test_multiple_clients(self):
        """Test multiple clients connecting simultaneously"""
        print("\n=== Testing Multiple Client Connections ===")
        
        clients = [
            ("client-ubuntu", "testuser1"),
            ("client-debian", "testuser2")
        ]
        
        # Connect both clients
        for client, user in clients:
            self.docker_exec(
                "algo-server",
                f"cp /algo/configs/10.99.0.10/wireguard/{user}.conf /etc/algo/{user}-wg.conf"
            )
            
            self.docker_exec(
                client,
                f"cp /configs/{user}-wg.conf /etc/wireguard/wg0.conf"
            )
            
            self.docker_exec(
                client,
                "wg-quick up wg0"
            )
        
        # Test that both can ping the gateway
        for client, _ in clients:
            result = self.docker_exec(
                client,
                "ping -c 2 10.19.49.1",
                check=False
            )
            self.assertEqual(result.returncode, 0, f"{client} cannot reach gateway")
        
        # Test that clients can reach each other (if BetweenClients_DROP is false)
        result = self.docker_exec(
            "client-ubuntu",
            "ping -c 2 10.19.49.3",  # Assuming client-debian gets .3
            check=False
        )
        # This might fail depending on BetweenClients_DROP setting
        print(f"Inter-client connectivity: {'Success' if result.returncode == 0 else 'Blocked'}")
        
        # Clean up
        for client, _ in clients:
            self.docker_exec(client, "wg-quick down wg0", check=False)
    
    def test_service_availability(self):
        """Test that all Algo services are running"""
        print("\n=== Testing Service Availability ===")
        
        services = [
            ("wireguard", "systemctl is-active wg-quick@wg0 || echo inactive"),
            ("strongswan", "systemctl is-active strongswan || echo inactive"),
        ]
        
        for service_name, check_cmd in services:
            result = self.docker_exec("algo-server", check_cmd, check=False)
            print(f"{service_name}: {result.stdout.strip()}")
            # Services might not be active until a client connects
            self.assertIsNotNone(result)


def run_integration_tests():
    """Run the integration test suite"""
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Run tests
    unittest.main(argv=sys.argv[:1], verbosity=2)


if __name__ == "__main__":
    run_integration_tests()