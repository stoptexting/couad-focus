"""Secure process execution utility with command sanitization."""

import asyncio
import subprocess
import re
from typing import Optional, Dict
from pathlib import Path


class ProcessRunner:
    """Secure command execution with blacklist filtering."""

    # Dangerous command patterns (case-insensitive)
    BLACKLISTED_PATTERNS = [
        r"rm\s+-rf\s+/",  # Delete root
        r"sudo\s+rm",  # Sudo remove
        r"dd\s+if=/dev/zero",  # Disk wipe
        r"dd\s+if=/dev/random",  # Disk wipe
        r"mkfs\.",  # Format filesystem
        r":\(\)\s*\{\s*:\|\:&\s*\}\s*;\s*:",  # Fork bomb
        r"chmod\s+-R\s+777\s+/",  # Dangerous permissions on root
        r">/dev/sd[a-z]",  # Write to raw disk
        r"shred",  # Secure delete
        r"wipefs",  # Wipe filesystem signatures
    ]

    @staticmethod
    def sanitize_command(command: str) -> bool:
        """
        Check if command is safe to execute.

        Args:
            command: Command to check

        Returns:
            True if safe, False if dangerous

        Raises:
            ValueError: If command matches a blacklisted pattern
        """
        command_lower = command.lower()

        for pattern in ProcessRunner.BLACKLISTED_PATTERNS:
            if re.search(pattern, command_lower):
                raise ValueError(
                    f"Command blocked: matches dangerous pattern '{pattern}'"
                )

        return True

    @staticmethod
    async def run(
        command: str,
        timeout: int = 300,
        cwd: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Run a command and capture output.

        Args:
            command: Command to execute
            timeout: Timeout in seconds (default 300 = 5 minutes)
            cwd: Working directory for command execution

        Returns:
            Dictionary with stdout, stderr, returncode, and success status

        Raises:
            ValueError: If command is blacklisted
        """
        # Sanitize command
        ProcessRunner.sanitize_command(command)

        try:
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )

            # Wait for completion with timeout
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                stdout = stdout_bytes.decode('utf-8', errors='replace')
                stderr = stderr_bytes.decode('utf-8', errors='replace')
                returncode = process.returncode

            except asyncio.TimeoutError:
                # Kill process on timeout
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass

                return {
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout} seconds",
                    "returncode": -1,
                    "success": False,
                    "timed_out": True
                }

            return {
                "stdout": stdout,
                "stderr": stderr,
                "returncode": returncode,
                "success": returncode == 0,
                "timed_out": False
            }

        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Error executing command: {str(e)}",
                "returncode": -1,
                "success": False,
                "timed_out": False
            }

    @staticmethod
    async def run_async(
        command: str,
        log_file: Path,
        cwd: Optional[str] = None
    ) -> subprocess.Popen:
        """
        Run a command asynchronously (background process) with output logged to file.

        Args:
            command: Command to execute
            log_file: Path to log file for output
            cwd: Working directory for command execution

        Returns:
            subprocess.Popen object

        Raises:
            ValueError: If command is blacklisted
        """
        # Sanitize command
        ProcessRunner.sanitize_command(command)

        # Ensure log file directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Open log file
        log_handle = open(log_file, "w")

        # Start process
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            cwd=cwd
        )

        return process

    @staticmethod
    def is_process_running(process: subprocess.Popen) -> bool:
        """
        Check if a process is still running.

        Args:
            process: subprocess.Popen object

        Returns:
            True if running, False otherwise
        """
        return process.poll() is None

    @staticmethod
    def kill_process(process: subprocess.Popen) -> bool:
        """
        Kill a running process.

        Args:
            process: subprocess.Popen object

        Returns:
            True if killed successfully, False otherwise
        """
        try:
            if ProcessRunner.is_process_running(process):
                process.terminate()

                # Wait up to 5 seconds for graceful termination
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if still running
                    process.kill()
                    process.wait()

                return True

            return False

        except Exception as e:
            print(f"[ProcessRunner] Error killing process: {e}")
            return False

    @staticmethod
    def read_log_file(log_file: Path, tail_lines: Optional[int] = None) -> str:
        """
        Read output from log file.

        Args:
            log_file: Path to log file
            tail_lines: If specified, return only last N lines

        Returns:
            Log file contents
        """
        try:
            if not log_file.exists():
                return ""

            with open(log_file, "r") as f:
                if tail_lines:
                    # Read last N lines
                    lines = f.readlines()
                    return "".join(lines[-tail_lines:])
                else:
                    # Read entire file
                    return f.read()

        except Exception as e:
            return f"Error reading log file: {e}"
