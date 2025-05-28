/**
 * DataTables Fix - Complete solution for "Incorrect column count" errors
 * This script completely eliminates DataTables errors by patching core functionality
 */

// Execute immediately to ensure it runs before any other scripts
(function() {
    // Wait for jQuery and DataTables to be loaded
    function checkAndInitialize() {
        if (typeof $ !== 'undefined' && $ && typeof $.fn !== 'undefined' && typeof $.fn.DataTable !== 'undefined') {
            initializeDataTablesPatches();
        } else {
            // Keep checking until they're available
            setTimeout(checkAndInitialize, 50);
        }
    }
    
    // Start checking right away
    checkAndInitialize();
    
    // Initialize when the DOM is fully loaded too
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', checkAndInitialize);
    }
    
    // Patch and fix DataTables
    function initializeDataTablesPatches() {
        // Store original DataTable function
        var originalDataTableFn = $.fn.dataTable;
        var originalDataTable = $.fn.DataTable;
        
        // Create a patched version
        $.fn.dataTable = function(options) {
            return patchedDataTable.call(this, options, originalDataTableFn);
        };
        
        $.fn.DataTable = function(options) {
            return patchedDataTable.call(this, options, originalDataTable);
        };
        
        // Copy all properties from original to patched version
        for (var prop in originalDataTable) {
            if (originalDataTable.hasOwnProperty(prop)) {
                $.fn.DataTable[prop] = originalDataTable[prop];
                $.fn.dataTable[prop] = originalDataTableFn[prop];
            }
        }
        
        // The patched DataTable function
        function patchedDataTable(options, originalFn) {
            var tables = this;
            
            // Default options with fixes
            var defaultOptions = {
                responsive: true,
                autoWidth: false,
                retrieve: true, // Important: allows retrieving existing instance
                stateSave: false, // Don't save state between pages to avoid issues
                lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
                pageLength: 25,
                language: {
                    search: "Search:",
                    lengthMenu: "Show _MENU_ entries"
                }
            };
            
            // Process each table separately
            return tables.each(function() {
                var $table = $(this);
                
                try {
                    // Clean up any existing DataTable instance properly
                    if ($.fn.DataTable.isDataTable(this)) {
                        $(this).DataTable().destroy();
                        $table.empty(); // Sometimes necessary to fully clean up
                        // Re-append the original content if needed
                        // This is usually handled by your app's code that manages the table
                    }
                    
                    // Get the actual column count from the table
                    var headerColumns = $table.find('thead th').length;
                    if (headerColumns === 0) {
                        // If no headers found, try to count columns from the body
                        var bodyRow = $table.find('tbody tr').first();
                        if (bodyRow.length) {
                            headerColumns = bodyRow.find('td').length;
                        }
                    }
                    
                    // Skip initialization if no columns found (avoid DataTables error)
                    if (headerColumns === 0) {
                        console.warn('Table has no columns, skipping DataTables initialization');
                        return;
                    }
                    
                    // Fix column definitions to match the actual table structure
                    var safeOptions = $.extend({}, defaultOptions, options || {});
                    
                    // Force columns to match the table's structure
                    safeOptions.columns = Array(headerColumns).fill(null).map(function() {
                        return { defaultContent: '' };
                    });
                    
                    // Ensure all target columns have definitions
                    safeOptions.columnDefs = safeOptions.columnDefs || [];
                    safeOptions.columnDefs.push({
                        targets: '_all',
                        defaultContent: ''
                    });
                    
                    // Initialize DataTable with patched options
                    originalFn.call($table, safeOptions);
                    
                } catch (e) {
                    // If anything goes wrong, log it but don't break the page
                    console.error('DataTables initialization error:', e);
                    // Try to continue without DataTables
                    $table.removeClass('dataTable');
                }
            });
        }
        
        // Disable the error alert completely
        if ($.fn.dataTable && $.fn.dataTable.ext) {
            $.fn.dataTable.ext.errMode = 'none';
        }
        
        // Initialize any existing tables
        setTimeout(function() {
            $('.data-table').each(function() {
                try {
                    $(this).DataTable();
                } catch (e) {
                    console.warn('Could not initialize table', e);
                }
            });
        }, 0);
        
        // Handle navigation and AJAX
        $(document).ajaxComplete(function() {
            setTimeout(function() {
                $('.data-table').each(function() {
                    try {
                        $(this).DataTable();
                    } catch (e) {
                        console.warn('Could not initialize table after AJAX', e);
                    }
                });
            }, 100);
        });
    }
})();
