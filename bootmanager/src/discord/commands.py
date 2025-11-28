"""Discord command handler and processor."""

import asyncio
import psutil
import sys
from typing import Optional, Tuple
from pathlib import Path

from .job_manager import get_job_manager
from ..utils.process_runner import ProcessRunner
from ..network.wifi_manager import WiFiManager
from ..network.tunnel_manager import TunnelManager
from ..services import get_service_manager

# Add shared module to path for LED client
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))
try:
    from led_manager.led_manager_client import LEDManagerClient
    LED_CLIENT_AVAILABLE = True
except ImportError:
    LED_CLIENT_AVAILABLE = False


class CommandHandler:
    """Handles Discord command parsing and execution."""

    def __init__(
        self,
        wifi_manager: WiFiManager,
        tunnel_manager: TunnelManager,
        service_manager=None
    ):
        """
        Initialize command handler.

        Args:
            wifi_manager: WiFiManager instance
            tunnel_manager: TunnelManager instance
            service_manager: ServiceManager instance (optional)
        """
        self.wifi_manager = wifi_manager
        self.tunnel_manager = tunnel_manager
        self.service_manager = service_manager
        self.job_manager = get_job_manager()

        # Initialize LED client
        self.led_client = None
        if LED_CLIENT_AVAILABLE:
            try:
                self.led_client = LEDManagerClient()
            except Exception as e:
                print(f"[Discord] Warning: Could not initialize LED client: {e}")

    async def handle_command(self, message_content: str) -> str:
        """
        Parse and execute a command from Discord.

        Args:
            message_content: Full message content (including ! prefix)

        Returns:
            Response string to send back to Discord
        """
        # Remove the ! prefix
        if not message_content.startswith("!"):
            return "Invalid command format. Commands must start with !"

        command = message_content[1:].strip()

        # Parse command and arguments
        parts = command.split(maxsplit=1)
        cmd_name = parts[0].lower() if parts else ""
        cmd_args = parts[1] if len(parts) > 1 else ""

        # Route to appropriate handler
        if cmd_name == "ps":
            return await self.cmd_ps()
        elif cmd_name == "tail":
            return await self.cmd_tail(cmd_args)
        elif cmd_name == "stop":
            return await self.cmd_stop(cmd_args)
        elif cmd_name == "status":
            return await self.cmd_status()
        elif cmd_name == "services":
            return await self.cmd_services()
        elif cmd_name == "urls":
            return await self.cmd_urls()
        elif cmd_name == "restart-server":
            return await self.cmd_restart_server()
        elif cmd_name == "restart-frontend":
            return await self.cmd_restart_frontend()
        elif cmd_name == "logs-server":
            return await self.cmd_logs_server(cmd_args)
        elif cmd_name == "logs-frontend":
            return await self.cmd_logs_frontend(cmd_args)
        elif cmd_name == "reboot":
            return await self.cmd_reboot()
        elif cmd_name == "help":
            return self.cmd_help()
        elif cmd_name == "subway":
            return await self.cmd_subway()
        elif cmd_name == "brainrot":
            return await self.cmd_brainrot()
        elif cmd_name == "neuille":
            return await self.cmd_neuille()
        else:
            # Execute as shell command
            return await self.cmd_execute(command)

    async def cmd_execute(self, command: str) -> str:
        """
        Execute a shell command as a background job.

        Args:
            command: Shell command to execute

        Returns:
            Response message with job ID and initial output
        """
        try:
            # Start job
            job = await self.job_manager.start_job(command)

            # Wait for initial output
            initial_output = await self.job_manager.wait_for_initial_output(
                job.id,
                wait_seconds=5,
                tail_lines=20
            )

            # Check if job completed quickly
            self.job_manager._update_job_statuses()
            job_status = job.status

            status_icon = "✅" if job_status == "completed" else "🔄"
            status_text = "Terminé" if job_status == "completed" else "En cours"

            response = (
                f"🔧 **Commande exécutée** [`{job.id}`]\n"
                f"```bash\n$ {command}\n```\n"
                f"📤 **Sortie (5s):**\n"
                f"```\n{initial_output[:1500]}\n```\n"
                f"📊 Statut : {status_icon} {status_text}\n"
                f"💡 Utilisez `!tail {job.id}` pour voir la suite"
            )

            return response

        except ValueError as e:
            # Command was blacklisted
            return f"❌ **Commande bloquée**\n```\n{str(e)}\n```"
        except Exception as e:
            return f"❌ **Erreur lors de l'exécution**\n```\n{str(e)}\n```"

    async def cmd_ps(self) -> str:
        """
        List all active jobs.

        Returns:
            Formatted list of jobs
        """
        jobs = self.job_manager.list_jobs()

        if not jobs:
            return "📋 **Aucun job actif**"

        running_jobs = [j for j in jobs if j.status == 'running']

        if not running_jobs:
            return "📋 **Aucun job en cours d'exécution**"

        response = f"📋 **Jobs actifs ({len(running_jobs)}):**\n"
        response += "━━━━━━━━━━━━━━━━━━━━━━\n"

        for job in running_jobs[:10]:  # Limit to 10 jobs
            # Truncate command if too long
            cmd_display = job.command[:50] + "..." if len(job.command) > 50 else job.command

            response += (
                f"**ID:** `{job.id}`\n"
                f"**Cmd:** `{cmd_display}`\n"
                f"**Statut:** {job.status.upper()}\n"
                f"**Uptime:** {job.get_uptime_str()}\n"
                f"\n"
            )

        if len(running_jobs) > 10:
            response += f"\n... et {len(running_jobs) - 10} autres jobs"

        return response

    async def cmd_tail(self, args: str) -> str:
        """
        Show log output from a job.

        Args:
            args: Job ID and optional line count (e.g., "a3f7b21c 50")

        Returns:
            Job log output
        """
        if not args:
            return "❌ **Usage:** `!tail <job_id> [lignes]`"

        parts = args.split()
        job_id = parts[0]
        num_lines = int(parts[1]) if len(parts) > 1 else 30

        job = self.job_manager.get_job(job_id)

        if not job:
            return f"❌ **Job `{job_id}` introuvable**"

        output = self.job_manager.get_job_output(job_id, tail_lines=num_lines)

        if not output:
            output = "(aucune sortie)"

        # Truncate if too long for Discord
        if len(output) > 1800:
            output = output[-1800:] + "\n... (tronqué)"

        response = (
            f"📜 **Logs du job `{job.id}`** ({num_lines} dernières lignes)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"```\n{output}\n```"
        )

        return response

    async def cmd_stop(self, args: str) -> str:
        """
        Stop a running job.

        Args:
            args: Job ID

        Returns:
            Confirmation message
        """
        if not args:
            return "❌ **Usage:** `!stop <job_id>`"

        job_id = args.strip()
        job = self.job_manager.get_job(job_id)

        if not job:
            return f"❌ **Job `{job_id}` introuvable**"

        if job.status != 'running':
            return f"ℹ️ **Job `{job_id}` n'est pas en cours d'exécution** (statut: {job.status})"

        success = await self.job_manager.stop_job(job_id)

        if success:
            return f"🛑 **Job `{job_id}` terminé avec succès**"
        else:
            return f"❌ **Erreur lors de l'arrêt du job `{job_id}`**"

    async def cmd_status(self) -> str:
        """
        Show system status.

        Returns:
            System status information
        """
        # Get Wi-Fi status
        wifi_status = await self.wifi_manager.get_status()

        # Get tunnel status
        tunnel_status = await self.tunnel_manager.get_status()

        # Get job stats
        job_stats = self.job_manager.get_job_stats()

        # Get system info
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = psutil.boot_time()
        uptime_seconds = int(psutil.time.time() - boot_time)

        # Format uptime
        uptime_hours = uptime_seconds // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60

        response = (
            "📊 **État du système**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🌐 **Réseau:**\n"
            f"  • Wi-Fi: {'✅ Connecté' if wifi_status['connected'] else '❌ Déconnecté'}\n"
            f"  • IP locale: {wifi_status['ip_address'] or 'N/A'}\n"
            f"  • Tunnel SSH: {'✅ Actif' if tunnel_status['active'] else '❌ Inactif'}\n"
        )

        if tunnel_status['active']:
            response += f"  • SSH: `{tunnel_status['ssh_command']}`\n"

        # Add HTTP tunnel status
        if tunnel_status.get('http_active'):
            response += f"  • Site web public: ✅ Actif\n"
            response += f"  • URL: `{tunnel_status.get('http_tunnel_url', 'N/A')}`\n"
        else:
            response += f"  • Site web public: ❌ Inactif\n"

        response += (
            f"\n💻 **Système:**\n"
            f"  • CPU: {cpu_percent}%\n"
            f"  • RAM: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)\n"
            f"  • Disque: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)\n"
            f"  • Uptime: {uptime_hours}h {uptime_minutes}m\n"
            f"\n📋 **Jobs:**\n"
            f"  • Total: {job_stats['total']}\n"
            f"  • En cours: {job_stats['running']}\n"
            f"  • Terminés: {job_stats['completed']}\n"
            f"  • Arrêtés: {job_stats['killed']}\n"
        )

        return response

    async def cmd_services(self) -> str:
        """
        Show detailed service status.

        Returns:
            Service status information
        """
        if not self.service_manager:
            return "❌ **Service manager non disponible**"

        try:
            status = await self.service_manager.get_status()

            server_icon = "✅" if status["server"]["healthy"] else ("🔄" if status["server"]["running"] else "❌")
            frontend_icon = "✅" if status["frontend"]["healthy"] else ("🔄" if status["frontend"]["running"] else "❌")

            response = (
                "🔧 **Focus Services**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"**Backend Server:**\n"
                f"  • Status: {server_icon} {'Healthy' if status['server']['healthy'] else ('Running' if status['server']['running'] else 'Stopped')}\n"
                f"  • URL: `{status['server']['url']}`\n"
            )

            if status["server"]["pid"]:
                response += f"  • PID: {status['server']['pid']}\n"

            response += (
                f"\n**Frontend:**\n"
                f"  • Status: {frontend_icon} {'Healthy' if status['frontend']['healthy'] else ('Running' if status['frontend']['running'] else 'Stopped')}\n"
                f"  • URL: `{status['frontend']['url']}`\n"
            )

            if status["frontend"]["pid"]:
                response += f"  • PID: {status['frontend']['pid']}\n"

            response += "\n💡 Utilisez `!restart-server` ou `!restart-frontend` pour redémarrer"

            return response

        except Exception as e:
            return f"❌ **Erreur lors de la récupération du statut**\n```\n{str(e)}\n```"

    async def cmd_urls(self) -> str:
        """
        Show all access URLs.

        Returns:
            URLs for SSH, frontend, and backend
        """
        tunnel_status = await self.tunnel_manager.get_status()
        wifi_status = await self.wifi_manager.get_status()

        response = (
            "🌐 **URLs d'accès**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        # Public website URL
        if tunnel_status.get("http_active") and tunnel_status.get("http_tunnel_url"):
            response += (
                f"🌍 **Site web public (protégé):**\n"
                f"`{tunnel_status['http_tunnel_url']}`\n\n"
            )

        # SSH access
        if tunnel_status["active"]:
            response += f"**SSH:**\n`{tunnel_status['ssh_command']}`\n\n"

        # Local IP
        response += f"**IP locale:** `{wifi_status['ip_address'] or 'N/A'}`\n\n"

        # Local service URLs
        if self.service_manager:
            status = await self.service_manager.get_status()
            response += (
                f"**Backend API (local):**\n"
                f"`{status['server']['url']}`\n\n"
                f"**Frontend (local):**\n"
                f"`{status['frontend']['url']}`\n"
            )

        return response

    async def cmd_restart_server(self) -> str:
        """
        Restart the backend server.

        Returns:
            Confirmation message
        """
        if not self.service_manager:
            return "❌ **Service manager non disponible**"

        try:
            await self.service_manager.restart_server()
            return "🔄 **Backend server redémarré avec succès**"
        except Exception as e:
            return f"❌ **Erreur lors du redémarrage du serveur**\n```\n{str(e)}\n```"

    async def cmd_restart_frontend(self) -> str:
        """
        Restart the frontend.

        Returns:
            Confirmation message
        """
        if not self.service_manager:
            return "❌ **Service manager non disponible**"

        try:
            await self.service_manager.restart_frontend()
            return "🔄 **Frontend redémarré avec succès**"
        except Exception as e:
            return f"❌ **Erreur lors du redémarrage du frontend**\n```\n{str(e)}\n```"

    async def cmd_logs_server(self, args: str) -> str:
        """
        Show server logs.

        Args:
            args: Number of lines (optional)

        Returns:
            Server log output
        """
        if not self.service_manager:
            return "❌ **Service manager non disponible**"

        try:
            lines = int(args) if args.strip() else 30
            logs = self.service_manager.get_server_log_tail(lines)

            if len(logs) > 1800:
                logs = logs[-1800:] + "\n... (tronqué)"

            return (
                f"📜 **Server Logs** ({lines} dernières lignes)\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"```\n{logs}\n```"
            )
        except Exception as e:
            return f"❌ **Erreur lors de la lecture des logs**\n```\n{str(e)}\n```"

    async def cmd_logs_frontend(self, args: str) -> str:
        """
        Show frontend logs.

        Args:
            args: Number of lines (optional)

        Returns:
            Frontend log output
        """
        if not self.service_manager:
            return "❌ **Service manager non disponible**"

        try:
            lines = int(args) if args.strip() else 30
            logs = self.service_manager.get_frontend_log_tail(lines)

            if len(logs) > 1800:
                logs = logs[-1800:] + "\n... (tronqué)"

            return (
                f"📜 **Frontend Logs** ({lines} dernières lignes)\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"```\n{logs}\n```"
            )
        except Exception as e:
            return f"❌ **Erreur lors de la lecture des logs**\n```\n{str(e)}\n```"

    async def cmd_reboot(self) -> str:
        """
        Reboot the Raspberry Pi.

        Returns:
            Confirmation message
        """
        return (
            "🔄 **Redémarrage du Raspberry Pi**\n"
            "⚠️ Cette commande redémarre le système dans 10 secondes.\n"
            "Utilisez `sudo reboot` directement pour confirmer."
        )
        # Note: Actual reboot would be:
        # asyncio.create_task(self._delayed_reboot())

    async def _delayed_reboot(self) -> None:
        """Execute delayed reboot (10 seconds)."""
        await asyncio.sleep(10)
        await ProcessRunner.run("sudo reboot")

    async def cmd_subway(self) -> str:
        """
        Display subway GIF on LED matrix.

        Returns:
            Confirmation message
        """
        if not self.led_client:
            return "❌ **LED matrix non disponible**"

        try:
            self.led_client.show_gif("subway", loop=True)
            return "🚇 **Subway GIF** en cours d'affichage sur la matrice LED"
        except Exception as e:
            return f"❌ **Erreur LED**: {str(e)}"

    async def cmd_brainrot(self) -> str:
        """
        Display brainrot GIF on LED matrix.

        Returns:
            Confirmation message
        """
        if not self.led_client:
            return "❌ **LED matrix non disponible**"

        try:
            self.led_client.show_gif("brainrot", loop=True)
            return "🧠 **Brainrot GIF** en cours d'affichage sur la matrice LED"
        except Exception as e:
            return f"❌ **Erreur LED**: {str(e)}"

    async def cmd_neuille(self) -> str:
        """
        Display couad GIF on LED matrix.

        Returns:
            Confirmation message
        """
        if not self.led_client:
            return "❌ **LED matrix non disponible**"

        try:
            self.led_client.show_gif("couad", loop=True)
            return "🎬 **Neuille GIF** en cours d'affichage sur la matrice LED"
        except Exception as e:
            return f"❌ **Erreur LED**: {str(e)}"

    def cmd_help(self) -> str:
        """
        Show help message.

        Returns:
            Help text
        """
        return (
            "📖 **Commandes disponibles**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "**Système:**\n"
            "`!status` — Affiche l'état du système\n"
            "`!reboot` — Redémarre le Raspberry Pi\n"
            "`!urls` — Affiche toutes les URLs d'accès\n"
            "\n**Services Focus:**\n"
            "`!services` — Affiche l'état des services\n"
            "`!restart-server` — Redémarre le backend\n"
            "`!restart-frontend` — Redémarre le frontend\n"
            "`!logs-server [n]` — Logs du serveur\n"
            "`!logs-frontend [n]` — Logs du frontend\n"
            "\n**Jobs:**\n"
            "`!<cmd>` — Exécute une commande shell\n"
            "`!ps` — Liste tous les jobs actifs\n"
            "`!tail <id> [n]` — Affiche les n dernières lignes d'un job\n"
            "`!stop <id>` — Termine un job en cours\n"
            "\n**LED Matrix:**\n"
            "`!subway` — Affiche le GIF subway sur la matrice LED\n"
            "`!brainrot` — Affiche le GIF brainrot sur la matrice LED\n"
            "`!neuille` — Affiche le GIF couad sur la matrice LED\n"
            "\n**Exemples:**\n"
            "```\n"
            "!services\n"
            "!urls\n"
            "!logs-server 50\n"
            "!restart-frontend\n"
            "!ps\n"
            "!python3 script.py\n"
            "```"
        )
