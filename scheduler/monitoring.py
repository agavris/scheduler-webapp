"""
Monitoring and performance tracking for the scheduler application.
"""
import time
import logging
import functools
import psutil
import json
from datetime import datetime
from django.conf import settings
from django.db import connection

# Configure logger
logger = logging.getLogger('scheduler.monitoring')

class PerformanceMetrics:
    """Class to track and report performance metrics for the application."""
    
    @staticmethod
    def measure_execution_time(func):
        """
        Decorator to measure function execution time.
        
        Args:
            func: The function to measure
            
        Returns:
            The wrapped function with timing
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log the execution time
            logger.info(
                f"PERFORMANCE: Function '{func.__name__}' executed in {execution_time:.4f} seconds"
            )
            
            # If the result is a dict, add the execution time
            if isinstance(result, dict):
                result['execution_time'] = execution_time
                
            return result
        return wrapper
    
    @staticmethod
    def get_system_metrics():
        """
        Get current system metrics.
        
        Returns:
            dict: System metrics including CPU, memory, and disk usage
        """
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'percent': cpu_percent,
                'cores': psutil.cpu_count()
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            }
        }
        
        return metrics
    
    @staticmethod
    def log_db_queries():
        """Log the number and time of database queries in the current request."""
        total_time = sum(float(query.get('time', 0)) for query in connection.queries)
        num_queries = len(connection.queries)
        
        logger.info(
            f"PERFORMANCE: Database queries - Count: {num_queries}, "
            f"Total time: {total_time:.4f} seconds"
        )
        
        if settings.DEBUG:
            for i, query in enumerate(connection.queries):
                logger.debug(f"Query {i}: {query['sql']} - Time: {query['time']}")
    
    @staticmethod
    def track_scheduler_performance(schedule_data):
        """
        Track and log scheduler performance metrics.
        
        Args:
            schedule_data (dict): Results from the scheduler
            
        Returns:
            dict: The input data with added performance metrics
        """
        try:
            # Add system metrics
            schedule_data['system_metrics'] = PerformanceMetrics.get_system_metrics()
            
            # Calculate statistical metrics
            perfect_count = schedule_data.get('perfect_count', 0)
            partial_count = schedule_data.get('partial_count', 0)
            unsatisfied_count = schedule_data.get('unsatisfied_count', 0)
            total_students = perfect_count + partial_count + unsatisfied_count
            
            if total_students > 0:
                schedule_data['satisfaction_rate'] = (perfect_count + (partial_count * 0.5)) / total_students
            else:
                schedule_data['satisfaction_rate'] = 0
                
            # Log performance data
            logger.info(
                f"SCHEDULER PERFORMANCE: "
                f"Execution time: {schedule_data.get('execution_time', 0):.4f} seconds, "
                f"Satisfaction rate: {schedule_data['satisfaction_rate']:.2%}, "
                f"Students: {total_students}"
            )
            
            return schedule_data
        except Exception as e:
            logger.error(f"Error tracking scheduler performance: {str(e)}")
            return schedule_data
