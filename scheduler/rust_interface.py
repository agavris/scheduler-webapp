import json
import os
import logging
from pathlib import Path
import importlib.util
from django.conf import settings

logger = logging.getLogger(__name__)

class RustSchedulerInterface:
    """Interface to the scheduler implementation.
    
    This class now defaults to using the OR-Tools implementation if available.
    """
    
    def __init__(self, compile_if_needed=False):
        """Initialize the interface
        
        Args:
            compile_if_needed: Ignored parameter (kept for backwards compatibility)
        """
        self.rust_module_path = Path(__file__).parent / 'rust_scheduler'
        self.rust_module = None
        
        # Try to import OR-Tools, fallback to Python implementation if unavailable
        try:
            from ortools.linear_solver import pywraplp
            self.using_python_impl = False
            logger.info("Using Google OR-Tools scheduler implementation")
        except ImportError:
            self.using_python_impl = True
            logger.info("OR-Tools not available, falling back to pure Python scheduler implementation")
    
    def compile_rust_module(self):
        """Compile the Rust module using maturin - now disabled"""
        logger.warning("Rust module compilation is disabled, using Python implementation")
        return False
    
    def run_scheduler(self, courses, students, config):
        """
        Run the scheduler algorithm with the given inputs
        
        Args:
            courses: List of course objects
            students: List of student objects
            config: Dict with configuration parameters
            
        Returns:
            Dict containing the schedule results
        """
        # Try to use OR-Tools implementation if available, otherwise fallback to Python
        if not self.using_python_impl:
            from .ortools_scheduler import ORToolsScheduler
            scheduler = ORToolsScheduler(courses, students)
            return scheduler.run_with_config(config)
        else:
            return self._run_python_scheduler(courses, students, config)
    
    def run_scheduler_parallel(self, courses, students, config, num_threads=4):
        """
        Run the scheduler algorithm in parallel for better results
        
        For OR-Tools, we increase the time limit to get a better solution.
        For Python implementation, we run multiple iterations with different seeds.
        
        Args:
            courses: List of course objects
            students: List of student objects
            config: Dict with configuration parameters
            num_threads: Number of runs to perform (or time multiplier for OR-Tools)
            
        Returns:
            Dict containing the best schedule results
        """
        if not self.using_python_impl:
            # For OR-Tools, we give it more time instead of multiple runs
            from .ortools_scheduler import ORToolsScheduler
            # Increase time limit based on num_threads parameter
            extended_config = config.copy()
            extended_config['time_limit_seconds'] = config.get('time_limit_seconds', 20) * (num_threads / 2)
            scheduler = ORToolsScheduler(courses, students)
            return scheduler.run_with_config(extended_config)
        else:
            # Fallback to Python implementation with multiple runs
            logger.warning("OR-Tools not available, using Python implementation with multiple runs")
            best_result = None
            best_score = float('inf')
            
            for _ in range(num_threads):
                result = self._run_python_scheduler(courses, students, config)
                
                # Check if this result is better than the current best
                if result and 'score' in result and result['score'] < best_score:
                    best_result = result
                    best_score = result['score']
            
            return best_result if best_result else self._run_python_scheduler(courses, students, config)
    
    def _prepare_courses_json(self, courses):
        """Convert Django course objects to the format expected by Rust"""
        rust_courses = []
        for course in courses:
            rust_courses.append({
                'name': course.name,
                'time_slot': course.time_slot,
                'max_students': course.max_students
            })
        return json.dumps(rust_courses)
    
    def _prepare_students_json(self, students):
        """Convert Django student objects to the format expected by Rust"""
        rust_students = []
        for i, student in enumerate(students):
            rust_students.append({
                'id': i,
                'email': student.email,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'grade': student.grade,
                'priority': student.priority,
                'am_preferences': student.get_am_preferences(),
                'pm_preferences': student.get_pm_preferences(),
                'am_course': student.am_course.name if student.am_course else None,
                'pm_course': student.pm_course.name if student.pm_course else None,
                'full_day_course': student.full_day_course.name if student.full_day_course else None
            })
        return json.dumps(rust_students)
    
    def _prepare_config_json(self, config):
        """Convert config dict to the format expected by Rust"""
        rust_config = {
            'iterations': config.get('iterations', 1000),
            'min_course_fill': config.get('min_course_fill', 0.75),
            'early_stop_score': config.get('early_stop_score', 0.0)
        }
        return json.dumps(rust_config)
    
    def _run_python_scheduler(self, courses, students, config):
        """Run the Python implementation of the scheduler"""
        from .scheduler_python import PythonScheduler
        
        # Make sure we only keep the best schedule
        config['save_only_best'] = True
        
        scheduler = PythonScheduler(courses, students)
        return scheduler.run_with_config(config)
