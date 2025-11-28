"""Job manager for tracking and managing background processes."""

import uuid
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass

from ..utils.process_runner import ProcessRunner


@dataclass
class Job:
    """Represents a background job/process."""

    id: str
    command: str
    process: subprocess.Popen
    log_file: Path
    start_time: datetime
    status: str  # 'running', 'completed', 'killed'

    def get_uptime_seconds(self) -> int:
        """Get job uptime in seconds."""
        return int((datetime.now() - self.start_time).total_seconds())

    def get_uptime_str(self) -> str:
        """Get formatted uptime string (e.g., '2m 34s')."""
        seconds = self.get_uptime_seconds()

        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"


class JobManager:
    """Manages background jobs spawned from Discord commands."""

    def __init__(self, log_dir: Path):
        """
        Initialize job manager.

        Args:
            log_dir: Directory for storing job logs
        """
        self.log_dir = log_dir
        self.active_jobs: Dict[str, Job] = {}

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def generate_job_id(self) -> str:
        """
        Generate a unique job ID.

        Returns:
            8-character hexadecimal job ID
        """
        return uuid.uuid4().hex[:8]

    async def start_job(self, command: str) -> Job:
        """
        Start a new background job.

        Args:
            command: Command to execute

        Returns:
            Job object

        Raises:
            ValueError: If command is blacklisted
        """
        # Generate unique job ID
        job_id = self.generate_job_id()
        log_file = self.log_dir / f"{job_id}.log"

        print(f"[JobManager] Starting job {job_id}: {command}")

        # Start process
        process = await ProcessRunner.run_async(command, log_file)

        # Create job object
        job = Job(
            id=job_id,
            command=command,
            process=process,
            log_file=log_file,
            start_time=datetime.now(),
            status='running'
        )

        # Track job
        self.active_jobs[job_id] = job

        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job object or None if not found
        """
        return self.active_jobs.get(job_id)

    def list_jobs(self) -> List[Job]:
        """
        Get list of all tracked jobs.

        Returns:
            List of Job objects
        """
        # Update job statuses
        self._update_job_statuses()

        return list(self.active_jobs.values())

    def get_running_jobs(self) -> List[Job]:
        """
        Get list of currently running jobs.

        Returns:
            List of running Job objects
        """
        self._update_job_statuses()

        return [
            job for job in self.active_jobs.values()
            if job.status == 'running'
        ]

    def _update_job_statuses(self) -> None:
        """Update status of all jobs based on process state."""
        for job in self.active_jobs.values():
            if job.status == 'running':
                if not ProcessRunner.is_process_running(job.process):
                    job.status = 'completed'

    async def stop_job(self, job_id: str) -> bool:
        """
        Stop a running job.

        Args:
            job_id: Job identifier

        Returns:
            True if stopped successfully, False otherwise
        """
        job = self.get_job(job_id)

        if not job:
            print(f"[JobManager] Job {job_id} not found")
            return False

        if job.status != 'running':
            print(f"[JobManager] Job {job_id} is not running (status: {job.status})")
            return False

        print(f"[JobManager] Stopping job {job_id}")

        success = ProcessRunner.kill_process(job.process)

        if success:
            job.status = 'killed'
            print(f"[JobManager] Job {job_id} stopped")

        return success

    def get_job_output(
        self,
        job_id: str,
        tail_lines: Optional[int] = None
    ) -> Optional[str]:
        """
        Get output from job log file.

        Args:
            job_id: Job identifier
            tail_lines: If specified, return only last N lines

        Returns:
            Log contents or None if job not found
        """
        job = self.get_job(job_id)

        if not job:
            return None

        return ProcessRunner.read_log_file(job.log_file, tail_lines)

    async def wait_for_initial_output(
        self,
        job_id: str,
        wait_seconds: int = 5,
        tail_lines: int = 20
    ) -> str:
        """
        Wait for job to produce initial output.

        Args:
            job_id: Job identifier
            wait_seconds: How long to wait
            tail_lines: How many lines to return

        Returns:
            Initial output from job
        """
        await asyncio.sleep(wait_seconds)
        output = self.get_job_output(job_id, tail_lines=tail_lines)
        return output or "(no output yet)"

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> None:
        """
        Remove old completed/killed jobs from tracking.

        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        now = datetime.now()
        to_remove = []

        for job_id, job in self.active_jobs.items():
            if job.status in ['completed', 'killed']:
                age_hours = (now - job.start_time).total_seconds() / 3600

                if age_hours > max_age_hours:
                    to_remove.append(job_id)

        for job_id in to_remove:
            print(f"[JobManager] Cleaning up old job {job_id}")
            del self.active_jobs[job_id]

    def get_job_stats(self) -> Dict[str, int]:
        """
        Get statistics about jobs.

        Returns:
            Dictionary with job counts by status
        """
        self._update_job_statuses()

        stats = {
            'total': len(self.active_jobs),
            'running': 0,
            'completed': 0,
            'killed': 0
        }

        for job in self.active_jobs.values():
            if job.status in stats:
                stats[job.status] += 1

        return stats

    async def stop_all_jobs(self) -> int:
        """
        Stop all running jobs.

        Returns:
            Number of jobs stopped
        """
        running_jobs = self.get_running_jobs()
        stopped_count = 0

        for job in running_jobs:
            if await self.stop_job(job.id):
                stopped_count += 1

        return stopped_count


# Global job manager instance
_job_manager: Optional[JobManager] = None


def init_job_manager(log_dir: Path) -> JobManager:
    """
    Initialize and return global job manager instance.

    Args:
        log_dir: Directory for job logs

    Returns:
        Initialized JobManager instance
    """
    global _job_manager
    _job_manager = JobManager(log_dir)
    return _job_manager


def get_job_manager() -> JobManager:
    """
    Get the global job manager instance.

    Returns:
        JobManager instance

    Raises:
        RuntimeError: If job manager hasn't been initialized yet
    """
    if _job_manager is None:
        raise RuntimeError("Job manager not initialized. Call init_job_manager() first.")
    return _job_manager
