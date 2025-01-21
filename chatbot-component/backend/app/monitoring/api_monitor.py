"""API Monitoring Module

This module provides functionality for monitoring API requests, timing, errors,
and usage statistics using Prometheus metrics.
"""
import time
from functools import wraps
from flask import request, g, Response
import logging
import json
from typing import Dict, List, Any
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

ERROR_COUNT = Counter(
    'http_request_errors_total',
    'Total HTTP request errors',
    ['error_type']
)

# Metrics storage for legacy support
request_times: List[float] = []
endpoint_stats: Dict[str, int] = {}
error_counts: Dict[str, int] = {}
status_codes: Dict[str, int] = {}

# PUBLIC_INTERFACE
def init_monitoring(app):
    """Initialize API monitoring for the Flask application with Prometheus metrics.
    
    Args:
        app: Flask application instance
    """
    @app.route('/metrics')
    def metrics():
        """Expose Prometheus metrics."""
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    @app.before_request
    def before_request():
        if request.path != '/metrics':  # Skip monitoring for metrics endpoint
            g.start_time = time.time()

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time') and request.path != '/metrics':
            duration = time.time() - g.start_time
            endpoint = f"{request.method} {request.endpoint}"
            status = str(response.status_code)
            
            # Update Prometheus metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.endpoint or 'root',
                status=status
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.endpoint or 'root'
            ).observe(duration)
            
            # Update legacy metrics
            request_times.append(duration)
            endpoint_stats[endpoint] = endpoint_stats.get(endpoint, 0) + 1
            status_codes[status] = status_codes.get(status, 0) + 1
            
            # Log request details
            log_request_details(duration, endpoint, status)
        
        return response

    @app.errorhandler(Exception)
    def handle_error(error):
        error_type = type(error).__name__
        
        # Update Prometheus metrics
        ERROR_COUNT.labels(error_type=error_type).inc()
        
        # Update legacy metrics
        error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        logger.error(f"Error occurred: {error_type} - {str(error)}")
        return {"error": str(error)}, 500

# PUBLIC_INTERFACE
def get_monitoring_stats() -> Dict[str, Any]:
    """Get current monitoring statistics.
    
    Returns:
        Dict containing monitoring statistics including:
        - Average response time
        - Endpoint usage counts
        - Error counts
        - Status code distribution
    """
    avg_time = sum(request_times) / len(request_times) if request_times else 0
    return {
        "average_response_time": round(avg_time, 3),
        "endpoint_stats": endpoint_stats,
        "error_counts": error_counts,
        "status_code_distribution": status_codes
    }

def log_request_details(duration: float, endpoint: str, status: str):
    """Log details about the request.
    
    Args:
        duration: Request processing time in seconds
        endpoint: The endpoint that was accessed
        status: HTTP status code of the response
    """
    log_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "method": request.method,
        "endpoint": endpoint,
        "status_code": status,
        "duration": round(duration, 3),
        "ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", "Unknown")
    }
    logger.info(json.dumps(log_data))
