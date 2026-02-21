"""
Task manager for background processing.
Stores task status and results in-memory with TTL-based cleanup.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import threading
import logging

logger = logging.getLogger(__name__)

# In-memory storage for tasks
_background_tasks: Dict[str, Dict] = {}
_task_results: Dict[str, Dict] = {}
_lock = threading.Lock()

# Configuration
TASK_CLEANUP_TTL = 3600  # 1 hour in seconds


def cleanup_old_tasks() -> int:
    """
    Remove completed tasks older than TTL.
    
    Returns:
        Number of tasks cleaned up
    """
    with _lock:
        current_time = datetime.now()
        cleaned_count = 0
        
        for task_id in list(_task_results.keys()):
            task = _task_results[task_id]
            if 'completed_at' in task:
                age = (current_time - task['completed_at']).total_seconds()
                if age > TASK_CLEANUP_TTL:
                    del _task_results[task_id]
                    cleaned_count += 1
                    logger.info(f"Cleaned up old task: {task_id}")
        
        return cleaned_count


def create_task(task_id: str, total_items: int = 0, metadata: Optional[Dict] = None) -> None:
    """
    Create a new background task.
    
    Args:
        task_id: Unique identifier for the task
        total_items: Total number of items to process
        metadata: Optional metadata about the task
    """
    with _lock:
        _background_tasks[task_id] = {
            'status': 'processing',
            'progress': {
                'current': 0,
                'total': total_items,
                'percentage': 0
            },
            'created_at': datetime.now(),
            'metadata': metadata or {}
        }
        logger.info(f"Created task {task_id} with {total_items} items")


def update_task_progress(task_id: str, current: int, status: str = 'processing') -> None:
    """
    Update task progress.
    
    Args:
        task_id: Task identifier
        current: Current progress count
        status: Task status (processing, completed, error)
    """
    with _lock:
        if task_id in _background_tasks:
            task = _background_tasks[task_id]
            total = task['progress']['total']
            percentage = int((current / total * 100)) if total > 0 else 0
            
            task['progress']['current'] = current
            task['progress']['percentage'] = percentage
            task['status'] = status
            task['updated_at'] = datetime.now()


def complete_task(task_id: str, result: Dict[str, Any]) -> None:
    """
    Mark task as completed and store result.
    
    Args:
        task_id: Task identifier
        result: Task result data
    """
    with _lock:
        # Store result
        _task_results[task_id] = {
            'status': 'completed',
            'data': result,
            'completed_at': datetime.now()
        }
        
        # Remove from active tasks
        if task_id in _background_tasks:
            del _background_tasks[task_id]
        
        logger.info(f"Task {task_id} completed successfully")


def fail_task(task_id: str, error: str) -> None:
    """
    Mark task as failed with error message.
    
    Args:
        task_id: Task identifier
        error: Error message
    """
    with _lock:
        # Store error result
        _task_results[task_id] = {
            'status': 'error',
            'error': error,
            'completed_at': datetime.now()
        }
        
        # Remove from active tasks
        if task_id in _background_tasks:
            del _background_tasks[task_id]
        
        logger.error(f"Task {task_id} failed: {error}")


def get_task_status(task_id: str) -> Optional[Dict]:
    """
    Get current task status.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Task status dict or None if not found
    """
    with _lock:
        # Check if task is still processing
        if task_id in _background_tasks:
            task = _background_tasks[task_id]
            total = task['progress']['total']
            current = task['progress']['current']
            
            # Estimate remaining time (2-3 seconds per item)
            remaining_items = total - current
            estimated_seconds = remaining_items * 2.5
            
            return {
                'status': 'processing',
                'progress': task['progress'],
                'estimated_remaining': f"{int(estimated_seconds)} seconds",
                'metadata': task.get('metadata', {})
            }
        
        # Check if result is ready
        if task_id in _task_results:
            return _task_results[task_id]
        
        # Task not found
        return None


def get_active_task_count() -> int:
    """Get count of currently active tasks."""
    with _lock:
        return len(_background_tasks)


def get_completed_task_count() -> int:
    """Get count of completed/failed tasks in storage."""
    with _lock:
        return len(_task_results)
