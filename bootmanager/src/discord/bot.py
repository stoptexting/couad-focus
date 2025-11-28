"""Discord bot for remote command execution."""

import discord
from discord.ext import commands
from typing import Optional
import asyncio
import ssl
import aiohttp

from .commands import CommandHandler
from ..network.wifi_manager import WiFiManager
from ..network.tunnel_manager import TunnelManager


class BootManagerBot:
    """Discord bot for Raspberry Pi Boot Manager."""

    def __init__(
        self,
        token: str,
        channel_id: int,
        wifi_manager: WiFiManager,
        tunnel_manager: TunnelManager,
        service_manager=None
    ):
        """
        Initialize Discord bot.

        Args:
            token: Discord bot token
            channel_id: Discord channel ID for command execution
            wifi_manager: WiFiManager instance
            tunnel_manager: TunnelManager instance
            service_manager: ServiceManager instance (optional)
        """
        self.token = token
        self.channel_id = channel_id
        self.wifi_manager = wifi_manager
        self.tunnel_manager = tunnel_manager
        self.service_manager = service_manager

        # Set up bot with required intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for reading message content
        intents.messages = True

        # TEMPORARY FIX: Disable SSL verification for Discord connection
        # This is a workaround for Raspberry Pi SSL certificate issues
        # TODO: Fix SSL certificates properly in the Python environment
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Create aiohttp connector with disabled SSL verification
        connector = aiohttp.TCPConnector(ssl=ssl_context)

        self.client = discord.Client(intents=intents, connector=connector)
        self.command_handler = CommandHandler(wifi_manager, tunnel_manager, service_manager)

        # Set up event handlers
        self._setup_events()

    def _setup_events(self) -> None:
        """Set up Discord event handlers."""

        @self.client.event
        async def on_ready():
            """Called when bot is connected and ready."""
            print(f"[Discord] Bot connected as {self.client.user}")
            print(f"[Discord] Listening on channel ID: {self.channel_id}")

        @self.client.event
        async def on_message(message):
            """
            Called when a message is received.

            Args:
                message: Discord message object
            """
            # Ignore messages from the bot itself
            if message.author == self.client.user:
                return

            # Only respond in configured channel
            if message.channel.id != self.channel_id:
                return

            # Only handle commands (messages starting with !)
            if not message.content.startswith("!"):
                return

            print(f"[Discord] Received command: {message.content}")

            # Process command
            try:
                response = await self.command_handler.handle_command(message.content)

                # Split response if too long for Discord (2000 char limit)
                if len(response) > 2000:
                    # Split into chunks
                    chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                    for chunk in chunks:
                        await message.channel.send(chunk)
                else:
                    await message.channel.send(response)

            except Exception as e:
                error_msg = f"❌ **Erreur lors du traitement de la commande**\n```\n{str(e)}\n```"
                await message.channel.send(error_msg)
                print(f"[Discord] Error processing command: {e}")

        @self.client.event
        async def on_error(event, *args, **kwargs):
            """
            Called when an error occurs.

            Args:
                event: Event name
            """
            print(f"[Discord] Error in event {event}")
            import traceback
            traceback.print_exc()

    async def send_message(self, message: str) -> bool:
        """
        Send a message to the configured channel.

        Args:
            message: Message to send

        Returns:
            True if sent successfully
        """
        try:
            channel = self.client.get_channel(self.channel_id)

            if channel:
                await channel.send(message)
                return True
            else:
                print(f"[Discord] Channel {self.channel_id} not found")
                return False

        except Exception as e:
            print(f"[Discord] Error sending message: {e}")
            return False

    async def send_boot_notification(
        self,
        boot_time: float,
        local_ip: str,
        ssh_command: str,
        service_status: dict = None,
        http_tunnel_url: str = None,
        http_username: str = None
    ) -> None:
        """
        Send boot notification to Discord.

        Args:
            boot_time: Boot time in seconds
            local_ip: Local IP address
            ssh_command: SSH command string
            service_status: Service status dictionary (optional)
            http_tunnel_url: Public HTTP tunnel URL (optional)
            http_username: HTTP auth username (optional)
        """
        message = (
            "🚀 **Raspberry Pi Boot Manager - Ready**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📡 **Connexion SSH disponible :**\n"
            f"```\n{ssh_command}\n```\n"
            f"🌐 IP locale : {local_ip}\n"
        )

        # Add public website URL if available
        if http_tunnel_url:
            message += (
                f"\n🌍 **Site web public (protégé par mot de passe) :**\n"
                f"{http_tunnel_url}\n"
            )
            if http_username:
                message += f"👤 Username: `{http_username}`\n"

        # Add service information if available
        if service_status:
            server_icon = "✅" if service_status["server"]["healthy"] else ("🔄" if service_status["server"]["running"] else "❌")
            frontend_icon = "✅" if service_status["frontend"]["healthy"] else ("🔄" if service_status["frontend"]["running"] else "❌")

            message += (
                f"\n🎯 **Focus Task Manager :**\n"
                f"  • Backend: {server_icon} `{service_status['server']['url']}`\n"
                f"  • Frontend: {frontend_icon} `{service_status['frontend']['url']}`\n"
            )

        message += f"\n⏰ Boot time : {boot_time:.1f}s\n"
        message += "\n💡 Utilisez `!help` pour voir les commandes disponibles"

        await self.send_message(message)

    async def start(self) -> None:
        """Start the Discord bot."""
        print("[Discord] Starting bot...")

        try:
            await self.client.start(self.token)
        except discord.LoginFailure:
            print("[Discord] ERROR: Invalid token")
            raise
        except Exception as e:
            print(f"[Discord] Error starting bot: {e}")
            raise

    async def stop(self) -> None:
        """Stop the Discord bot."""
        print("[Discord] Stopping bot...")

        try:
            await self.client.close()
        except Exception as e:
            print(f"[Discord] Error stopping bot: {e}")

    def run(self) -> None:
        """
        Run the bot (blocking).

        Note: This is a blocking call. Use start() for async usage.
        """
        self.client.run(self.token)


# Global bot instance
_bot: Optional[BootManagerBot] = None


def init_bot(
    token: str,
    channel_id: int,
    wifi_manager: WiFiManager,
    tunnel_manager: TunnelManager,
    service_manager=None
) -> BootManagerBot:
    """
    Initialize and return global bot instance.

    Args:
        token: Discord bot token
        channel_id: Discord channel ID
        wifi_manager: WiFiManager instance
        tunnel_manager: TunnelManager instance
        service_manager: ServiceManager instance (optional)

    Returns:
        Initialized BootManagerBot instance
    """
    global _bot
    _bot = BootManagerBot(token, channel_id, wifi_manager, tunnel_manager, service_manager)
    return _bot


def get_bot() -> BootManagerBot:
    """
    Get the global bot instance.

    Returns:
        BootManagerBot instance

    Raises:
        RuntimeError: If bot hasn't been initialized yet
    """
    if _bot is None:
        raise RuntimeError("Bot not initialized. Call init_bot() first.")
    return _bot
