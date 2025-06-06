import os
import time
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from config import SCHEDULE_FORMAT

logger = logging.getLogger(__name__)

class UploadScheduler:
    def __init__(self):
        self.scheduled_tasks: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self._task = None
        
    async def start(self):
        """Start the scheduler."""
        if not self.running:
            self.running = True
            self._task = asyncio.create_task(self._run_scheduler())
            logger.info("Upload scheduler started")
            
    async def stop(self):
        """Stop the scheduler."""
        if self.running:
            self.running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            logger.info("Upload scheduler stopped")
            
    async def _run_scheduler(self):
        """Run the scheduler loop."""
        while self.running:
            try:
                current_time = datetime.now()
                tasks_to_run = []
                
                # Check for tasks to run
                for task_id, task in list(self.scheduled_tasks.items()):
                    if task['scheduled_time'] <= current_time:
                        tasks_to_run.append((task_id, task))
                        
                # Run tasks
                for task_id, task in tasks_to_run:
                    try:
                        await task['callback'](*task['args'], **task['kwargs'])
                        del self.scheduled_tasks[task_id]
                        logger.info(f"Scheduled task {task_id} completed")
                    except Exception as e:
                        logger.error(f"Scheduled task {task_id} failed: {str(e)}")
                        
                # Sleep for a short time
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                await asyncio.sleep(5)
                
    def schedule_upload(
        self,
        task_id: str,
        scheduled_time: datetime,
        callback: Callable,
        *args,
        **kwargs
    ) -> bool:
        """
        Schedule a file upload.
        
        Args:
            task_id: Unique task identifier
            scheduled_time: Time to run the task
            callback: Function to call
            *args: Arguments for callback
            **kwargs: Keyword arguments for callback
            
        Returns:
            bool: True if task scheduled successfully
        """
        try:
            if task_id in self.scheduled_tasks:
                raise ValueError(f"Task {task_id} already exists")
                
            self.scheduled_tasks[task_id] = {
                'scheduled_time': scheduled_time,
                'callback': callback,
                'args': args,
                'kwargs': kwargs
            }
            logger.info(f"Task {task_id} scheduled for {scheduled_time}")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule task {task_id}: {str(e)}")
            return False
            
    def cancel_upload(self, task_id: str) -> bool:
        """
        Cancel a scheduled upload.
        
        Args:
            task_id: Task identifier to cancel
            
        Returns:
            bool: True if task cancelled successfully
        """
        try:
            if task_id not in self.scheduled_tasks:
                raise ValueError(f"Task {task_id} not found")
                
            del self.scheduled_tasks[task_id]
            logger.info(f"Task {task_id} cancelled")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {str(e)}")
            return False
            
    def get_scheduled_uploads(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all scheduled uploads.
        
        Returns:
            Dict[str, Dict[str, Any]]: Scheduled uploads
        """
        return self.scheduled_tasks
        
    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a scheduled task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Task information
        """
        return self.scheduled_tasks.get(task_id)

# Create global scheduler instance
scheduler = UploadScheduler() 