use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use pyo3::types::{PyDict, PyList, PyString};
use rand::prelude::*;
use rayon::prelude::*;
use std::collections::HashMap;
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Course {
    name: String,
    time_slot: String,
    max_students: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Student {
    id: i32,
    email: String,
    first_name: String,
    last_name: String,
    grade: String,
    priority: i32,
    am_preferences: Vec<String>,
    pm_preferences: Vec<String>,
    am_course: Option<String>,
    pm_course: Option<String>,
    full_day_course: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Section {
    course_name: String,
    time_slot: String,
    max_students: i32,
    students: Vec<i32>, // Student IDs
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Schedule {
    students: Vec<Student>,
    sections: Vec<Section>,
    score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SchedulerConfig {
    iterations: i32,
    min_course_fill: f64,
    early_stop_score: f64,
}

impl Student {
    fn satisfaction_score(&self) -> f64 {
        let mut score = 0.0;
        
        // Check full day course first (if enrolled)
        if let Some(course_name) = &self.full_day_course {
            if !self.am_preferences.contains(course_name) {
                score += 1.0;
                return score;  // Return immediately as in Go code
            }
        }
        
        // Check AM course
        if let Some(course_name) = &self.am_course {
            if !self.am_preferences.contains(course_name) {
                score += 0.5;
            }
        }
        
        // Check PM course
        if let Some(course_name) = &self.pm_course {
            if !self.pm_preferences.contains(course_name) {
                score += 0.5;
            }
        }
        
        score
    }
    
    fn clear_enrollments(&mut self) {
        self.am_course = None;
        self.pm_course = None;
        self.full_day_course = None;
    }
}

impl Section {
    fn new(course: &Course) -> Self {
        Section {
            course_name: course.name.clone(),
            time_slot: course.time_slot.clone(),
            max_students: course.max_students,
            students: Vec::new(),
        }
    }
    
    fn add_student(&mut self, student_id: i32) -> bool {
        if self.students.len() < self.max_students as usize {
            self.students.push(student_id);
            return true;
        }
        false
    }
    
    fn clear_students(&mut self) {
        self.students.clear();
    }
}

struct Scheduler {
    courses: Vec<Course>,
    students: Vec<Student>,
    course_name_to_section: HashMap<String, Section>,
    best_schedule: Option<Schedule>,
}

impl Scheduler {
    fn new(courses: Vec<Course>, students: Vec<Student>) -> Self {
        let mut scheduler = Scheduler {
            courses,
            students,
            course_name_to_section: HashMap::new(),
            best_schedule: None,
        };
        
        // Initialize sections for each course
        for course in &scheduler.courses {
            let section = Section::new(course);
            scheduler.course_name_to_section.insert(course.name.clone(), section);
        }
        
        scheduler
    }
    
    fn safe_add_student_to_section(&mut self, student_id: i32, section_name: &str) -> bool {
        if let Some(section) = self.course_name_to_section.get_mut(section_name) {
            if section.students.len() < section.max_students as usize {
                section.add_student(student_id);
                
                // Update student's enrolled courses
                let student = &mut self.students[student_id as usize];
                match section.time_slot.as_str() {
                    "AM" => student.am_course = Some(section_name.to_string()),
                    "PM" => student.pm_course = Some(section_name.to_string()),
                    "FullDay" => student.full_day_course = Some(section_name.to_string()),
                    _ => {}
                }
                
                return true;
            }
        }
        false
    }
    
    fn find_first_available_section_for_student(&self, student: &Student, time_slot: &str) -> Option<String> {
        let course_names = match time_slot {
            "AM" | "FullDay" => &student.am_preferences,
            "PM" => &student.pm_preferences,
            _ => return None,
        };
        
        // Try each requested course in order
        for course_name in course_names {
            if let Some(section) = self.course_name_to_section.get(course_name) {
                if section.students.len() < section.max_students as usize {
                    return Some(course_name.clone());
                }
            }
        }
        
        // If none of the requested have space, fallback to any open section
        self.get_first_available_section_without_request(time_slot)
    }
    
    fn get_first_available_section_without_request(&self, time_slot: &str) -> Option<String> {
        for (course_name, section) in &self.course_name_to_section {
            if section.time_slot == time_slot && section.students.len() < section.max_students as usize {
                return Some(course_name.clone());
            }
        }
        None
    }
    
    fn assign_students_to_sections(&mut self) {
        for (student_idx, student) in self.students.iter().enumerate() {
            // Assign AM course
            if let Some(section_name) = self.find_first_available_section_for_student(student, "AM") {
                self.safe_add_student_to_section(student_idx as i32, &section_name);
                
                // If we assigned an AM course, then try to assign PM
                let pm_slot = self.find_first_available_section_for_student(student, "PM");
                if let Some(pm_section_name) = pm_slot {
                    self.safe_add_student_to_section(student_idx as i32, &pm_section_name);
                }
            }
        }
    }
    
    fn extract_by_grade_and_shuffle(&mut self) {
        // Clear all student enrollments
        for student in &mut self.students {
            student.clear_enrollments();
        }
        
        // Group students by priority
        let mut students_by_priority: HashMap<i32, Vec<usize>> = HashMap::new();
        for (idx, student) in self.students.iter().enumerate() {
            students_by_priority
                .entry(student.priority)
                .or_insert_with(Vec::new)
                .push(idx);
        }
        
        // Shuffle each priority group and recombine in order
        let mut rng = rand::thread_rng();
        let mut shuffled_indices = Vec::new();
        
        for priority in 1..=3 {
            if let Some(indices) = students_by_priority.get_mut(&priority) {
                indices.shuffle(&mut rng);
                shuffled_indices.extend(indices.iter().cloned());
            }
        }
        
        // Reorder students based on shuffled indices
        let students_copy = self.students.clone();
        for (new_idx, &old_idx) in shuffled_indices.iter().enumerate() {
            self.students[new_idx] = students_copy[old_idx].clone();
        }
    }
    
    fn score_schedule(&mut self) -> f64 {
        let mut score = 0.0;
        
        for student in &self.students {
            let student_score = student.satisfaction_score();
            score += student_score;
            
            // If we already exceed (or equal) best known, we can skip
            if let Some(best_schedule) = &self.best_schedule {
                if score >= best_schedule.score {
                    return score;
                }
            }
        }
        
        // If this is strictly better, store it
        if self.best_schedule.is_none() || score < self.best_schedule.as_ref().unwrap().score {
            let students_copy = self.students.clone();
            let sections_copy: Vec<Section> = self.course_name_to_section.values().cloned().collect();
            
            self.best_schedule = Some(Schedule {
                students: students_copy,
                sections: sections_copy,
                score,
            });
        }
        
        score
    }
    
    fn clear_sections(&mut self) {
        for (_, section) in &mut self.course_name_to_section {
            section.clear_students();
        }
        
        // Also clear student enrollments
        for student in &mut self.students {
            student.clear_enrollments();
        }
    }
    
    fn run_with_config(&mut self, config: SchedulerConfig) -> Option<Schedule> {
        let mut best_score_at = 0; // iteration index when we last improved
        
        for i in 0..config.iterations {
            // 1) Shuffle students by priority
            self.extract_by_grade_and_shuffle();
            
            // 2) Assign them
            self.assign_students_to_sections();
            
            // 3) Score
            let cur_score = self.score_schedule();
            
            // Check if we improved
            if let Some(best_schedule) = &self.best_schedule {
                if best_schedule.score == cur_score {
                    best_score_at = i;
                }
            }
            
            // Early stop if we reach threshold
            if config.early_stop_score > 0.0 && cur_score <= config.early_stop_score {
                break;
            }
            
            // Maybe stop if no improvement for many iterations
            if i - best_score_at > 10000 {
                break;
            }
            
            // Clear for next iteration
            self.clear_sections();
        }
        
        self.best_schedule.clone()
    }
}

// Python module implementation
#[pyfunction]
fn run_scheduler(
    py: Python,
    courses_json: &str,
    students_json: &str,
    config_json: &str,
) -> PyResult<String> {
    // Parse input data
    let courses: Vec<Course> = serde_json::from_str(courses_json)?;
    let students: Vec<Student> = serde_json::from_str(students_json)?;
    let config: SchedulerConfig = serde_json::from_str(config_json)?;
    
    // Create and run scheduler
    let mut scheduler = Scheduler::new(courses, students);
    let result = scheduler.run_with_config(config);
    
    // Convert result back to JSON for Python
    match result {
        Some(schedule) => Ok(serde_json::to_string(&schedule)?),
        None => Ok("{}".to_string()),
    }
}

// Parallel version for large datasets
#[pyfunction]
fn run_scheduler_parallel(
    py: Python,
    courses_json: &str,
    students_json: &str,
    config_json: &str,
    num_threads: usize,
) -> PyResult<String> {
    // Parse input data
    let courses: Vec<Course> = serde_json::from_str(courses_json)?;
    let students: Vec<Student> = serde_json::from_str(students_json)?;
    let config: SchedulerConfig = serde_json::from_str(config_json)?;
    
    // Run multiple instances in parallel with different random seeds
    let results: Vec<_> = (0..num_threads).into_par_iter().map(|_| {
        let mut scheduler = Scheduler::new(courses.clone(), students.clone());
        let result = scheduler.run_with_config(config.clone());
        result
    }).collect();
    
    // Find the best result among all threads
    let best_schedule = results.into_iter()
        .filter_map(|result| result)
        .min_by(|a, b| a.score.partial_cmp(&b.score).unwrap_or(std::cmp::Ordering::Equal));
    
    // Convert result back to JSON
    match best_schedule {
        Some(schedule) => Ok(serde_json::to_string(&schedule)?),
        None => Ok("{}".to_string()),
    }
}

#[pymodule]
fn rust_scheduler(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(run_scheduler, m)?)?;
    m.add_function(wrap_pyfunction!(run_scheduler_parallel, m)?)?;
    Ok(())
}
