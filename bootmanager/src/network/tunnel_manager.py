"""Ngrok tunnel manager for SSH access."""

import asyncio
import subprocess
import requests
import time
from typing import Optional, Dict
import json
import tempfile
import yaml
from pathlib import Path


class TunnelManager:
    """Manages ngrok tunnel for SSH access."""

    def __init__(
        self,
        auth_token: str,
        retry_delay: int = 30,
        http_username: Optional[str] = None,
        http_password: Optional[str] = None
    ):
        """
        Initialize tunnel manager.

        Args:
            auth_token: Ngrok authentication token
            retry_delay: Delay between retry attempts in seconds
            http_username: HTTP Basic Auth username (optional)
            http_password: HTTP Basic Auth password (optional)
        """
        self.auth_token = auth_token
        self.retry_delay = retry_delay
        self.http_username = http_username
        self.http_password = http_password

        # SSH tunnel
        self.process: Optional[subprocess.Popen] = None
        self.tunnel_url: Optional[str] = None

        # HTTP tunnel
        self.http_process: Optional[subprocess.Popen] = None
        self.http_tunnel_url: Optional[str] = None
        self.http_config_file: Optional[str] = None  # Temporary config file for HTTP tunnel

        # Port 4040 is used by ngrok-ssh.service (emergency tunnel)
        # Port 4041 is used by bootmanager's HTTP tunnel
        self.ssh_api_url = "http://localhost:4040/api/tunnels"  # Emergency tunnel API
        self.http_api_url = "http://localhost:4041/api/tunnels"  # HTTP tunnel API

    async def get_existing_ssh_tunnel(self) -> Optional[str]:
        """
        Query existing SSH tunnel from ngrok-ssh.service (emergency tunnel).

        This method does NOT start a new tunnel. It queries the existing
        ngrok process managed by ngrok-ssh.service for its tunnel URL.

        Returns:
            Public tunnel URL (tcp://X.tcp.ngrok.io:XXXXX) or None if not found
        """
        print("[Ngrok] Querying emergency SSH tunnel (ngrok-ssh.service)...")

        try:
            # Try multiple times to allow ngrok-ssh.service time to initialize
            for attempt in range(1, 11):  # Try 10 times over 10 seconds
                self.tunnel_url = await self._get_tunnel_url_from_api(self.ssh_api_url)

                if self.tunnel_url:
                    print(f"[Ngrok] Found emergency SSH tunnel: {self.tunnel_url}")
                    return self.tunnel_url

                await asyncio.sleep(1)

            print("[Ngrok] Emergency SSH tunnel not found (ngrok-ssh.service may not be running)")
            return None

        except Exception as e:
            print(f"[Ngrok] Error querying emergency tunnel: {e}")
            return None

    async def start_tunnel(self) -> Optional[str]:
        """
        DEPRECATED: Use get_existing_ssh_tunnel() instead.

        SSH tunnel is now managed by ngrok-ssh.service (emergency access).
        Bootmanager should query the existing tunnel, not start a new one.

        Returns:
            Public tunnel URL or None if failed
        """
        print("[Ngrok] WARNING: start_tunnel() is deprecated. SSH tunnel managed by ngrok-ssh.service")
        print("[Ngrok] Falling back to get_existing_ssh_tunnel()...")
        return await self.get_existing_ssh_tunnel()

    async def start_http_tunnel(self, port: int = 80) -> Optional[str]:
        """
        Start ngrok HTTP tunnel with basic auth.

        Uses port 4041 for ngrok API to avoid conflict with ngrok-ssh.service (port 4040).
        Creates a temporary ngrok config file since v3 requires web_addr in config, not CLI flag.

        Args:
            port: Local port to tunnel (default 80 for nginx)

        Returns:
            Public HTTPS URL or None if failed
        """
        print(f"[Ngrok] Starting HTTP tunnel for port {port}...")

        try:
            # Create temporary ngrok config file for HTTP tunnel
            # ngrok v3 requires web_addr in config file, not as CLI flag
            config = {
                "version": "3",
                "agent": {
                    "authtoken": self.auth_token,
                    "web_addr": "127.0.0.1:4041"  # Use port 4041 to avoid conflict with SSH tunnel
                }
            }

            # Create temporary config file
            fd, self.http_config_file = tempfile.mkstemp(suffix=".yml", prefix="ngrok-http-")
            with open(self.http_config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

            print(f"[Ngrok] Created config file: {self.http_config_file}")

            # Debug: Show config file content
            with open(self.http_config_file, 'r') as f:
                config_content = f.read()
                print(f"[Ngrok] Config file content:\n{config_content}")

            # Build ngrok command using config file
            # Use 127.0.0.1 explicitly to force IPv4 and avoid IPv6 connection issues
            cmd = [
                "ngrok", "http", f"127.0.0.1:{port}",
                "--config", self.http_config_file
            ]

            # Add basic auth if credentials provided
            if self.http_username and self.http_password:
                auth_string = f"{self.http_username}:{self.http_password}"
                cmd.extend(["--basic-auth", auth_string])
                print(f"[Ngrok] HTTP tunnel will require authentication (user: {self.http_username})")

            # Debug: Show exact command
            print(f"[Ngrok] Running command: {' '.join(cmd)}")

            # Start ngrok process
            self.http_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL
            )

            print(f"[Ngrok] Process started with PID: {self.http_process.pid}")

            # Wait for ngrok to initialize
            print("[Ngrok] Waiting for HTTP tunnel to establish...")
            await asyncio.sleep(3)

            # Check if process is still running
            if self.http_process.poll() is not None:
                # Process died, get error output
                stdout, stderr = self.http_process.communicate()
                print(f"[Ngrok] ERROR: Process exited with code {self.http_process.returncode}")
                print(f"[Ngrok] STDOUT: {stdout.decode('utf-8', errors='ignore')}")
                print(f"[Ngrok] STDERR: {stderr.decode('utf-8', errors='ignore')}")
                await self.stop_http_tunnel()
                return None

            # Get tunnel URL from API (using port 4041)
            for attempt in range(1, 11):  # Try 10 times over 10 seconds
                # Check if process is still alive
                if self.http_process.poll() is not None:
                    stdout, stderr = self.http_process.communicate()
                    print(f"[Ngrok] ERROR: Process died during startup")
                    print(f"[Ngrok] STDERR: {stderr.decode('utf-8', errors='ignore')}")
                    await self.stop_http_tunnel()
                    return None

                self.http_tunnel_url = await self._get_http_tunnel_url_from_api(self.http_api_url)

                if self.http_tunnel_url:
                    print(f"[Ngrok] HTTP tunnel established: {self.http_tunnel_url}")
                    return self.http_tunnel_url

                print(f"[Ngrok] Attempt {attempt}/10: No tunnel URL yet, waiting...")
                await asyncio.sleep(1)

            # Final check: is the process still running?
            if self.http_process.poll() is not None:
                stdout, stderr = self.http_process.communicate()
                print(f"[Ngrok] ERROR: Process not running after 10 attempts")
                print(f"[Ngrok] Exit code: {self.http_process.returncode}")
                print(f"[Ngrok] STDERR: {stderr.decode('utf-8', errors='ignore')}")
            else:
                print(f"[Ngrok] ERROR: Process running but API not responding on port 4041")
                print(f"[Ngrok] Process PID: {self.http_process.pid}")
                # Try to get any output
                try:
                    import select
                    if select.select([self.http_process.stderr], [], [], 0)[0]:
                        stderr_data = self.http_process.stderr.read()
                        print(f"[Ngrok] Available STDERR: {stderr_data.decode('utf-8', errors='ignore')}")
                except Exception as e:
                    print(f"[Ngrok] Could not read stderr: {e}")

            print("[Ngrok] Failed to get HTTP tunnel URL from API")
            await self.stop_http_tunnel()
            return None

        except FileNotFoundError:
            print("[Ngrok] ERROR: ngrok not found. Please install ngrok.")
            return None
        except Exception as e:
            print(f"[Ngrok] Error starting HTTP tunnel: {e}")
            await self.stop_http_tunnel()
            return None

    async def _get_tunnel_url_from_api(self, api_url: str) -> Optional[str]:
        """
        Get SSH tunnel URL from ngrok local API.

        Args:
            api_url: Ngrok API URL (either port 4040 for SSH or 4041 for HTTP)

        Returns:
            Tunnel URL (tcp://X.tcp.ngrok.io:XXXXX) or None
        """
        try:
            response = requests.get(api_url, timeout=2)

            if response.status_code == 200:
                data = response.json()

                # Find the TCP tunnel
                for tunnel in data.get("tunnels", []):
                    if tunnel.get("proto") == "tcp":
                        public_url = tunnel.get("public_url")
                        if public_url:
                            return public_url

            return None

        except requests.exceptions.RequestException:
            return None
        except Exception as e:
            print(f"[Ngrok] API error: {e}")
            return None

    async def _get_http_tunnel_url_from_api(self, api_url: str) -> Optional[str]:
        """
        Get HTTP tunnel URL from ngrok local API.

        Args:
            api_url: Ngrok API URL (should be port 4041 for HTTP tunnel)

        Returns:
            Tunnel URL (https://X.ngrok.io) or None
        """
        try:
            response = requests.get(api_url, timeout=2)

            if response.status_code == 200:
                data = response.json()

                # Find the HTTPS tunnel
                for tunnel in data.get("tunnels", []):
                    proto = tunnel.get("proto")
                    public_url = tunnel.get("public_url", "")

                    # Look for https tunnel
                    if proto == "https" or public_url.startswith("https://"):
                        return public_url

            return None

        except requests.exceptions.RequestException:
            return None
        except Exception as e:
            print(f"[Ngrok] API error: {e}")
            return None

    async def get_tunnel_url(self) -> Optional[str]:
        """
        Get current SSH tunnel URL (from emergency tunnel).

        Returns:
            Tunnel URL or None if not active
        """
        if self.tunnel_url:
            return self.tunnel_url

        # Try to refresh from emergency tunnel API
        self.tunnel_url = await self._get_tunnel_url_from_api(self.ssh_api_url)
        return self.tunnel_url

    async def is_tunnel_active(self) -> bool:
        """
        Check if emergency SSH tunnel is active.

        Note: This checks the emergency tunnel managed by ngrok-ssh.service,
        not a tunnel started by bootmanager.

        Returns:
            True if tunnel is running and reachable
        """
        # Check if we can get tunnel URL from emergency tunnel API
        url = await self._get_tunnel_url_from_api(self.ssh_api_url)
        return url is not None

    async def get_http_tunnel_url(self) -> Optional[str]:
        """
        Get current HTTP tunnel URL.

        Returns:
            HTTP tunnel URL or None if not active
        """
        if self.http_tunnel_url:
            return self.http_tunnel_url

        # Try to refresh from HTTP tunnel API (port 4041)
        self.http_tunnel_url = await self._get_http_tunnel_url_from_api(self.http_api_url)
        return self.http_tunnel_url

    async def is_http_tunnel_active(self) -> bool:
        """
        Check if HTTP tunnel is active.

        Returns:
            True if HTTP tunnel is running and reachable
        """
        # Check if process is running
        if self.http_process is None or self.http_process.poll() is not None:
            return False

        # Check if we can get tunnel URL from HTTP tunnel API (port 4041)
        url = await self._get_http_tunnel_url_from_api(self.http_api_url)
        return url is not None

    async def stop_tunnel(self) -> None:
        """Stop the ngrok tunnel."""
        print("[Ngrok] Stopping tunnel...")

        if self.process:
            try:
                self.process.terminate()
                # Wait up to 5 seconds for graceful shutdown
                for _ in range(10):
                    if self.process.poll() is not None:
                        break
                    await asyncio.sleep(0.5)

                # Force kill if still running
                if self.process.poll() is None:
                    self.process.kill()
                    await asyncio.sleep(0.5)

            except Exception as e:
                print(f"[Ngrok] Error stopping tunnel: {e}")

            self.process = None

        self.tunnel_url = None
        print("[Ngrok] Tunnel stopped")

    async def stop_http_tunnel(self) -> None:
        """Stop the ngrok HTTP tunnel and clean up config file."""
        print("[Ngrok] Stopping HTTP tunnel...")

        if self.http_process:
            try:
                self.http_process.terminate()
                # Wait up to 5 seconds for graceful shutdown
                for _ in range(10):
                    if self.http_process.poll() is not None:
                        break
                    await asyncio.sleep(0.5)

                # Force kill if still running
                if self.http_process.poll() is None:
                    self.http_process.kill()
                    await asyncio.sleep(0.5)

            except Exception as e:
                print(f"[Ngrok] Error stopping HTTP tunnel: {e}")

            self.http_process = None

        # Clean up temporary config file
        if self.http_config_file and Path(self.http_config_file).exists():
            try:
                Path(self.http_config_file).unlink()
                print(f"[Ngrok] Cleaned up config file: {self.http_config_file}")
            except Exception as e:
                print(f"[Ngrok] Warning: Could not delete config file: {e}")
            self.http_config_file = None

        self.http_tunnel_url = None
        print("[Ngrok] HTTP tunnel stopped")

    async def restart_tunnel(self) -> Optional[str]:
        """
        Restart the tunnel.

        Returns:
            New tunnel URL or None if failed
        """
        print("[Ngrok] Restarting tunnel...")
        await self.stop_tunnel()
        await asyncio.sleep(2)
        return await self.start_tunnel()

    async def restart_http_tunnel(self, port: int = 80) -> Optional[str]:
        """
        Restart the HTTP tunnel.

        Args:
            port: Local port to tunnel

        Returns:
            New tunnel URL or None if failed
        """
        print("[Ngrok] Restarting HTTP tunnel...")
        await self.stop_http_tunnel()
        await asyncio.sleep(2)
        return await self.start_http_tunnel(port)

    async def monitor_tunnel(self, check_interval: int = 30) -> None:
        """
        Monitor tunnel and restart if it goes down.

        Args:
            check_interval: How often to check tunnel status (seconds)
        """
        print(f"[Ngrok] Starting tunnel monitor (checking every {check_interval}s)")

        while True:
            try:
                await asyncio.sleep(check_interval)

                if not await self.is_tunnel_active():
                    print("[Ngrok] Tunnel is down, attempting restart...")
                    url = await self.restart_tunnel()

                    if url:
                        print(f"[Ngrok] Tunnel restarted successfully: {url}")
                    else:
                        print(f"[Ngrok] Failed to restart tunnel, will retry in {self.retry_delay}s")
                        await asyncio.sleep(self.retry_delay)

            except asyncio.CancelledError:
                print("[Ngrok] Monitor cancelled")
                break
            except Exception as e:
                print(f"[Ngrok] Monitor error: {e}")
                await asyncio.sleep(self.retry_delay)

    def get_ssh_command(self) -> Optional[str]:
        """
        Get SSH command string for connecting through tunnel.

        Returns:
            SSH command string (e.g., "ssh focus@X.tcp.ngrok.io -p XXXXX")
        """
        if not self.tunnel_url:
            return None

        try:
            # Parse tunnel URL: tcp://X.tcp.ngrok.io:XXXXX
            if self.tunnel_url.startswith("tcp://"):
                url_without_proto = self.tunnel_url[6:]  # Remove "tcp://"
                host, port = url_without_proto.rsplit(":", 1)
                return f"ssh focus@{host} -p {port}"

            return None

        except Exception:
            return None

    async def get_status(self) -> Dict[str, any]:
        """
        Get comprehensive tunnel status.

        Returns:
            Dictionary with tunnel status information
        """
        # SSH tunnel status
        active = await self.is_tunnel_active()
        url = await self.get_tunnel_url() if active else None
        ssh_cmd = self.get_ssh_command() if active else None

        # HTTP tunnel status
        http_active = await self.is_http_tunnel_active()
        http_url = await self.get_http_tunnel_url() if http_active else None

        return {
            "active": active,
            "tunnel_url": url,
            "ssh_command": ssh_cmd,
            "process_running": self.process is not None and self.process.poll() is None,
            "http_active": http_active,
            "http_tunnel_url": http_url,
            "http_process_running": self.http_process is not None and self.http_process.poll() is None,
        }

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.stop_tunnel()
        await self.stop_http_tunnel()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
