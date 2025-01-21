"""Storage manager for handling temporary file storage and cleanup."""
import os
import time
import threading
import logging
from typing import Optional
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import current_app

class StorageManager:
    """Manages temporary file storage with automatic cleanup."""
    
    def __init__(self):
        """Initialize the storage manager."""
        self._file_registry = {}  # Tracks file upload times
        self._lock = threading.Lock()  # Thread-safe operations
        self._cleanup_thread = None
        self._running = False
        self.logger = logging.getLogger(__name__)
    
    # PUBLIC_INTERFACE
    def start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        if not self._cleanup_thread:
            self._running = True
            self._cleanup_thread = threading.Thread(target=self._cleanup_task, daemon=True)
            self._cleanup_thread.start()
            self.logger.info("Cleanup task started")
    
    # PUBLIC_INTERFACE
    def stop_cleanup_task(self) -> None:
        """Stop the background cleanup task."""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join()
            self._cleanup_thread = None
            self.logger.info("Cleanup task stopped")
    
    # PUBLIC_INTERFACE
    def store_file(self, file_data, filename: str) -> Optional[str]:
        """
        Store a file in the temporary storage.
        
        Args:
            file_data: File data to store
            filename: Original filename
            
        Returns:
            str: Stored filename if successful, None otherwise
        """
        try:
            filename = secure_filename(filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            
            with self._lock:
                file_data.save(filepath)
                self._file_registry[filename] = datetime.now()
                self.logger.info(f"File stored: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Error storing file {filename}: {str(e)}")
            return None
    
    # PUBLIC_INTERFACE
    def get_file(self, filename: str) -> Optional[str]:
        """
        Get the full path of a stored file.
        
        Args:
            filename: Name of the file to retrieve
            
        Returns:
            str: Full file path if exists, None otherwise
        """
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            return filepath
        return None
    
    # PUBLIC_INTERFACE
    def delete_file(self, filename: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            with self._lock:
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    self._file_registry.pop(filename, None)
                    self.logger.info(f"File deleted: {filename}")
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Error deleting file {filename}: {str(e)}")
            return False
    
    def _cleanup_task(self) -> None:
        """Background task to clean up old files."""
        while self._running:
            try:
                self._cleanup_old_files()
                time.sleep(current_app.config['CLEANUP_INTERVAL'])
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {str(e)}")
                time.sleep(60)  # Wait before retrying
    
    def _cleanup_old_files(self) -> None:
        """Remove files that exceed the maximum age."""
        current_time = datetime.now()
        max_age = timedelta(seconds=current_app.config['MAX_FILE_AGE'])
        
        with self._lock:
            for filename, upload_time in list(self._file_registry.items()):
                if current_time - upload_time > max_age:
                    self.delete_file(filename)

# Global instance
storage_manager = StorageManager()