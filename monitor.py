import os
import time
import logging
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from config import MONITOR_SETTINGS

logger = logging.getLogger(__name__)

class FileUploadHandler(FileSystemEventHandler):
    def __init__(self, upload_callback: Callable, allowed_extensions: List[str]):
        self.upload_callback = upload_callback
        self.allowed_extensions = allowed_extensions
        self.processing_files: Dict[str, float] = {}
        self.cooldown = MONITOR_SETTINGS['cooldown_period']

    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        if not self._is_valid_file(file_path):
            return

        # Check if file is still being written
        if self._is_file_locked(file_path):
            return

        # Add to processing queue
        self.processing_files[file_path] = time.time()
        asyncio.create_task(self._process_file(file_path))

    def _is_valid_file(self, file_path: str) -> bool:
        """Check if file has allowed extension and meets size requirements."""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in self.allowed_extensions:
                return False

            size = os.path.getsize(file_path)
            if size < MONITOR_SETTINGS['min_file_size']:
                return False
            if size > MONITOR_SETTINGS['max_file_size']:
                logger.warning(f"File {file_path} exceeds maximum size limit")
                return False

            return True
        except Exception as e:
            logger.error(f"Error checking file validity: {str(e)}")
            return False

    def _is_file_locked(self, file_path: str) -> bool:
        """Check if file is still being written to."""
        try:
            if file_path in self.processing_files:
                last_check = self.processing_files[file_path]
                if time.time() - last_check < self.cooldown:
                    return True

            # Try to open file in exclusive mode
            with open(file_path, 'rb+') as f:
                return False
        except IOError:
            return True
        except Exception as e:
            logger.error(f"Error checking file lock: {str(e)}")
            return True

    async def _process_file(self, file_path: str):
        """Process file after cooldown period."""
        try:
            # Wait for cooldown period
            await asyncio.sleep(self.cooldown)

            # Check if file still exists and is valid
            if not os.path.exists(file_path) or not self._is_valid_file(file_path):
                return

            # Check if file is still being written
            if self._is_file_locked(file_path):
                return

            # Process file
            await self.upload_callback(file_path)

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
        finally:
            self.processing_files.pop(file_path, None)

class FileMonitor:
    def __init__(self, upload_callback: Callable, allowed_extensions: List[str]):
        self.observer = Observer()
        self.handler = FileUploadHandler(upload_callback, allowed_extensions)
        self.watched_paths: Dict[str, bool] = {}
        self.running = False

    def start(self):
        """Start the file monitor."""
        if self.running:
            return

        try:
            self.observer.start()
            self.running = True
            logger.info("File monitor started")
        except Exception as e:
            logger.error(f"Error starting file monitor: {str(e)}")
            raise

    def stop(self):
        """Stop the file monitor."""
        if not self.running:
            return

        try:
            self.observer.stop()
            self.observer.join()
            self.running = False
            logger.info("File monitor stopped")
        except Exception as e:
            logger.error(f"Error stopping file monitor: {str(e)}")
            raise

    def add_watch(self, path: str, recursive: bool = True):
        """Add a directory to watch."""
        try:
            if not os.path.exists(path):
                raise ValueError(f"Path does not exist: {path}")

            if not os.path.isdir(path):
                raise ValueError(f"Path is not a directory: {path}")

            if path in self.watched_paths:
                return

            self.observer.schedule(self.handler, path, recursive=recursive)
            self.watched_paths[path] = recursive
            logger.info(f"Added watch for path: {path} (recursive: {recursive})")
        except Exception as e:
            logger.error(f"Error adding watch for {path}: {str(e)}")
            raise

    def remove_watch(self, path: str):
        """Remove a directory from watch."""
        try:
            if path not in self.watched_paths:
                return

            for watch in self.observer.watches.copy():
                if watch.path == path:
                    self.observer.unschedule(watch)
                    break

            self.watched_paths.pop(path)
            logger.info(f"Removed watch for path: {path}")
        except Exception as e:
            logger.error(f"Error removing watch for {path}: {str(e)}")
            raise

    def get_watched_paths(self) -> Dict[str, bool]:
        """Get all watched paths and their recursive status."""
        return self.watched_paths.copy()

    def is_watching(self, path: str) -> bool:
        """Check if a path is being watched."""
        return path in self.watched_paths 