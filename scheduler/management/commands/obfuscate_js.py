"""
Management command to obfuscate JavaScript files.
This makes it much harder for anyone to understand your JavaScript code
even if they can access the files directly.
"""
import os
import re
import glob
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Obfuscates JavaScript files to make them harder to read'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default=os.path.join(settings.STATIC_ROOT, 'scheduler/js'),
            help='Path to JavaScript files to obfuscate'
        )

    def handle(self, *args, **options):
        path = options['path']
        self.stdout.write(f"Obfuscating JavaScript files in {path}")

        # Create directory if it doesn't exist
        os.makedirs(path, exist_ok=True)

        # Find all .js files that aren't already minified (.min.js)
        js_files = [f for f in glob.glob(f"{path}/**/*.js", recursive=True) 
                    if not f.endswith('.min.js')]
        
        for js_file in js_files:
            self.stdout.write(f"Processing {js_file}")
            
            # Read the original file
            with open(js_file, 'r') as f:
                content = f.read()
            
            # Apply basic obfuscation techniques
            obfuscated = self._obfuscate_content(content)
            
            # Write to new file with .min.js extension
            output_file = js_file.replace('.js', '.min.js')
            with open(output_file, 'w') as f:
                f.write(obfuscated)
            
            self.stdout.write(self.style.SUCCESS(f"Created obfuscated version: {output_file}"))

    def _obfuscate_content(self, content):
        """
        Apply basic obfuscation techniques to JavaScript content.
        For real production use, you would want to use a proper JS obfuscator
        like javascript-obfuscator npm package, but this shows the concept.
        """
        # Remove comments
        content = re.sub(r'\/\/.*?$', '', content, flags=re.MULTILINE)
        content = re.sub(r'\/\*[\s\S]*?\*\/', '', content)
        
        # Remove whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Basic variable name obfuscation
        # This is just a demonstration - real obfuscation would use a proper parser
        var_names = set(re.findall(r'var\s+(\w+)', content))
        replacement_map = {name: f'_{i}' for i, name in enumerate(var_names)}
        
        for original, replacement in replacement_map.items():
            # Only replace variable declarations and references
            content = re.sub(r'var\s+' + original + r'\b', 'var ' + replacement, content)
            content = re.sub(r'(?<!\.)' + original + r'\b(?!\s*:)', replacement, content)
        
        return content
