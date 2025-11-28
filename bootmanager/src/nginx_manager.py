"""Nginx reverse proxy manager for Focus services."""

import asyncio
import subprocess
from pathlib import Path
from typing import Optional


class NginxManager:
    """Manages nginx reverse proxy for routing to services."""

    def __init__(self, server_port: int, frontend_port: int):
        """
        Initialize nginx manager.

        Args:
            server_port: Backend server port
            frontend_port: Frontend port
        """
        self.server_port = server_port
        self.frontend_port = frontend_port
        self.config_path = Path("/etc/nginx/sites-available/focus")
        self.config_link = Path("/etc/nginx/sites-enabled/focus")
        self.template_path = Path(__file__).parent.parent / "config" / "nginx.conf.template"
        self.nginx_running = False

    async def setup(self) -> bool:
        """
        Set up nginx configuration.

        Returns:
            True if setup successful
        """
        try:
            print("[Nginx] Setting up reverse proxy...")

            # Check if nginx is installed (check systemd service instead of which)
            result = await self._run_command("systemctl list-unit-files nginx.service")
            if not result or "nginx.service" not in result:
                print("[Nginx] ERROR: nginx not installed. Run install.sh first.")
                return False

            # Read template
            if not self.template_path.exists():
                print(f"[Nginx] ERROR: Template not found at {self.template_path}")
                return False

            template_content = self.template_path.read_text()

            # Replace placeholders
            nginx_config = template_content.replace("{{SERVER_PORT}}", str(self.server_port))
            nginx_config = nginx_config.replace("{{FRONTEND_PORT}}", str(self.frontend_port))

            # Write config to temporary file
            temp_config = Path("/tmp/focus-nginx.conf")
            temp_config.write_text(nginx_config)

            # Copy to nginx sites-available with sudo
            copy_cmd = f"sudo cp {temp_config} {self.config_path}"
            await self._run_command(copy_cmd)

            # Remove default nginx site if it exists
            await self._run_command("sudo rm -f /etc/nginx/sites-enabled/default")

            # Create symlink to sites-enabled
            await self._run_command(f"sudo ln -sf {self.config_path} {self.config_link}")

            # Test nginx configuration
            test_result = await self._run_command("sudo nginx -t")
            if test_result is None:
                print("[Nginx] ERROR: Configuration test failed")
                return False

            print("[Nginx] ✓ Configuration set up successfully")
            return True

        except Exception as e:
            print(f"[Nginx] Setup error: {e}")
            return False

    async def start(self) -> bool:
        """
        Start nginx service.

        Returns:
            True if started successfully
        """
        try:
            print("[Nginx] Starting service...")

            # Check if already running
            if await self.is_running():
                print("[Nginx] Already running, reloading configuration...")
                return await self.reload()

            # Start nginx
            result = await self._run_command("sudo systemctl start nginx")
            if result is None:
                print("[Nginx] ERROR: Failed to start nginx")
                return False

            # Enable nginx to start on boot
            await self._run_command("sudo systemctl enable nginx")

            # Verify it's running
            await asyncio.sleep(1)
            if await self.is_running():
                self.nginx_running = True
                print("[Nginx] ✓ Service started successfully")
                return True
            else:
                print("[Nginx] ERROR: Service failed to start")
                return False

        except Exception as e:
            print(f"[Nginx] Start error: {e}")
            return False

    async def stop(self) -> bool:
        """
        Stop nginx service.

        Returns:
            True if stopped successfully
        """
        try:
            print("[Nginx] Stopping service...")
            await self._run_command("sudo systemctl stop nginx")
            self.nginx_running = False
            print("[Nginx] ✓ Service stopped")
            return True

        except Exception as e:
            print(f"[Nginx] Stop error: {e}")
            return False

    async def reload(self) -> bool:
        """
        Reload nginx configuration.

        Returns:
            True if reloaded successfully
        """
        try:
            print("[Nginx] Reloading configuration...")
            result = await self._run_command("sudo systemctl reload nginx")
            if result is not None:
                print("[Nginx] ✓ Configuration reloaded")
                return True
            else:
                print("[Nginx] ERROR: Failed to reload")
                return False

        except Exception as e:
            print(f"[Nginx] Reload error: {e}")
            return False

    async def is_running(self) -> bool:
        """
        Check if nginx is running.

        Returns:
            True if nginx is active
        """
        try:
            result = await self._run_command("systemctl is-active nginx")
            return result is not None and "active" in result.lower()

        except Exception:
            return False

    async def get_status(self) -> dict:
        """
        Get nginx status.

        Returns:
            Status dictionary
        """
        running = await self.is_running()
        return {
            "running": running,
            "config_path": str(self.config_path),
            "proxy_port": 80,
        }

    async def cleanup(self) -> None:
        """Clean up nginx configuration."""
        try:
            # Remove config files
            await self._run_command(f"sudo rm -f {self.config_link}")
            await self._run_command(f"sudo rm -f {self.config_path}")

            # Stop nginx
            await self.stop()

        except Exception as e:
            print(f"[Nginx] Cleanup error: {e}")

    async def _run_command(self, command: str) -> Optional[str]:
        """
        Run a shell command.

        Args:
            command: Command to run

        Returns:
            Command output or None if failed
        """
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return stdout.decode().strip()
            else:
                return None

        except Exception as e:
            print(f"[Nginx] Command error: {e}")
            return None


# Global nginx manager instance
_nginx_manager: Optional[NginxManager] = None


def init_nginx_manager(server_port: int, frontend_port: int) -> NginxManager:
    """
    Initialize and return global nginx manager instance.

    Args:
        server_port: Backend server port
        frontend_port: Frontend port

    Returns:
        Initialized NginxManager instance
    """
    global _nginx_manager
    _nginx_manager = NginxManager(server_port, frontend_port)
    return _nginx_manager


def get_nginx_manager() -> NginxManager:
    """
    Get the global nginx manager instance.

    Returns:
        NginxManager instance

    Raises:
        RuntimeError: If nginx manager hasn't been initialized yet
    """
    if _nginx_manager is None:
        raise RuntimeError("Nginx manager not initialized. Call init_nginx_manager() first.")
    return _nginx_manager
