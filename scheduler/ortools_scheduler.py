"""
OR-Tools based scheduler implementation.
This should be significantly faster than the pure Python implementation.
"""
import logging
from typing import List, Dict, Optional, Tuple, Union
import time
import numpy as np
import random
from collections import defaultdict
from ortools.linear_solver import pywraplp
from .models import Course, Student, Section, Schedule, UserPreference

logger = logging.getLogger(__name__)

class ORToolsScheduler:
    """
    Google OR-Tools implementation of the scheduler algorithm.
    This uses a Mixed Integer Programming approach which should be much faster 
    than the random search method from the Python implementation.
    
    Advanced features:
    - Multiple optimization runs with best result selection
    - Custom priority weighting
    - Satisfaction threshold customization
    - Runtime parameter tuning
    """
    
    def __init__(self, courses, students):
        """
        Initialize the scheduler with courses and students
        
        Args:
            courses: List of Course objects
            students: List of Student objects
        """
        self.courses = courses
        self.students = students
        self.course_name_to_section = {}
        self.best_schedule = None
        self.all_schedules = []  # For multiple run optimization
        
        # Initialize sections for all courses
        self.load_sections()
    
    def load_sections(self):
        """Create a Section for each course"""
        for course in self.courses:
            # Create a section object if it doesn't exist
            if not hasattr(course, 'section'):
                section = Section(course=course)
                section.save()
            self.course_name_to_section[course.name] = course.section
    
    def run_with_config(self, config: Dict) -> Dict:
        """
        Run the scheduler with the given configuration using OR-Tools MIP solver
        
        Args:
            config: Dict with configuration parameters
            
        Returns:
            Dict: Schedule results
        """
        # Core configuration parameters
        iterations = config.get('iterations', 1000)
        min_course_fill = config.get('min_course_fill', 0.75)
        early_stop_score = config.get('early_stop_score', 0.0)
        
        # Advanced optimization options
        multiple_runs = config.get('multiple_runs', False)
        run_count = config.get('run_count', 3) if multiple_runs else 1
        priority_weight_mode = config.get('priority_weight', 'standard')
        
        # Custom priority weights (if provided)
        custom_weights = config.get('custom_weights', None)
        
        # Determine priority weights based on mode or custom settings
        priority_weights = self._get_priority_weights(priority_weight_mode, custom_weights)
        
        # Custom satisfaction thresholds (if provided)
        satisfaction_thresholds = config.get('satisfaction_thresholds', None)
        
        # Extract configuration
        time_limit_seconds = config.get('time_limit_seconds', 20)
        
        if multiple_runs:
            # Run the scheduler multiple times and pick the best result
            logger.info(f"Running scheduler {run_count} times with {priority_weight_mode} priority weights")
            best_score = float('inf')
            best_result = None
            self.all_schedules = []
            
            for run in range(run_count):
                # For each run, we shuffle students to get different results
                shuffled_students = list(self.students)
                random.shuffle(shuffled_students)
                self.students = shuffled_students
                
                # Run a single optimization
                result = self._run_single_optimization(time_limit_seconds, min_course_fill, priority_weights)
                
                # Store this result
                self.all_schedules.append({
                    'name': f"Run_{run+1}_{self.schedule_name}",
                    'score': self.schedule_score,
                    'assignments': self.student_assignments
                })
                
                # Keep track of the best result
                if self.schedule_score < best_score:
                    best_score = self.schedule_score
                    best_result = result
                    self.best_schedule = {
                        'name': f"Best_{self.schedule_name}",
                        'score': self.schedule_score,
                        'assignments': self.student_assignments
                    }
                
                logger.info(f"Run {run+1}/{run_count} completed with score {self.schedule_score:.4f}")
                
                # Check for early stopping
                if early_stop_score > 0 and self.schedule_score <= early_stop_score:
                    logger.info(f"Early stopping at run {run+1} with score {self.schedule_score:.4f}")
                    break
            
            # Return the best result from all runs
            return best_result
        else:
            # Just run once with the given configuration
            return self._run_single_optimization(time_limit_seconds, min_course_fill, priority_weights)
    
    def _get_priority_weights(self, mode='standard', custom_weights=None):
        """Get priority weights based on the selected mode or custom values
        
        Args:
            mode: The priority weight mode ('standard', 'strong', 'balanced')
            custom_weights: Optional dictionary with custom weights by priority level
            
        Returns:
            Dict: Mapping of priority level to weight value
        """
        if custom_weights:
            # Use custom weights provided by the user
            return custom_weights
        
        # Predefined weight schemes
        if mode == 'standard':
            # Standard priority weights - moderately prioritizes higher grades
            return {1: 1.0, 2: 0.8, 3: 0.6}
        elif mode == 'strong':
            # Strong priority weights - heavily prioritizes higher grades
            return {1: 1.0, 2: 0.6, 3: 0.3}
        elif mode == 'balanced':
            # Balanced priority weights - gives more equal chances
            return {1: 1.0, 2: 0.9, 3: 0.8}
        else:
            # Default to standard
            return {1: 1.0, 2: 0.8, 3: 0.6}
    
    def _run_single_optimization(self, time_limit_seconds, min_course_fill, priority_weights):
        """Run a single optimization process
        
        Args:
            time_limit_seconds: Time limit for the solver in seconds
            min_course_fill: Minimum course fill rate as a fraction
            priority_weights: Dictionary mapping priority levels to weights
            
        Returns:
            Dict: Optimization results
        """
        # Start timer
        start_time = time.time()
        logger.info("Starting OR-Tools scheduler")
        
        # Initialize the solver
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            logger.error("OR-Tools solver not available, falling back to Python implementation")
            from .scheduler_python import PythonScheduler
            fallback = PythonScheduler(self.courses, self.students)
            return fallback.run_with_config(config)
        
        # Set time limit
        solver.SetTimeLimit(time_limit_seconds * 1000)  # milliseconds
        
        # Create data structures
        # 1. Get all AM, PM and FullDay courses
        am_courses = [c for c in self.courses if c.time_slot == 'AM']
        pm_courses = [c for c in self.courses if c.time_slot == 'PM']
        fd_courses = [c for c in self.courses if c.time_slot == 'FullDay']
        
        # Create course indices for easy reference
        am_course_map = {c.id: i for i, c in enumerate(am_courses)}
        pm_course_map = {c.id: i for i, c in enumerate(pm_courses)}
        fd_course_map = {c.id: i for i, c in enumerate(fd_courses)}
        
        # Create preference matrices
        students_by_priority = {1: [], 2: [], 3: []}
        for student in self.students:
            students_by_priority[student.priority].append(student)
            
        # Create a unified list ordered by priority
        ordered_students = []
        for priority in [1, 2, 3]:
            ordered_students.extend(students_by_priority[priority])
        
        # Create decision variables for all students and courses
        # z[s][c] = 1 if student s is assigned to course c, 0 otherwise
        z = {}
        for s, student in enumerate(self.students):
            # Get student priority weight
            student_priority = student.priority
            priority_weight = priority_weights.get(student_priority, 1.0)
            
            z[s] = {}
            for c in self.courses:
                z[s][c.id] = solver.IntVar(0, 1, f'z_{s}_{c.id}')
                
        # y[s][c] = 1 if student s is assigned to PM course c
        y = {}
        for s, student in enumerate(ordered_students):
            y[s] = {}
            for c in pm_courses:
                y[s][c.id] = solver.IntVar(0, 1, f'y_{s}_{c.id}')
        
        # z[s][c] = 1 if student s is assigned to full-day course c
        z = {}
        for s, student in enumerate(ordered_students):
            z[s] = {}
            for c in fd_courses:
                z[s][c.id] = solver.IntVar(0, 1, f'z_{s}_{c.id}')
        
        # Create satisfaction penalty variables (higher priority = lower penalties)
        penalties = {}
        for s, student in enumerate(ordered_students):
            penalties[s] = solver.NumVar(0, solver.infinity(), f'penalty_{s}')
        
        # Add constraints
        
        # 1. Each student gets exactly one schedule type: AM+PM or FullDay
        for s, student in enumerate(ordered_students):
            # Sum of AM assignments
            am_sum = solver.Sum([x[s][c.id] for c in am_courses])
            # Sum of PM assignments
            pm_sum = solver.Sum([y[s][c.id] for c in pm_courses])
            # Sum of FD assignments
            fd_sum = solver.Sum([z[s][c.id] for c in fd_courses])
            
            # Student gets either (1 AM AND 1 PM) course OR 1 FD course
            solver.Add(am_sum == pm_sum)
            solver.Add(am_sum + fd_sum == 1)
        
        # 2. Course capacity constraints
        for c in am_courses:
            solver.Add(solver.Sum([x[s][c.id] for s in range(len(ordered_students))]) <= c.max_students)
            
        for c in pm_courses:
            solver.Add(solver.Sum([y[s][c.id] for s in range(len(ordered_students))]) <= c.max_students)
            
        for c in fd_courses:
            solver.Add(solver.Sum([z[s][c.id] for s in range(len(ordered_students))]) <= c.max_students)
        
        # 3. Calculate penalties based on preferences
        for s, student in enumerate(ordered_students):
            am_prefs = student.get_am_preferences()
            pm_prefs = student.get_pm_preferences()
            
            # Calculate AM penalty
            am_penalty = solver.Sum([
                x[s][c.id] * (0.0 if c.name in am_prefs else 0.5)  # 0.5 penalty for non-preference AM
                for c in am_courses
            ])
            
            # Calculate PM penalty
            pm_penalty = solver.Sum([
                y[s][c.id] * (0.0 if c.name in pm_prefs else 0.5)  # 0.5 penalty for non-preference PM
                for c in pm_courses
            ])
            
            # Calculate FD penalty (1.0 is higher because it replaces both AM+PM)
            fd_penalty = solver.Sum([
                z[s][c.id] * 1.0  # 1.0 penalty for any full day course
                for c in fd_courses
            ])
            
            # Set the total penalty for this student
            solver.Add(penalties[s] == am_penalty + pm_penalty + fd_penalty)
        
        # Setup objective - Priority weighted sum of penalties
        # Use customizable priority weights that were passed to the function
        # These weights determine how much influence each priority level has
        
        objective_terms = []
        for s, student in enumerate(ordered_students):
            # Get the weight for this student's priority level
            weight = priority_weights.get(student.priority, 1.0)
            
            # Priority 1 students (highest priority) should have higher weights
            # to ensure they get better satisfaction scores
            objective_terms.append(weight * penalties[s])
        
        solver.Minimize(solver.Sum(objective_terms))
        
        # Solve
        status = solver.Solve()
        
        # Process results
        if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
            logger.info(f"Solution found in {time.time() - start_time:.2f} seconds")
            
            # Clear all student enrollments
            for student in self.students:
                student.clear_enrollments()
            
            # Clear all sections
            for section_name, section in self.course_name_to_section.items():
                section.clear_students()
            
            # Apply the solution
            for s, student in enumerate(ordered_students):
                # Apply AM assignments
                for c in am_courses:
                    if x[s][c.id].solution_value() > 0.5:
                        section = c.section
                        section.add_student(student)
                
                # Apply PM assignments
                for c in pm_courses:
                    if y[s][c.id].solution_value() > 0.5:
                        section = c.section
                        section.add_student(student)
                
                # Apply Full Day assignments
                for c in fd_courses:
                    if z[s][c.id].solution_value() > 0.5:
                        section = c.section
                        section.add_student(student)
            
            # Calculate total score for the schedule
            # Normalize by number of students to keep scores low (between 0-1)
            student_scores = [student.satisfaction_score() for student in self.students]
            total_score = sum(student_scores) / len(self.students) if self.students else 0.0
            
            # Instead of creating a database entry, just store the calculated data
            self.schedule_name = f"ORTools_Schedule_{total_score:.2f}"
            self.schedule_score = total_score
            
            # Store student assignments for the result without creating database entries
            self.student_assignments = []
            for student in self.students:
                assignment = {
                    'student_id': student.id,
                    'student_name': f"{student.first_name} {student.last_name}",
                    'am_course': student.am_course.name if student.am_course else None,
                    'pm_course': student.pm_course.name if student.pm_course else None,
                    'full_day_course': student.full_day_course.name if student.full_day_course else None,
                    'satisfaction_score': student.satisfaction_score()
                }
                self.student_assignments.append(assignment)
            
            # Return result
            return self._format_result()
        else:
            logger.error("No solution found by OR-Tools solver")
            return {}
    
    def run(self, num_iterations) -> Dict:
        """
        Run the scheduler with the given number of iterations
        
        Args:
            num_iterations: Ignored for OR-Tools (used for compatibility)
            
        Returns:
            Dict: Schedule results
        """
        config = {'iterations': num_iterations}
        return self.run_with_config(config)
    
    def _format_result(self) -> Dict:
        """
        Format the schedule result
        
        Returns:
            Dict: Formatted schedule result
        """
        result = {
            'name': self.schedule_name,
            'score': self.schedule_score,
            'students': self.student_assignments,
            'courses': []
        }
        
        # Format course data
        for name, section in self.course_name_to_section.items():
            course_data = {
                'name': name,
                'time_slot': section.course.time_slot,
                'max_students': section.max_students,
                'enrolled': section.enrolled_students_count
            }
            result['courses'].append(course_data)
        
        return result
