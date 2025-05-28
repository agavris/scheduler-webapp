"""
Middleware for adding Content Security Policy nonces to enhance JavaScript security
"""
import base64
import os
import re
from django.utils.deprecation import MiddlewareMixin


class CSPNonceMiddleware(MiddlewareMixin):
    """
    Middleware that adds a random nonce to script tags in the response.
    This works with the CSP policy to only allow scripts with the correct nonce to execute.
    """
    
    def process_response(self, request, response):
        # Skip non-HTML responses
        content_type = response.get('Content-Type', '')
        if not content_type.startswith('text/html'):
            return response
            
        # Generate a random nonce
        nonce = base64.b64encode(os.urandom(16)).decode('utf-8')
        
        # Store the nonce in the request for the template context
        request.csp_nonce = nonce
        
        # Replace {nonce} placeholder in CSP header if it exists
        csp_header = response.get('Content-Security-Policy', '')
        if csp_header and '{nonce}' in csp_header:
            response['Content-Security-Policy'] = csp_header.replace('{nonce}', nonce)
            
        # If the response has a content, add the nonce to script tags
        if hasattr(response, 'content') and isinstance(response.content, bytes):
            content = response.content.decode('utf-8')
            
            # Add nonce to script tags
            content = re.sub(
                r'<script',
                f'<script nonce="{nonce}"',
                content
            )
            
            response.content = content.encode('utf-8')
            
        return response
