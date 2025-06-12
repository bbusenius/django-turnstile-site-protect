import ipaddress
import os
import re

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class TurnstileMiddleware(MiddlewareMixin):
    """
    Middleware that checks if a user has passed a Cloudflare Turnstile challenge.
    If not, redirects to the challenge page unless the path is excluded.
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.session_key = getattr(
            settings, 'TURNSTILE_SESSION_KEY', 'turnstile_passed'
        )
        self.excluded_paths = getattr(settings, 'TURNSTILE_EXCLUDED_PATHS', [])

        # Check if middleware is enabled (defaults to True if not specified)
        self.enabled = os.environ.get('TURNSTILE_ENABLED', 'True').lower() not in (
            'false',
            '0',
            'no',
            'off',
        )

        # Compile excluded paths into regex patterns for faster matching
        self.excluded_patterns = [re.compile(path) for path in self.excluded_paths]

        # Always exclude the challenge and verification paths
        self.challenge_path = reverse('turnstile_challenge')
        self.verify_path = reverse('turnstile_verify')

        # Get excluded IP ranges from settings
        self.excluded_ips = getattr(settings, 'TURNSTILE_EXCLUDED_IPS', [])
        self.ip_ranges = self._parse_ip_ranges(self.excluded_ips)

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

    def _parse_ip_ranges(self, ip_list):
        """
        Parse a list of IP addresses and ranges into network objects for efficient matching.
        Format for ranges: '192.168.1.0-192.168.1.255'
        Format for single IPs: '192.168.1.1'
        """
        networks = []

        for item in ip_list:
            if '-' in item:  # It's a range
                start_ip, end_ip = item.split('-')
                try:
                    # Convert to integer representations for comparison
                    start_int = int(ipaddress.IPv4Address(start_ip.strip()))
                    end_int = int(ipaddress.IPv4Address(end_ip.strip()))

                    # Store the range as a tuple of integers for efficient comparison
                    networks.append(('range', (start_int, end_int)))
                except ValueError:
                    # If invalid IP, just skip it
                    continue
            else:  # It's a single IP
                try:
                    networks.append(
                        ('single', int(ipaddress.IPv4Address(item.strip())))
                    )
                except ValueError:
                    # If invalid IP, just skip it
                    continue

        return networks

    def is_ip_excluded(self, request):
        """
        Check if the requester's IP address should be excluded from Turnstile verification.
        """
        # Get client IP from request
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Use the first IP in X-Forwarded-For header
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        try:
            # Convert client IP to integer for comparison
            client_ip_int = int(ipaddress.IPv4Address(ip))

            # Check against our networks list
            for net_type, net_value in self.ip_ranges:
                if net_type == 'single' and client_ip_int == net_value:
                    return True
                elif (
                    net_type == 'range'
                    and net_value[0] <= client_ip_int <= net_value[1]
                ):
                    return True

            return False
        except ValueError:
            # If the IP is invalid, don't exclude
            return False

    def process_request(self, request):
        """
        Process the request and redirect to challenge if user hasn't passed Turnstile.
        """
        # Skip middleware completely if disabled via environment variable
        if not self.enabled:
            return None

        # Skip verification for excluded paths
        if self.is_path_excluded(request.path):
            return None

        # Skip verification for excluded IPs
        if self.is_ip_excluded(request):
            return None

        # Check if user has passed Turnstile challenge
        if not request.session.get(self.session_key):
            # Store the original path for redirection after verification
            next_url = request.path
            challenge_url = f"{self.challenge_path}?next={next_url}"
            return redirect(challenge_url)

        return None
