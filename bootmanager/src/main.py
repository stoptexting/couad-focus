"""Main orchestrator for Raspberry Pi Boot Manager."""

import asyncio
import signal
import sys
import time
from pathlib import Path

from src.config import load_config, get_config
from src.utils.logger import setup_logger, get_logger
from src.led_client import init_led_client
from src.network.wifi_manager import WiFiManager
from src.network.tunnel_manager import TunnelManager
from src.discord.job_manager import init_job_manager
from src.discord.bot import init_bot
from src.services import init_service_manager, get_service_manager
from src.nginx_manager import init_nginx_manager


class BootManager:
    """Main orchestrator for the Raspberry Pi Boot Manager."""

    def __init__(self):
        """Initialize the boot manager."""
        self.config = None
        self.logger = None
        self.led = None
        self.wifi_manager = None
        self.tunnel_manager = None
        self.nginx_manager = None
        self.service_manager = None
        self.bot = None
        self.start_time = time.time()
        self.running = True

    def _led_safe(self, method_name: str, *args, **kwargs) -> None:
        """
        Safely call LED method if client is available.

        Args:
            method_name: Name of LED method to call
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        if self.led:
            try:
                method = getattr(self.led, method_name)
                method(*args, **kwargs)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"LED command failed: {e}")

    async def initialize(self) -> None:
        """Initialize all components."""
        print("=" * 60)
        print("🚀 Raspberry Pi Boot Manager")
        print("=" * 60)

        # Step 0: Pull latest code from git
        print("\n[0/11] Pulling latest code from git...")
        try:
            import subprocess
            result = subprocess.run(
                ["git", "pull"],
                cwd="/home/focus/focus",
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print(f"✓ Git pull successful: {result.stdout.strip()}")
            else:
                print(f"⚠ Git pull warning: {result.stderr.strip()}")
        except Exception as e:
            print(f"⚠ Git pull failed: {e}")
            print("⚠ Continuing with current code...")

        # Step 1: Load configuration
        print("\n[1/11] Loading configuration...")
        try:
            self.config = load_config()
            print(f"✓ Configuration loaded: {self.config}")
        except Exception as e:
            print(f"✗ Failed to load configuration: {e}")
            sys.exit(1)

        # Step 2: Initialize logger
        print("\n[2/11] Initializing logger...")
        try:
            self.logger = setup_logger(
                name="bootmanager",
                log_dir=self.config.log_dir
            )
            self.logger.info("Raspberry Pi Boot Manager starting...")
            print(f"✓ Logger initialized (log_dir: {self.config.log_dir})")
        except Exception as e:
            print(f"✗ Failed to initialize logger: {e}")
            sys.exit(1)

        # Step 3: Initialize LED client (connects to LED manager daemon)
        print("\n[3/11] Connecting to LED manager...")
        try:
            self.led = init_led_client()
            # Show connection test first to verify LED panel communication
            self._led_safe('show_connected_test')
            await asyncio.sleep(3)  # Keep CONNECTED message visible for 3 seconds
            # Then show boot animation
            self._led_safe('show_boot')
            self.logger.info("LED manager client connected")
            print("✓ LED manager client connected")
        except Exception as e:
            self.logger.warning(f"LED manager connection failed: {e}")
            print(f"⚠ LED manager connection failed: {e}")
            print("⚠ LED features will be unavailable")
            self.led = None

        # Step 4: Connect to Wi-Fi
        print("\n[4/11] Connecting to Wi-Fi...")
        try:
            self._led_safe('show_wifi_searching')
            self.wifi_manager = WiFiManager(
                retry_attempts=self.config.wifi_retry_attempts,
                retry_delay=self.config.wifi_retry_delay
            )

            success = await self.wifi_manager.connect(
                self.config.wifi_ssid,
                self.config.wifi_password
            )

            if not success:
                self.logger.error("Failed to connect to Wi-Fi")
                self._led_safe('show_wifi_error')
                print("✗ Wi-Fi connection failed")
                sys.exit(1)

            ip_address = await self.wifi_manager.get_ip_address()
            self._led_safe('show_wifi_connected')
            self.logger.info(f"Connected to Wi-Fi: {self.config.wifi_ssid} (IP: {ip_address})")
            print(f"✓ Connected to Wi-Fi (IP: {ip_address})")

        except Exception as e:
            self.logger.error(f"Wi-Fi connection error: {e}")
            self._led_safe('show_wifi_error')
            print(f"✗ Wi-Fi error: {e}")
            sys.exit(1)

        # Step 5: Query emergency SSH tunnel (managed by ngrok-ssh.service)
        print("\n[5/11] Querying emergency SSH tunnel...")
        try:
            self._led_safe('show_tunnel_active')
            self.tunnel_manager = TunnelManager(
                auth_token=self.config.ngrok_auth_token,
                retry_delay=self.config.ngrok_retry_delay,
                http_username=self.config.ngrok_http_username,
                http_password=self.config.ngrok_http_password
            )

            tunnel_url = await self.tunnel_manager.get_existing_ssh_tunnel()

            if not tunnel_url:
                self.logger.warning("Emergency SSH tunnel not found")
                print("⚠ Emergency SSH tunnel not available")
                print("⚠ ngrok-ssh.service may not be running - continuing anyway")
                print("⚠ You may need to manually check SSH access")
            else:
                ssh_command = self.tunnel_manager.get_ssh_command()
                self.logger.info(f"Emergency SSH tunnel found: {ssh_command}")
                print(f"✓ Emergency SSH tunnel found")
                print(f"  SSH: {ssh_command}")

        except Exception as e:
            self.logger.warning(f"Error querying emergency tunnel: {e}")
            print(f"⚠ Tunnel query error: {e}")
            print("⚠ Continuing without SSH tunnel access")

        # Step 6: Initialize job manager
        print("\n[6/11] Initializing job manager...")
        try:
            job_manager = init_job_manager(self.config.cmdruns_dir)
            self.logger.info("Job manager initialized")
            print(f"✓ Job manager initialized (log_dir: {self.config.cmdruns_dir})")
        except Exception as e:
            self.logger.error(f"Job manager initialization error: {e}")
            print(f"✗ Job manager error: {e}")
            sys.exit(1)

        # Step 7: Initialize service manager
        print("\n[7/11] Initializing service manager...")
        try:
            self.service_manager = init_service_manager(
                server_path=str(self.config.server_path),
                frontend_path=str(self.config.frontend_path),
                server_port=self.config.server_port,
                frontend_port=self.config.frontend_port,
                frontend_dev_mode=self.config.frontend_dev_mode
            )
            self.logger.info("Service manager initialized")
            print("✓ Service manager initialized")
        except Exception as e:
            self.logger.error(f"Service manager initialization error: {e}")
            print(f"✗ Service manager error: {e}")
            sys.exit(1)

        # Step 8: Start Focus backend server
        print("\n[8/11] Starting Focus backend server...")
        try:
            server_started = await self.service_manager.start_server()
            if not server_started:
                self.logger.warning("Failed to start server (may need to build first)")
                print("⚠ Server failed to start - continuing anyway")
            else:
                self.logger.info(f"Server started on port {self.config.server_port}")
                print(f"✓ Server started (http://localhost:{self.config.server_port})")
        except Exception as e:
            self.logger.warning(f"Server start error: {e}")
            print(f"⚠ Server error: {e}")

        # Step 9: Start Focus frontend
        print("\n[9/11] Starting Focus frontend...")
        try:
            frontend_started = await self.service_manager.start_frontend()
            if not frontend_started:
                self.logger.warning("Failed to start frontend (may need to build first)")
                print("⚠ Frontend failed to start - continuing anyway")
            else:
                self.logger.info(f"Frontend started on port {self.config.frontend_port}")
                print(f"✓ Frontend started (http://localhost:{self.config.frontend_port})")
        except Exception as e:
            self.logger.warning(f"Frontend start error: {e}")
            print(f"⚠ Frontend error: {e}")

        # Step 10: Set up nginx reverse proxy
        print("\n[10/11] Setting up nginx reverse proxy...")
        try:
            self.nginx_manager = init_nginx_manager(
                server_port=self.config.server_port,
                frontend_port=self.config.frontend_port
            )

            # Setup nginx configuration
            nginx_setup = await self.nginx_manager.setup()
            if not nginx_setup:
                self.logger.warning("Nginx setup failed - HTTP tunnel will not work")
                print("⚠ Nginx setup failed - continuing without HTTP tunnel")
            else:
                # Start nginx
                nginx_started = await self.nginx_manager.start()
                if nginx_started:
                    self.logger.info("Nginx reverse proxy started")
                    print("✓ Nginx reverse proxy started")

                    # Start HTTP tunnel through nginx
                    print("\n[10.5/11] Starting ngrok HTTP tunnel...")
                    http_tunnel_url = await self.tunnel_manager.start_http_tunnel(port=80)

                    if http_tunnel_url:
                        self.logger.info(f"HTTP tunnel started: {http_tunnel_url}")
                        print(f"✓ HTTP tunnel started")
                        print(f"  Public URL: {http_tunnel_url}")
                        print(f"  Username: {self.config.ngrok_http_username}")
                    else:
                        self.logger.warning("HTTP tunnel failed to start")
                        print("⚠ HTTP tunnel failed to start")
                else:
                    self.logger.warning("Nginx failed to start")
                    print("⚠ Nginx failed to start - continuing without HTTP tunnel")
        except Exception as e:
            self.logger.warning(f"Nginx/HTTP tunnel error: {e}")
            print(f"⚠ Nginx/HTTP tunnel error: {e}")

        # Step 11: Start Discord bot
        print("\n[11/11] Starting Discord bot...")
        try:
            self.bot = init_bot(
                token=self.config.discord_bot_token,
                channel_id=self.config.discord_channel_id,
                wifi_manager=self.wifi_manager,
                tunnel_manager=self.tunnel_manager,
                service_manager=self.service_manager
            )

            # Start bot in background
            asyncio.create_task(self.bot.start())

            # Wait for bot to be ready
            await asyncio.sleep(3)

            self._led_safe('show_discord_active')
            self.logger.info("Discord bot started")
            print("✓ Discord bot started")

        except Exception as e:
            self.logger.error(f"Discord bot error: {e}")
            print(f"✗ Discord bot error: {e}")
            sys.exit(1)

        # Calculate boot time
        boot_time = time.time() - self.start_time
        self.logger.info(f"System ready in {boot_time:.1f}s")

        # Send boot notification to Discord
        print("\n✓ All services initialized, sending boot notification to Discord...")
        try:
            await asyncio.sleep(2)  # Ensure bot is fully connected

            ip_address = await self.wifi_manager.get_ip_address()
            ssh_command = self.tunnel_manager.get_ssh_command()

            # Get service status
            service_status = await self.service_manager.get_status()

            # Get HTTP tunnel URL
            http_tunnel_url = await self.tunnel_manager.get_http_tunnel_url()

            await self.bot.send_boot_notification(
                boot_time=boot_time,
                local_ip=ip_address or "N/A",
                ssh_command=ssh_command or "N/A",
                service_status=service_status,
                http_tunnel_url=http_tunnel_url,
                http_username=self.config.ngrok_http_username if http_tunnel_url else None
            )

            print("✓ Boot notification sent")

        except Exception as e:
            self.logger.warning(f"Failed to send boot notification: {e}")
            print(f"⚠ Boot notification failed: {e}")

        print("\n" + "=" * 60)
        print("✅ SYSTEM READY")
        print("=" * 60)
        print(f"Boot time: {boot_time:.1f}s")
        print(f"SSH: {ssh_command}")
        print(f"Server: http://localhost:{self.config.server_port}")
        print(f"Frontend: http://localhost:{self.config.frontend_port}")
        print("=" * 60)

        # Show idle animation - DISABLED to prevent conflicts with gauge display
        # self._led_safe('show_idle')

    async def monitor_loop(self) -> None:
        """Main monitoring loop to check system health."""
        check_interval = 60  # Check every 60 seconds

        while self.running:
            try:
                await asyncio.sleep(check_interval)

                # Check Wi-Fi connection
                if not await self.wifi_manager.is_connected():
                    self.logger.warning("Wi-Fi disconnected, attempting reconnect...")
                    self._led_safe('show_wifi_searching')

                    success = await self.wifi_manager.connect(
                        self.config.wifi_ssid,
                        self.config.wifi_password
                    )

                    if success:
                        self.logger.info("Wi-Fi reconnected")
                        # Idle animation disabled to prevent LED conflicts
                        # self._led_safe('show_idle')
                    else:
                        self.logger.error("Wi-Fi reconnection failed")
                        self._led_safe('show_wifi_error')

                # Note: SSH tunnel is managed by ngrok-ssh.service (emergency tunnel)
                # We don't restart it here - systemd handles that automatically
                # Just log if it's down
                if not await self.tunnel_manager.is_tunnel_active():
                    self.logger.warning("Emergency SSH tunnel appears to be down")
                    self.logger.warning("Check ngrok-ssh.service: sudo systemctl status ngrok-ssh")

                # Check HTTP tunnel
                if self.nginx_manager and await self.nginx_manager.is_running():
                    if not await self.tunnel_manager.is_http_tunnel_active():
                        self.logger.warning("Ngrok HTTP tunnel down, attempting restart...")

                        url = await self.tunnel_manager.restart_http_tunnel(port=80)

                        if url:
                            self.logger.info(f"Ngrok HTTP tunnel restarted: {url}")
                        else:
                            self.logger.error("Ngrok HTTP tunnel restart failed")

                # Check services
                if self.service_manager:
                    service_status = await self.service_manager.get_status()

                    # Restart server if not running
                    if not service_status["server"]["running"]:
                        self.logger.warning("Server stopped, attempting restart...")
                        await self.service_manager.start_server()

                    # Restart frontend if not running
                    if not service_status["frontend"]["running"]:
                        self.logger.warning("Frontend stopped, attempting restart...")
                        await self.service_manager.start_frontend()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")

    async def shutdown(self) -> None:
        """Gracefully shutdown all components."""
        print("\n🛑 Shutting down...")
        if self.logger:
            self.logger.info("Shutting down...")

        self.running = False

        # Stop Discord bot
        if self.bot:
            try:
                await self.bot.stop()
                if self.logger:
                    self.logger.info("Discord bot stopped")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error stopping Discord bot: {e}")

        # Stop services
        if self.service_manager:
            try:
                await self.service_manager.cleanup()
                if self.logger:
                    self.logger.info("Services stopped")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error stopping services: {e}")

        # Stop tunnels
        if self.tunnel_manager:
            try:
                await self.tunnel_manager.stop_tunnel()
                await self.tunnel_manager.stop_http_tunnel()
                if self.logger:
                    self.logger.info("Ngrok tunnels stopped")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error stopping tunnels: {e}")

        # Stop nginx
        if self.nginx_manager:
            try:
                await self.nginx_manager.stop()
                if self.logger:
                    self.logger.info("Nginx stopped")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error stopping nginx: {e}")

        # Clean up LED
        self._led_safe('clear')
        if self.led:
            if self.logger:
                self.logger.info("LED cleared")

        if self.logger:
            self.logger.info("Shutdown complete")
        print("✓ Shutdown complete")

    async def run(self) -> None:
        """Run the boot manager."""
        # Set up signal handlers
        loop = asyncio.get_event_loop()

        def signal_handler():
            asyncio.create_task(self.shutdown())

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

        # Initialize
        await self.initialize()

        # Run monitoring loop
        await self.monitor_loop()


async def main() -> None:
    """Main entry point."""
    manager = BootManager()

    try:
        await manager.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await manager.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
