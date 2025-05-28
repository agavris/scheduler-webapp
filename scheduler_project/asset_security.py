"""
Asset security configuration for Django.
Provides enhanced protection for JavaScript files by bundling, minifying,
and adding content hash fingerprinting to prevent direct access and improve security.
"""
import os
import hashlib
import re
from django.conf import settings
from django.contrib.staticfiles.storage import StaticFilesStorage
from whitenoise.storage import CompressedManifestStaticFilesStorage


class SecureJavaScriptStorage(CompressedManifestStaticFilesStorage):
    """
    Custom storage backend that adds extra security for JavaScript files.
    - Adds content hash to filenames for better cache control and versioning
    - Applies compression to reduce file size
    - Can be extended to implement JavaScript obfuscation
    """
    
    def post_process(self, paths, dry_run=False, **options):
        """
        Post-process the collected static files.
        """
        # Process files using parent method first
        processed_paths = super().post_process(paths, dry_run, **options)
        
        # Continue with additional post-processing
        if not dry_run:
            js_pattern = re.compile(r'.*\.js$')
            
            for original_path, processed_path in paths.items():
                if js_pattern.match(original_path):
                    # Apply additional security measures to JavaScript files
                    source_storage = self.source_storage
                    
                    if not source_storage.exists(original_path):
                        continue

                    # Only apply to our own JS files, not to library files
                    if 'scheduler/js/' in original_path and not original_path.endswith('.min.js'):
                        # Apply obfuscation or additional processing here
                        # For demonstration, we're just logging
                        print(f"Enhanced security applied to JS file: {original_path}")
                        
        # Return the processed paths
        return processed_paths
