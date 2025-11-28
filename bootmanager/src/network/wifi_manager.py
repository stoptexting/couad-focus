"""Wi-Fi connection manager for Raspberry Pi."""

import asyncio
import subprocess
import time
from typing import Optional, Dict
import netifaces


class WiFiManager:
    """Manages Wi-Fi connection on Raspberry Pi."""

    def __init__(self, retry_attempts: int = 10, retry_delay: int = 5):
        """
        Initialize Wi-Fi manager.

        Args:
            retry_attempts: Number of connection attempts
            retry_delay: Delay between attempts in seconds
        """
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.interface = self._detect_wireless_interface()

    def _detect_wireless_interface(self) -> str:
        """
        Detect wireless network interface.

        Returns:
            Name of wireless interface (e.g., 'wlan0')
        """
        try:
            # Try common wireless interface names
            result = subprocess.run(
                ["ip", "link", "show"],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Look for wlan interfaces
            for line in result.stdout.split("\n"):
                if "wlan" in line and ":" in line:
                    # Extract interface name
                    interface = line.split(":")[1].strip()
                    return interface

            # Default fallback
            return "wlan0"

        except Exception:
            # If detection fails, use default
            return "wlan0"

    async def connect(self, ssid: str, password: str) -> bool:
        """
        Connect to Wi-Fi network.

        Args:
            ssid: Network SSID
            password: Network password

        Returns:
            True if connected successfully, False otherwise
        """
        print(f"[WiFi] Connecting to '{ssid}'...")

        for attempt in range(1, self.retry_attempts + 1):
            print(f"[WiFi] Attempt {attempt}/{self.retry_attempts}")

            try:
                # Use nmcli to connect (if available)
                if await self._has_nmcli():
                    success = await self._connect_with_nmcli(ssid, password)
                else:
                    # Fallback to wpa_supplicant
                    success = await self._connect_with_wpa_supplicant(ssid, password)

                if success:
                    print(f"[WiFi] Connected successfully!")
                    return True

            except Exception as e:
                print(f"[WiFi] Connection attempt failed: {e}")

            if attempt < self.retry_attempts:
                print(f"[WiFi] Waiting {self.retry_delay}s before retry...")
                await asyncio.sleep(self.retry_delay)

        print(f"[WiFi] Failed to connect after {self.retry_attempts} attempts")
        return False

    async def _has_nmcli(self) -> bool:
        """Check if nmcli is available."""
        try:
            result = await asyncio.create_subprocess_exec(
                "which", "nmcli",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            return result.returncode == 0
        except Exception:
            return False

    async def _connect_with_nmcli(self, ssid: str, password: str) -> bool:
        """
        Connect using NetworkManager (nmcli).

        Args:
            ssid: Network SSID
            password: Network password

        Returns:
            True if connection successful
        """
        try:
            # Check if connection already exists
            result = await asyncio.create_subprocess_exec(
                "nmcli", "connection", "show", ssid,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.wait()

            if result.returncode == 0:
                # Connection exists, bring it up
                process = await asyncio.create_subprocess_exec(
                    "nmcli", "connection", "up", ssid,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            else:
                # Create new connection
                process = await asyncio.create_subprocess_exec(
                    "nmcli", "device", "wifi", "connect", ssid,
                    "password", password,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

            await process.wait()

            # Wait for connection to establish
            await asyncio.sleep(3)

            # Verify connection
            return await self.is_connected()

        except Exception as e:
            print(f"[WiFi] nmcli error: {e}")
            return False

    async def _connect_with_wpa_supplicant(self, ssid: str, password: str) -> bool:
        """
        Connect using wpa_supplicant (fallback method).

        Args:
            ssid: Network SSID
            password: Network password

        Returns:
            True if connection successful
        """
        try:
            # This is a simplified approach
            # In production, you'd write to wpa_supplicant.conf and restart the service
            print("[WiFi] Using wpa_supplicant method (requires manual configuration)")
            print(f"[WiFi] Please ensure {ssid} is configured in /etc/wpa_supplicant/wpa_supplicant.conf")

            # Attempt to bring up interface
            process = await asyncio.create_subprocess_exec(
                "sudo", "ip", "link", "set", self.interface, "up",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.wait()

            # Wait for connection
            await asyncio.sleep(5)

            return await self.is_connected()

        except Exception as e:
            print(f"[WiFi] wpa_supplicant error: {e}")
            return False

    async def is_connected(self) -> bool:
        """
        Check if Wi-Fi is connected.

        Returns:
            True if connected, False otherwise
        """
        try:
            # Method 1: Check for IP address
            ip = await self.get_ip_address()
            if ip and ip != "127.0.0.1":
                return True

            # Method 2: Try to ping a known server
            process = await asyncio.create_subprocess_exec(
                "ping", "-c", "1", "-W", "2", "8.8.8.8",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.wait()

            return process.returncode == 0

        except Exception:
            return False

    async def get_ip_address(self) -> Optional[str]:
        """
        Get current IP address.

        Returns:
            IP address string or None if not connected
        """
        try:
            # Try to get IP from wireless interface
            if self.interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(self.interface)
                if netifaces.AF_INET in addrs:
                    ip = addrs[netifaces.AF_INET][0]['addr']
                    return ip

            # Fallback: get any non-loopback IP
            for interface in netifaces.interfaces():
                if interface == "lo":
                    continue

                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    ip = addrs[netifaces.AF_INET][0]['addr']
                    if ip != "127.0.0.1":
                        return ip

            return None

        except Exception as e:
            print(f"[WiFi] Error getting IP address: {e}")
            return None

    async def get_signal_strength(self) -> Optional[int]:
        """
        Get Wi-Fi signal strength.

        Returns:
            Signal strength in dBm or None if unavailable
        """
        try:
            result = await asyncio.create_subprocess_exec(
                "iwconfig", self.interface,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()

            output = stdout.decode()
            for line in output.split("\n"):
                if "Signal level" in line:
                    # Extract signal level (format: "Signal level=-XX dBm")
                    parts = line.split("Signal level=")
                    if len(parts) > 1:
                        signal = parts[1].split()[0]
                        return int(signal)

            return None

        except Exception:
            return None

    async def wait_for_connection(self, timeout: int = 60) -> bool:
        """
        Wait for Wi-Fi connection to be established.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if connected within timeout, False otherwise
        """
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            if await self.is_connected():
                return True
            await asyncio.sleep(2)

        return False

    async def disconnect(self) -> None:
        """Disconnect from current Wi-Fi network."""
        try:
            if await self._has_nmcli():
                process = await asyncio.create_subprocess_exec(
                    "nmcli", "device", "disconnect", self.interface,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.wait()
            else:
                # Bring down interface
                process = await asyncio.create_subprocess_exec(
                    "sudo", "ip", "link", "set", self.interface, "down",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.wait()

            print("[WiFi] Disconnected")

        except Exception as e:
            print(f"[WiFi] Error disconnecting: {e}")

    async def get_status(self) -> Dict[str, any]:
        """
        Get comprehensive Wi-Fi status.

        Returns:
            Dictionary with connection status, IP, signal strength, etc.
        """
        connected = await self.is_connected()
        ip = await self.get_ip_address() if connected else None
        signal = await self.get_signal_strength() if connected else None

        return {
            "connected": connected,
            "interface": self.interface,
            "ip_address": ip,
            "signal_strength": signal,
        }
