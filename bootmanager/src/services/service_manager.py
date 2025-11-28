"""Service manager for Focus server and frontend."""

import asyncio
import subprocess
import time
import requests
from typing import Optional, Dict
from pathlib import Path


class ServiceManager:
    """Manages Focus server (Flask) and frontend (Next.js) processes."""

    def __init__(
        self,
        server_path: str,
        frontend_path: str,
        server_port: int = 5001,
        frontend_port: int = 3000,
        frontend_dev_mode: bool = False
    ):
        """
        Initialize service manager.

        Args:
            server_path: Path to server directory
            frontend_path: Path to frontend directory
            server_port: Port for Flask server
            frontend_port: Port for Next.js frontend
            frontend_dev_mode: If True, run frontend in dev mode (hot reload)
        """
        self.server_path = Path(server_path)
        self.frontend_path = Path(frontend_path)
        self.server_port = server_port
        self.frontend_port = frontend_port
        self.frontend_dev_mode = frontend_dev_mode

        self.server_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None

        self.server_log_file = None
        self.frontend_log_file = None

    async def start_server(self) -> bool:
        """
        Start the Flask backend server.

        Returns:
            True if started successfully
        """
        try:
            print(f"[Services] Starting server from {self.server_path}...")

            # Check if venv exists
            venv_python = self.server_path / "venv" / "bin" / "python3"
            if not venv_python.exists():
                print(f"[Services] Server venv not found at {venv_python}")
                return False

            # Open log files
            self.server_log_file = open(
                self.server_path / "bootmanager_server.log", "a"
            )

            # Start server process
            self.server_process = subprocess.Popen(
                [str(venv_python), "run.py"],
                cwd=str(self.server_path),
                stdout=self.server_log_file,
                stderr=subprocess.STDOUT,
                env={**subprocess.os.environ, "PYTHONUNBUFFERED": "1"}
            )

            # Wait a moment and check if it's running
            await asyncio.sleep(3)

            if self.server_process.poll() is not None:
                print("[Services] Server process exited immediately")
                return False

            # Check health endpoint
            is_healthy = await self.check_server_health()
            if is_healthy:
                print(f"[Services] ✓ Server started (PID: {self.server_process.pid})")
                return True
            else:
                print("[Services] Server started but health check failed")
                return True  # Still return True as process is running

        except Exception as e:
            print(f"[Services] Error starting server: {e}")
            return False

    async def start_frontend(self) -> bool:
        """
        Start the Next.js frontend.

        Returns:
            True if started successfully
        """
        try:
            mode_str = "DEV" if self.frontend_dev_mode else "PRODUCTION"
            print(f"[Services] Starting frontend from {self.frontend_path} ({mode_str} mode)...")

            # Check if node_modules exists
            if not (self.frontend_path / "node_modules").exists():
                print("[Services] Frontend node_modules not found, run 'npm install' first")
                return False

            # Check if build exists (only required for production mode)
            if not self.frontend_dev_mode and not (self.frontend_path / ".next").exists():
                print("[Services] Frontend not built, run 'npm run build' first")
                return False

            # Open log files
            self.frontend_log_file = open(
                self.frontend_path / "bootmanager_frontend.log", "a"
            )

            # Start frontend process (dev or production mode)
            npm_command = ["npm", "run", "dev"] if self.frontend_dev_mode else ["npm", "start"]
            self.frontend_process = subprocess.Popen(
                npm_command,
                cwd=str(self.frontend_path),
                stdout=self.frontend_log_file,
                stderr=subprocess.STDOUT,
                env={**subprocess.os.environ}
            )

            # Wait a moment and check if it's running
            await asyncio.sleep(5)

            if self.frontend_process.poll() is not None:
                print("[Services] Frontend process exited immediately")
                return False

            # Check health endpoint
            is_healthy = await self.check_frontend_health()
            if is_healthy:
                print(f"[Services] ✓ Frontend started (PID: {self.frontend_process.pid})")
                return True
            else:
                print("[Services] Frontend started but health check failed")
                return True  # Still return True as process is running

        except Exception as e:
            print(f"[Services] Error starting frontend: {e}")
            return False

    async def stop_server(self) -> bool:
        """
        Stop the Flask backend server.

        Returns:
            True if stopped successfully
        """
        if not self.server_process:
            return True

        try:
            print("[Services] Stopping server...")
            self.server_process.terminate()

            # Wait for graceful shutdown
            for _ in range(10):
                if self.server_process.poll() is not None:
                    break
                await asyncio.sleep(0.5)

            # Force kill if still running
            if self.server_process.poll() is None:
                self.server_process.kill()
                await asyncio.sleep(0.5)

            if self.server_log_file:
                self.server_log_file.close()
                self.server_log_file = None

            self.server_process = None
            print("[Services] ✓ Server stopped")
            return True

        except Exception as e:
            print(f"[Services] Error stopping server: {e}")
            return False

    async def stop_frontend(self) -> bool:
        """
        Stop the Next.js frontend.

        Returns:
            True if stopped successfully
        """
        if not self.frontend_process:
            return True

        try:
            print("[Services] Stopping frontend...")
            self.frontend_process.terminate()

            # Wait for graceful shutdown
            for _ in range(10):
                if self.frontend_process.poll() is not None:
                    break
                await asyncio.sleep(0.5)

            # Force kill if still running
            if self.frontend_process.poll() is None:
                self.frontend_process.kill()
                await asyncio.sleep(0.5)

            if self.frontend_log_file:
                self.frontend_log_file.close()
                self.frontend_log_file = None

            self.frontend_process = None
            print("[Services] ✓ Frontend stopped")
            return True

        except Exception as e:
            print(f"[Services] Error stopping frontend: {e}")
            return False

    async def restart_server(self) -> bool:
        """
        Restart the Flask backend server.

        Returns:
            True if restarted successfully
        """
        await self.stop_server()
        await asyncio.sleep(2)
        return await self.start_server()

    async def restart_frontend(self) -> bool:
        """
        Restart the Next.js frontend.

        Returns:
            True if restarted successfully
        """
        await self.stop_frontend()
        await asyncio.sleep(2)
        return await self.start_frontend()

    async def check_server_health(self, max_attempts: int = 15, delay: float = 2.0) -> bool:
        """
        Check if server is healthy with retry logic.

        Args:
            max_attempts: Maximum number of health check attempts (default: 15)
            delay: Delay in seconds between attempts (default: 2.0)

        Returns:
            True if server is responding within max_attempts
        """
        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    f"http://localhost:{self.server_port}/health",
                    timeout=2
                )
                if response.status_code == 200:
                    if attempt > 0:
                        print(f"[Services] Server health check succeeded after {attempt + 1} attempts")
                    return True
            except Exception:
                pass

            # Don't sleep after the last attempt
            if attempt < max_attempts - 1:
                await asyncio.sleep(delay)

        return False

    async def check_frontend_health(self, max_attempts: int = 15, delay: float = 2.0) -> bool:
        """
        Check if frontend is healthy with retry logic.

        Args:
            max_attempts: Maximum number of health check attempts (default: 15)
            delay: Delay in seconds between attempts (default: 2.0)

        Returns:
            True if frontend is responding within max_attempts
        """
        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    f"http://localhost:{self.frontend_port}",
                    timeout=2
                )
                if response.status_code == 200:
                    if attempt > 0:
                        print(f"[Services] Frontend health check succeeded after {attempt + 1} attempts")
                    return True
            except Exception:
                pass

            # Don't sleep after the last attempt
            if attempt < max_attempts - 1:
                await asyncio.sleep(delay)

        return False

    def is_server_running(self) -> bool:
        """Check if server process is running."""
        return (
            self.server_process is not None
            and self.server_process.poll() is None
        )

    def is_frontend_running(self) -> bool:
        """Check if frontend process is running."""
        return (
            self.frontend_process is not None
            and self.frontend_process.poll() is None
        )

    async def get_status(self) -> Dict:
        """
        Get comprehensive service status.

        Returns:
            Dictionary with service status information
        """
        server_running = self.is_server_running()
        frontend_running = self.is_frontend_running()

        server_healthy = await self.check_server_health() if server_running else False
        frontend_healthy = await self.check_frontend_health() if frontend_running else False

        return {
            "server": {
                "running": server_running,
                "healthy": server_healthy,
                "url": f"http://localhost:{self.server_port}",
                "pid": self.server_process.pid if server_running else None,
            },
            "frontend": {
                "running": frontend_running,
                "healthy": frontend_healthy,
                "url": f"http://localhost:{self.frontend_port}",
                "pid": self.frontend_process.pid if frontend_running else None,
            },
        }

    def get_server_log_tail(self, lines: int = 30) -> str:
        """
        Get last N lines from server log.

        Args:
            lines: Number of lines to retrieve

        Returns:
            Log content
        """
        log_file = self.server_path / "bootmanager_server.log"
        if not log_file.exists():
            return "(no logs yet)"

        try:
            with open(log_file, "r") as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception as e:
            return f"(error reading logs: {e})"

    def get_frontend_log_tail(self, lines: int = 30) -> str:
        """
        Get last N lines from frontend log.

        Args:
            lines: Number of lines to retrieve

        Returns:
            Log content
        """
        log_file = self.frontend_path / "bootmanager_frontend.log"
        if not log_file.exists():
            return "(no logs yet)"

        try:
            with open(log_file, "r") as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception as e:
            return f"(error reading logs: {e})"

    async def cleanup(self) -> None:
        """Clean up all services."""
        await self.stop_server()
        await self.stop_frontend()


# Global service manager instance
_service_manager: Optional[ServiceManager] = None


def init_service_manager(
    server_path: str,
    frontend_path: str,
    server_port: int = 5001,
    frontend_port: int = 3000,
    frontend_dev_mode: bool = False
) -> ServiceManager:
    """
    Initialize and return global service manager instance.

    Args:
        server_path: Path to server directory
        frontend_path: Path to frontend directory
        server_port: Port for Flask server
        frontend_port: Port for Next.js frontend
        frontend_dev_mode: If True, run frontend in dev mode (hot reload)

    Returns:
        Initialized ServiceManager instance
    """
    global _service_manager
    _service_manager = ServiceManager(
        server_path, frontend_path, server_port, frontend_port, frontend_dev_mode
    )
    return _service_manager


def get_service_manager() -> ServiceManager:
    """
    Get the global service manager instance.

    Returns:
        ServiceManager instance

    Raises:
        RuntimeError: If service manager hasn't been initialized yet
    """
    if _service_manager is None:
        raise RuntimeError("Service manager not initialized. Call init_service_manager() first.")
    return _service_manager
