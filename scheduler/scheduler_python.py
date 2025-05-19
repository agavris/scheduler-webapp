import random
import copy
import logging
from typing import List, Dict, Optional, Tuple
from .models import Course, Student, Section, Schedule

logger = logging.getLogger(__name__)

class PythonScheduler:
    """
    Pure Python implementation of the scheduler algorithm.
    This serves as a fallback if the Rust scheduler is unavailable.
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
    
    def safe_add_student_to_section(self, student, section) -> bool:
        """
        Safely add a student to a section if there is capacity
        
        Args:
            student: Student object to add
            section: Section object to add the student to
            
        Returns:
            bool: True if the student was added, False otherwise
        """
        if section is None:
            logger.error("Attempted to add student to a nil section")
            return False
        
        if section.enrolled_students_count < section.max_students:
            section.add_student(student)
            return True
        return False
    
    def find_first_available_section_for_student(self, student, time_slot) -> Optional[Section]:
        """
        Find the first available section for a student based on their preferences
        
        Args:
            student: Student object
            time_slot: Time slot to look for ('AM', 'PM', or 'FullDay')
            
        Returns:
            Section object or None if no section is available
        """
        course_names = []
        if time_slot == 'AM' or time_slot == 'FullDay':
            course_names = student.get_am_preferences()
        elif time_slot == 'PM':
            course_names = student.get_pm_preferences()
        
        # Try each requested course in order
        for course_name in course_names:
            if course_name and course_name in self.course_name_to_section:
                section = self.course_name_to_section[course_name]
                if section.enrolled_students_count < section.max_students:
                    return section
        
        # If none of the requested have space, fallback to any open section
        return self.get_first_available_section_without_request(time_slot)
    
    def get_first_available_section_without_request(self, time_slot) -> Optional[Section]:
        """
        Find any available section for the given time slot
        
        Args:
            time_slot: Time slot to look for ('AM', 'PM', or 'FullDay')
            
        Returns:
            Section object or None if no section is available
        """
        for section_name, section in self.course_name_to_section.items():
            if section.course.time_slot == time_slot and section.enrolled_students_count < section.max_students:
                return section
        return None
    
    def assign_students_to_sections(self):
        """Assign each student to an AM course + PM course if possible"""
        for student in self.students:
            # Assign AM course
            am_section = self.find_first_available_section_for_student(student, 'AM')
            if am_section:
                self.safe_add_student_to_section(student, am_section)
                
                # If we actually assigned an AM course, then do PM
                if am_section.course.time_slot == 'AM':
                    pm_section = self.find_first_available_section_for_student(student, 'PM')
                    if pm_section:
                        self.safe_add_student_to_section(student, pm_section)
    
    def extract_by_grade_and_shuffle(self):
        """
        Group students by priority, shuffle each group,
        and recombine maintaining priority order
        """
        # Clear all student enrollments
        for student in self.students:
            student.clear_enrollments()
        
        # Group students by priority
        students_by_priority = {1: [], 2: [], 3: []}
        for student in self.students:
            priority = student.priority
            students_by_priority[priority].append(student)
        
        # Shuffle each priority group
        for priority in students_by_priority:
            random.shuffle(students_by_priority[priority])
        
        # Recombine groups in priority order 1 -> 2 -> 3
        shuffled = []
        for priority in [1, 2, 3]:
            shuffled.extend(students_by_priority[priority])
        
        self.students = shuffled
    
    def score_schedule(self, save_only_best=False) -> float:
        """
        Calculate the total score for the current schedule
        
        Args:
            save_only_best: If True, only save the schedule if it's better than the current best
                          and mark it as the best schedule (replacing any previous best)
        
        Returns:
            float: The total satisfaction score
        """
        score = 0.0
        for student in self.students:
            student_score = student.satisfaction_score()
            score += student_score
            
            # If we already exceed (or equal) best known, we can skip
            if self.best_schedule and score >= self.best_schedule.score:
                return score
        
        # If this is strictly better, store it
        if not self.best_schedule or score < self.best_schedule.score:
            # Create a new Schedule object
            schedule = Schedule(
                name=f"Schedule_{score:.2f}",
                score=score,
                is_best=save_only_best  # Mark as best if save_only_best is True
            )
            schedule.save()
            
            # If save_only_best is True, mark all other schedules as not best
            if save_only_best:
                Schedule.objects.filter(is_best=True).exclude(id=schedule.id).update(is_best=False)
            
            # Save a snapshot of the current state
            schedule.save_snapshot()
            self.best_schedule = schedule
        
        return score
    
    def clear_sections(self):
        """
        Clear all sections for the next iteration
        """
        for section_name, section in self.course_name_to_section.items():
            section.clear_students()
    
    def run(self, num_iterations) -> Dict:
        """
        Run the scheduler with the given number of iterations
        
        Args:
            num_iterations: Number of iterations to run
            
        Returns:
            Dict: Schedule results
        """
        config = {'iterations': num_iterations}
        return self.run_with_config(config)
    
    def run_with_config(self, config) -> Dict:
        """
        Run the scheduler with the given configuration
        
        Args:
            config: Dict with configuration parameters
            
        Returns:
            Dict: Schedule results
        """
        iterations = config.get('iterations', 1000)
        min_course_fill = config.get('min_course_fill', 0.75)
        early_stop_score = config.get('early_stop_score', 0.0)
        save_only_best = config.get('save_only_best', False)  # Whether to only save the best schedule
        
        # Increase number of iterations before giving up if we're only saving one schedule
        stop_after_no_improvement = 5000 if save_only_best else 2000
        best_score_at = 0  # iteration index when we last improved
        
        for i in range(iterations):
            # 1) Shuffle students by priority
            self.extract_by_grade_and_shuffle()
            
            # 2) Assign them
            self.assign_students_to_sections()
            
            # 3) Score
            cur_score = self.score_schedule(save_only_best=save_only_best)
            
            # Check if we improved
            if self.best_schedule and self.best_schedule.score == cur_score:
                best_score_at = i
            
            # 4) Early stop if we reach threshold
            if early_stop_score > 0 and cur_score <= early_stop_score:
                logger.info(f"Reached early stop threshold score of {early_stop_score}")
                break
            
            # 5) Maybe stop if no improvement for many iterations
            if i - best_score_at > stop_after_no_improvement:
                logger.info(f"Stopping after {stop_after_no_improvement} iterations without improvement")
                break
            
            # 6) Clear for next iteration
            self.clear_sections()
            
            # 7) Log progress for long runs
            if i % 500 == 0:
                logger.info(f"Completed {i} iterations, current best score: {self.best_schedule.score if self.best_schedule else 'N/A'}")
        
        # Return the results
        if self.best_schedule:
            logger.info(f"Best schedule score: {self.best_schedule.score} after {i+1} iterations")
            return self._format_result()
        else:
            logger.warning("No valid schedule found.")
            return {}
    
    def _format_result(self) -> Dict:
        """
        Format the best schedule result in a format similar to the Rust output
        
        Returns:
            Dict: Formatted schedule result
        """
        result = {
            'score': self.best_schedule.score,
            'students': [],
            'sections': []
        }
        
        # Add students
        snapshots = self.best_schedule.snapshots.all()
        for snapshot in snapshots:
            student = {
                'id': snapshot.student.id,
                'email': snapshot.student.email,
                'first_name': snapshot.student.first_name,
                'last_name': snapshot.student.last_name,
                'grade': snapshot.student.grade,
                'priority': snapshot.student.priority,
                'am_course': snapshot.am_course.name if snapshot.am_course else None,
                'pm_course': snapshot.pm_course.name if snapshot.pm_course else None,
                'full_day_course': snapshot.full_day_course.name if snapshot.full_day_course else None,
                'satisfaction_score': snapshot.satisfaction_score
            }
            result['students'].append(student)
        
        # Add sections
        for course_name, section in self.course_name_to_section.items():
            section_data = {
                'course_name': course_name,
                'time_slot': section.course.time_slot,
                'max_students': section.max_students,
                'enrolled_students': section.enrolled_students_count,
                'student_ids': [s.id for s in section.get_students()]
            }
            result['sections'].append(section_data)
        
        return result
