"""PDF Processing Monitoring Module

This module provides functionality for monitoring PDF processing operations,
including upload success/failure rates, processing times, file sizes,
error tracking, and progress monitoring.
"""
import time
import logging
from typing import Dict, List, Any
from functools import wraps
import json
from dataclasses import dataclass, asdict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PDFProcessingMetrics:
    """Data class to store PDF processing metrics."""
    file_name: str
    file_size: int
    start_time: float
    processing_steps: Dict[str, float] = None
    status: str = "in_progress"
    error_type: str = None
    error_message: str = None

# Metrics storage
processing_metrics: Dict[str, PDFProcessingMetrics] = {}
upload_stats = {
    "success": 0,
    "failure": 0
}
error_types: Dict[str, int] = {}
file_size_stats = {
    "total_processed": 0,
    "avg_size": 0,
    "min_size": float('inf'),
    "max_size": 0
}

# PUBLIC_INTERFACE
def start_processing(file_name: str, file_size: int) -> str:
    """Start monitoring PDF processing for a file.
    
    Args:
        file_name: Name of the PDF file
        file_size: Size of the file in bytes
        
    Returns:
        str: Processing ID for tracking
    """
    processing_id = f"{file_name}_{int(time.time())}"
    processing_metrics[processing_id] = PDFProcessingMetrics(
        file_name=file_name,
        file_size=file_size,
        start_time=time.time(),
        processing_steps={}
    )
    return processing_id

# PUBLIC_INTERFACE
def record_step_time(processing_id: str, step_name: str):
    """Decorator to record time taken for each processing step.
    
    Args:
        processing_id: Processing ID from start_processing
        step_name: Name of the processing step
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                if processing_id in processing_metrics:
                    processing_metrics[processing_id].processing_steps[step_name] = time.time() - start_time
                return result
            except Exception as e:
                record_error(processing_id, type(e).__name__, str(e))
                raise
        return wrapper
    return decorator

# PUBLIC_INTERFACE
def complete_processing(processing_id: str, success: bool = True):
    """Mark PDF processing as complete and update statistics.
    
    Args:
        processing_id: Processing ID from start_processing
        success: Whether processing completed successfully
    """
    if processing_id not in processing_metrics:
        return
    
    metrics = processing_metrics[processing_id]
    metrics.status = "success" if success else "failed"
    
    # Update upload stats
    if success:
        upload_stats["success"] += 1
    else:
        upload_stats["failure"] += 1
    
    # Update file size stats
    file_size_stats["total_processed"] += 1
    file_size_stats["avg_size"] = (
        (file_size_stats["avg_size"] * (file_size_stats["total_processed"] - 1) + metrics.file_size)
        / file_size_stats["total_processed"]
    )
    file_size_stats["min_size"] = min(file_size_stats["min_size"], metrics.file_size)
    file_size_stats["max_size"] = max(file_size_stats["max_size"], metrics.file_size)
    
    # Log completion
    log_processing_details(processing_id)

# PUBLIC_INTERFACE
def record_error(processing_id: str, error_type: str, error_message: str):
    """Record an error that occurred during PDF processing.
    
    Args:
        processing_id: Processing ID from start_processing
        error_type: Type of error that occurred
        error_message: Detailed error message
    """
    if processing_id in processing_metrics:
        metrics = processing_metrics[processing_id]
        metrics.error_type = error_type
        metrics.error_message = error_message
        metrics.status = "failed"
        
        # Update error statistics
        error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Log error
        logger.error(f"PDF Processing Error - ID: {processing_id}, Type: {error_type}, Message: {error_message}")

# PUBLIC_INTERFACE
def get_processing_stats() -> Dict[str, Any]:
    """Get current PDF processing statistics.
    
    Returns:
        Dict containing processing statistics including:
        - Upload success/failure rates
        - Average processing times by step
        - File size statistics
        - Error type distribution
    """
    # Calculate average processing times
    step_times: Dict[str, List[float]] = {}
    for metrics in processing_metrics.values():
        for step, time_taken in metrics.processing_steps.items():
            if step not in step_times:
                step_times[step] = []
            step_times[step].append(time_taken)
    
    avg_step_times = {
        step: sum(times) / len(times)
        for step, times in step_times.items()
    }
    
    return {
        "upload_stats": upload_stats,
        "average_step_times": avg_step_times,
        "file_size_stats": file_size_stats,
        "error_distribution": error_types,
        "total_processed": file_size_stats["total_processed"]
    }

# PUBLIC_INTERFACE
def get_processing_progress(processing_id: str) -> Dict[str, Any]:
    """Get progress information for a specific processing job.
    
    Args:
        processing_id: Processing ID from start_processing
        
    Returns:
        Dict containing progress information including:
        - Current status
        - Completed steps
        - Time taken for each step
        - Errors if any
    """
    if processing_id not in processing_metrics:
        return {"error": "Processing ID not found"}
    
    metrics = processing_metrics[processing_id]
    return {
        "file_name": metrics.file_name,
        "status": metrics.status,
        "processing_steps": metrics.processing_steps,
        "total_time": time.time() - metrics.start_time if metrics.status == "in_progress" else None,
        "error": {
            "type": metrics.error_type,
            "message": metrics.error_message
        } if metrics.error_type else None
    }

def log_processing_details(processing_id: str):
    """Log details about the PDF processing operation.
    
    Args:
        processing_id: Processing ID from start_processing
    """
    if processing_id not in processing_metrics:
        return
        
    metrics = processing_metrics[processing_id]
    log_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "processing_id": processing_id,
        "file_name": metrics.file_name,
        "file_size": metrics.file_size,
        "status": metrics.status,
        "processing_steps": metrics.processing_steps,
        "total_time": time.time() - metrics.start_time,
        "error": {
            "type": metrics.error_type,
            "message": metrics.error_message
        } if metrics.error_type else None
    }
    logger.info(json.dumps(log_data))