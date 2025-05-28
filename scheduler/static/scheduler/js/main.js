/**
 * Main JavaScript file for the Course Scheduler application
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize file upload handlers
    initializeFileUploads();
    
    // Setup confirmation modals
    setupConfirmationModals();
    
    // Initialize data tables if the library is loaded
    initializeDataTables();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize file upload functionality
 */
function initializeFileUploads() {
    // Check if we have file upload forms
    const fileUploads = document.querySelectorAll('.custom-file-input');
    
    fileUploads.forEach(function(fileInput) {
        fileInput.addEventListener('change', function() {
            // Update the file name label
            const fileName = this.files[0]?.name;
            const label = this.nextElementSibling;
            if (label && fileName) {
                label.textContent = fileName;
            }
        });
    });
    
    // Setup CSV import forms
    const importForms = document.querySelectorAll('form.import-form');
    importForms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            
            const formData = new FormData(form);
            const url = form.getAttribute('action');
            const submitBtn = form.querySelector('button[type="submit"]');
            const spinner = submitBtn.querySelector('.spinner-border');
            const statusDiv = form.querySelector('.import-status');
            
            // Show spinner
            if (spinner) spinner.classList.remove('d-none');
            if (submitBtn) submitBtn.disabled = true;
            
            // Clear previous status
            if (statusDiv) statusDiv.innerHTML = '';
            
            // Send the request
            fetch(url, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Hide spinner
                if (spinner) spinner.classList.add('d-none');
                if (submitBtn) submitBtn.disabled = false;
                
                // Show status message
                if (statusDiv) {
                    const alertClass = data.error ? 'alert-danger' : 'alert-success';
                    const message = data.error || data.message;
                    statusDiv.innerHTML = `
                        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                            ${message}
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    `;
                }
                
                // Reload the page after success
                if (!data.error && data.message) {
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                }
            })
            .catch(error => {
                // Hide spinner
                if (spinner) spinner.classList.add('d-none');
                if (submitBtn) submitBtn.disabled = false;
                
                // Show error
                if (statusDiv) {
                    statusDiv.innerHTML = `
                        <div class="alert alert-danger alert-dismissible fade show" role="alert">
                            Error: ${error.message}
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    `;
                }
            });
        });
    });
}

/**
 * Setup confirmation modals for dangerous actions
 */
function setupConfirmationModals() {
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    
    confirmButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            
            const message = this.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
            const href = this.getAttribute('href');
            
            if (confirm(message)) {
                if (href) {
                    window.location.href = href;
                } else {
                    // If not a link, might be a form submit button
                    const form = this.closest('form');
                    if (form) form.submit();
                }
            }
        });
    });
}

/**
 * Initialize DataTables for better table displays
 */
function initializeDataTables() {
    // Check if DataTable function exists
    if (typeof $.fn.DataTable !== 'undefined') {
        // Destroy any existing DataTables to prevent errors
        $('.data-table').each(function() {
            if ($.fn.DataTable.isDataTable(this)) {
                $(this).DataTable().destroy();
            }
        });
        
        // Re-initialize each table with proper column detection
        $('.data-table').each(function() {
            // Count columns in header
            var headerColCount = $(this).find('thead th').length;
            // Only initialize if we have a header
            if (headerColCount > 0) {
                $(this).DataTable({
                    "responsive": true,
                    "lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]],
                    "pageLength": 25,
                    "autoWidth": false,
                    // This ensures the column count matches the table
                    "columns": Array(headerColCount).fill(null).map(() => ({ "defaultContent": "" })),
                    "language": {
                        "search": "Filter:",
                        "lengthMenu": "Show _MENU_ entries",
                        "info": "Showing _START_ to _END_ of _TOTAL_ entries"
                    }
                });
            }
        });
    }
}

/**
 * Run the scheduler with the given configuration
 */
function runScheduler(config) {
    const statusDiv = document.getElementById('scheduler-status');
    const submitBtn = document.getElementById('run-scheduler-btn');
    const spinner = document.getElementById('scheduler-spinner');
    
    // Show spinner
    if (spinner) spinner.classList.remove('d-none');
    if (submitBtn) submitBtn.disabled = true;
    
    // Clear previous status
    if (statusDiv) statusDiv.innerHTML = '';
    
    // Send the request
    fetch('/api/run-scheduler/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ config })
    })
    .then(response => response.json())
    .then(data => {
        // Hide spinner
        if (spinner) spinner.classList.add('d-none');
        if (submitBtn) submitBtn.disabled = false;
        
        // Show status message
        if (statusDiv) {
            const alertClass = data.error ? 'alert-danger' : 'alert-success';
            const message = data.error || data.message;
            statusDiv.innerHTML = `
                <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
        }
        
        // Redirect to the schedule detail page after success
        if (!data.error && data.schedule_id) {
            setTimeout(() => {
                window.location.href = `/schedules/${data.schedule_id}/`;
            }, 2000);
        }
    })
    .catch(error => {
        // Hide spinner
        if (spinner) spinner.classList.add('d-none');
        if (submitBtn) submitBtn.disabled = false;
        
        // Show error
        if (statusDiv) {
            statusDiv.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    Error: ${error.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
        }
    });
}
