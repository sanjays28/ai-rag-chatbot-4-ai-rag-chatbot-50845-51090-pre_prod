"""RAG Model Monitoring Module

This module provides monitoring functionality for the RAG model, tracking:
1. Response generation times
2. Token usage
3. Memory and GPU usage
4. Embedding generation statistics
5. Context retrieval performance
"""
import time
import logging
import psutil
import torch
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class GenerationStats:
    """Statistics for response generation."""
    total_time: float
    tokens_generated: int
    tokens_per_second: float
    prompt_tokens: int
    total_tokens: int

@dataclass
class EmbeddingStats:
    """Statistics for embedding generation."""
    processing_time: float
    num_chunks: int
    avg_chunk_size: float
    total_embeddings: int

@dataclass
class RetrievalStats:
    """Statistics for context retrieval."""
    retrieval_time: float
    num_chunks_retrieved: int
    avg_similarity_score: float
    context_window_size: int

@dataclass
class ResourceStats:
    """System resource usage statistics."""
    cpu_percent: float
    memory_percent: float
    gpu_memory_allocated: Optional[float]
    gpu_memory_cached: Optional[float]

class RAGMonitor:
    """Monitor for tracking RAG model performance and resource usage."""
    
    def __init__(self, window_size: int = 100):
        """
        Initialize the RAG monitor.
        
        Args:
            window_size: Number of data points to keep in rolling windows
        """
        self.window_size = window_size
        self._generation_times = deque(maxlen=window_size)
        self._embedding_times = deque(maxlen=window_size)
        self._retrieval_times = deque(maxlen=window_size)
        self._token_counts = deque(maxlen=window_size)
        self._resource_stats = deque(maxlen=window_size)
        
        # Initialize counters
        self.total_queries = 0
        self.total_embeddings = 0
        self.total_tokens_generated = 0
        
        # Track current operation
        self.current_operation = None
        self.operation_start_time = None
    
    def start_operation(self, operation: str) -> None:
        """
        Start timing an operation.
        
        Args:
            operation: Name of the operation being timed
        """
        self.current_operation = operation
        self.operation_start_time = time.time()
    
    def end_operation(self) -> float:
        """
        End timing the current operation.
        
        Returns:
            float: Duration of the operation in seconds
        """
        if not self.operation_start_time:
            return 0.0
        
        duration = time.time() - self.operation_start_time
        self.operation_start_time = None
        self.current_operation = None
        return duration
    
    def record_generation_stats(self, stats: GenerationStats) -> None:
        """
        Record statistics for response generation.
        
        Args:
            stats: Generation statistics
        """
        self._generation_times.append(stats.total_time)
        self._token_counts.append(stats.tokens_generated)
        self.total_tokens_generated += stats.tokens_generated
        self.total_queries += 1
        
        logger.info(f"Generation stats: {asdict(stats)}")
    
    def record_embedding_stats(self, stats: EmbeddingStats) -> None:
        """
        Record statistics for embedding generation.
        
        Args:
            stats: Embedding statistics
        """
        self._embedding_times.append(stats.processing_time)
        self.total_embeddings += stats.total_embeddings
        
        logger.info(f"Embedding stats: {asdict(stats)}")
    
    def record_retrieval_stats(self, stats: RetrievalStats) -> None:
        """
        Record statistics for context retrieval.
        
        Args:
            stats: Retrieval statistics
        """
        self._retrieval_times.append(stats.retrieval_time)
        
        logger.info(f"Retrieval stats: {asdict(stats)}")
    
    def record_resource_usage(self) -> None:
        """Record current system resource usage."""
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        gpu_memory_allocated = None
        gpu_memory_cached = None
        
        if torch.cuda.is_available():
            gpu_memory_allocated = torch.cuda.memory_allocated() / (1024 ** 3)  # Convert to GB
            gpu_memory_cached = torch.cuda.memory_reserved() / (1024 ** 3)  # Convert to GB
        
        stats = ResourceStats(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            gpu_memory_allocated=gpu_memory_allocated,
            gpu_memory_cached=gpu_memory_cached
        )
        
        self._resource_stats.append(stats)
        logger.info(f"Resource stats: {asdict(stats)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive monitoring statistics.
        
        Returns:
            Dict containing all monitoring statistics
        """
        def safe_mean(data):
            return float(np.mean(data)) if data else 0.0
        
        def safe_percentile(data, p):
            return float(np.percentile(data, p)) if data else 0.0
        
        # Calculate statistics
        generation_stats = {
            "avg_generation_time": safe_mean(self._generation_times),
            "p95_generation_time": safe_percentile(self._generation_times, 95),
            "avg_tokens_per_query": safe_mean(self._token_counts),
            "total_tokens_generated": self.total_tokens_generated,
            "total_queries": self.total_queries
        }
        
        embedding_stats = {
            "avg_embedding_time": safe_mean(self._embedding_times),
            "p95_embedding_time": safe_percentile(self._embedding_times, 95),
            "total_embeddings": self.total_embeddings
        }
        
        retrieval_stats = {
            "avg_retrieval_time": safe_mean(self._retrieval_times),
            "p95_retrieval_time": safe_percentile(self._retrieval_times, 95)
        }
        
        # Get latest resource stats
        latest_resource_stats = self._resource_stats[-1] if self._resource_stats else ResourceStats(0, 0, None, None)
        resource_stats = asdict(latest_resource_stats)
        
        return {
            "generation": generation_stats,
            "embedding": embedding_stats,
            "retrieval": retrieval_stats,
            "resources": resource_stats,
            "current_operation": self.current_operation
        }

# Global monitor instance
_monitor = RAGMonitor()

# PUBLIC_INTERFACE
def get_monitor() -> RAGMonitor:
    """
    Get the global RAG monitor instance.
    
    Returns:
        RAGMonitor: Global monitor instance
    """
    return _monitor