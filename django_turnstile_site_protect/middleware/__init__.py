from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
import re


class TurnstileMiddleware(MiddlewareMixin):
    """
    Middleware that checks if a user has passed a Cloudflare Turnstile challenge.
    If not, redirects to the challenge page unless the path is excluded.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.session_key = getattr(settings, 'TURNSTILE_SESSION_KEY', 'turnstile_passed')
        self.excluded_paths = getattr(settings, 'TURNSTILE_EXCLUDED_PATHS', [])
        
        # Compile excluded paths into regex patterns for faster matching
        self.excluded_patterns = [re.compile(path) for path in self.excluded_paths]
        
        # Always exclude the challenge and verification paths
        self.challenge_path = reverse('turnstile_challenge')
        self.verify_path = reverse('turnstile_verify')
    
    def is_path_excluded(self, path):
        """
        Check if the current path should be excluded from Turnstile verification.
        """
        if path.startswith(self.challenge_path) or path.startswith(self.verify_path):
            return True
            
        for pattern in self.excluded_patterns:
            if pattern.match(path):
                return True
                
        return False
    
    def process_request(self, request):
        """
        Process the request and redirect to challenge if user hasn't passed Turnstile.
        """
        # Skip verification for excluded paths
        if self.is_path_excluded(request.path):
            return None
            
        # Check if user has passed Turnstile challenge
        if not request.session.get(self.session_key):
            # Store the original path for redirection after verification
            next_url = request.path
            challenge_url = f"{self.challenge_path}?next={next_url}"
            return redirect(challenge_url)
            
        return None
