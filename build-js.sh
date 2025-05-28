#!/bin/bash
# JavaScript Build and Security Script
# This script minifies, obfuscates, and secures JavaScript files

echo "Starting JavaScript security build process..."

# Create temporary directory
mkdir -p .js-build-tmp

# Install node dependencies if needed (add to Dockerfile for production)
if ! command -v uglifyjs &> /dev/null; then
    echo "Installing UglifyJS..."
    npm install -g uglify-js
fi

if ! command -v javascript-obfuscator &> /dev/null; then
    echo "Installing JavaScript Obfuscator..."
    npm install -g javascript-obfuscator
fi

# Process each JavaScript file in the static directory
find ./scheduler/static/scheduler/js -name "*.js" -not -name "*.min.js" | while read file; do
    filename=$(basename "$file")
    directory=$(dirname "$file")
    output_file="${directory}/${filename%.js}.min.js"
    
    echo "Processing $filename..."
    
    # Step 1: Minify with UglifyJS
    uglifyjs "$file" -o ".js-build-tmp/$filename.min" -c -m
    
    # Step 2: Obfuscate with JavaScript Obfuscator
    javascript-obfuscator ".js-build-tmp/$filename.min" \
        --output "$output_file" \
        --compact true \
        --control-flow-flattening true \
        --control-flow-flattening-threshold 0.7 \
        --dead-code-injection true \
        --dead-code-injection-threshold 0.4 \
        --debug-protection true \
        --debug-protection-interval true \
        --disable-console-output true \
        --domain-lock "yourdomain.com" \
        --identifier-names-generator "hexadecimal" \
        --rename-globals true \
        --rotate-string-array true \
        --self-defending true \
        --string-array true \
        --string-array-encoding "rc4" \
        --string-array-threshold 0.8 \
        --transform-object-keys true
        
    echo "Created secure version at $output_file"
    
    # Create an integrity hash for Subresource Integrity
    echo "Generating SRI hash..."
    sri_hash=$(openssl dgst -sha384 -binary "$output_file" | openssl base64 -A)
    echo "SRI Hash for $filename: sha384-$sri_hash"
    
    # Add to manifest for easy reference
    echo "$filename: sha384-$sri_hash" >> .js-build-tmp/js-integrity.txt
done

# Clean up
echo "Cleaning up..."
rm -rf .js-build-tmp

echo "JavaScript security build complete!"
