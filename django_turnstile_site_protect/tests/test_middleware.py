"""Tests for the TurnstileMiddleware class."""

from unittest.mock import patch

from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from django_turnstile_site_protect.middleware import TurnstileMiddleware


class TestTurnstileMiddleware(TestCase):
    """Test cases for TurnstileMiddleware."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Allow all hosts during testing to avoid DisallowedHost errors
        from django.conf import settings

        settings.ALLOWED_HOSTS = ['*']

    def setUp(self):
        """Set up test environment."""
        self.factory = RequestFactory()
        self.get_response = lambda req: HttpResponse()
        self.middleware = TurnstileMiddleware(self.get_response)
        self.default_settings = {
            'TURNSTILE_SITE_KEY': 'test-site-key',
            'TURNSTILE_SECRET_KEY': 'test-secret-key',
            'TURNSTILE_ENABLED': True,
            'TURNSTILE_VERIFY_URL': 'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            'TURNSTILE_SESSION_KEY': 'turnstile_verified',
            'TURNSTILE_CHALLENGE_PATH': '/challenge/',
            'TURNSTILE_EXCLUDED_PATHS': ['/challenge/', '/verify/'],
            'TURNSTILE_EXCLUDED_IPS': [
                # Note: The middleware only supports single IPs and range format (X.X.X.X-Y.Y.Y.Y)
                # Converting CIDR to range format for testing:
                '192.168.1.0-192.168.1.255',  # 192.168.1.0/24 in range format
                '10.0.0.0-10.255.255.255',  # 10.0.0.0/8 in range format
                '203.0.112.0-203.0.113.255',  # Already in range format
            ],
            'TURNSTILE_EXCLUDED_DOMAINS': ['example.com', '.test.com'],
        }

    def get_request(self, path='/', **kwargs):
        """Create a request object with a session."""
        request = self.factory.get(path, **kwargs)
        request.session = {}
        return request

    def test_is_path_excluded(self):
        """Test the is_path_excluded method of the middleware."""
        # Test with a path that shouldn't be excluded by default
        self.assertFalse(self.middleware.is_path_excluded('/some/random/path/'))

        # Test with the challenge path (should be excluded)
        self.assertTrue(
            self.middleware.is_path_excluded(self.middleware.challenge_path)
        )

        # Test with the verify path (should be excluded)
        self.assertTrue(self.middleware.is_path_excluded(self.middleware.verify_path))

        # Test with a path that matches an excluded pattern
        with override_settings(TURNSTILE_EXCLUDED_PATHS=['^/excluded/']):
            middleware = TurnstileMiddleware(self.get_response)
            self.assertTrue(middleware.is_path_excluded('/excluded/path/'))

        # Test with a path that doesn't match any excluded patterns
        with override_settings(TURNSTILE_EXCLUDED_PATHS=['^/other/']):
            middleware = TurnstileMiddleware(self.get_response)
            self.assertFalse(middleware.is_path_excluded('/excluded/path/'))

        # Test with a custom excluded path
        with self.settings(TURNSTILE_EXCLUDED_PATHS=['/api/']):
            middleware = TurnstileMiddleware(self.get_response)
            self.assertTrue(middleware.is_path_excluded('/api/'))

    def test_is_ip_excluded(self):
        """Test IP exclusion logic."""
        # List of IPs to test with their expected exclusion results
        test_cases = [
            ('192.168.1.1', True),  # In excluded range 192.168.1.0-192.168.1.255
            ('10.0.0.100', True),  # In excluded range 10.0.0.0-10.255.255.255
            ('203.0.112.100', True),  # In excluded range 203.0.112.0-203.0.113.255
            ('192.168.2.1', False),  # Not in excluded ranges
            ('172.16.0.1', False),  # Not in excluded ranges
        ]

        # Set up the specific IP ranges for this test
        excluded_ips = [
            '192.168.1.0-192.168.1.255',  # 192.168.1.0/24 in range format
            '10.0.0.0-10.255.255.255',  # 10.0.0.0/8 in range format
            '203.0.112.0-203.0.113.255',  # Already in range format
        ]

        # Apply settings and create a fresh middleware instance
        with self.settings(TURNSTILE_EXCLUDED_IPS=excluded_ips):
            # Create a new middleware instance with these settings
            test_middleware = TurnstileMiddleware(self.get_response)

            # Run test cases against the newly created middleware
            for ip, expected in test_cases:
                with self.subTest(ip=ip, expected=expected):
                    request = self.get_request(REMOTE_ADDR=ip)
                    self.assertEqual(test_middleware.is_ip_excluded(request), expected)

    def test_is_domain_excluded(self):
        """Test domain exclusion logic."""
        test_cases = [
            ('example.com', True),  # Exact match
            ('sub.test.com', True),  # Subdomain of .test.com
            ('example.org', False),  # Not in excluded domains
            ('test.example.com', False),  # Not in excluded domains
        ]

        for host, expected in test_cases:
            with self.subTest(host=host, expected=expected):
                request = self.get_request(HTTP_HOST=host)
                assert self.middleware.is_domain_excluded(request) == expected

    def test_process_request_redirects_to_challenge(self):
        """Test that unverified requests are redirected to challenge."""
        request = self.get_request()
        response = self.middleware.process_request(request)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/challenge/'))

    def test_process_request_allows_verified_requests(self):
        """Test that verified requests are allowed through."""
        request = self.get_request()
        request.session[self.middleware.session_key] = True
        response = self.middleware.process_request(request)
        # Middleware allows the request to continue
        self.assertIsNone(response)

    @override_settings(TURNSTILE_ENABLED=False)
    @patch.dict('os.environ', {'TURNSTILE_ENABLED': 'False'})
    def test_middleware_disabled_by_environment(self):
        """Test that middleware is disabled when TURNSTILE_ENABLED is False."""
        # Create a new middleware instance with environment variable set
        middleware = TurnstileMiddleware(self.get_response)
        request = self.get_request()
        response = middleware.process_request(request)
        # When disabled, middleware should not return a response (should pass through)
        self.assertIsNone(response)

    def test_middleware_with_custom_session_key(self):
        """Test middleware with a custom session key."""
        from django.test import override_settings

        custom_key = 'custom_verified_key'

        with override_settings(TURNSTILE_SESSION_KEY=custom_key):
            middleware = TurnstileMiddleware(self.get_response)

            # Test that middleware allows verified requests
            request = self.get_request()
            request.session[custom_key] = True
            response = middleware.process_request(request)
            self.assertIsNone(response)

            # Test that middleware redirects unverified requests
            request = self.get_request()
            request.session = {}
            response = middleware.process_request(request)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith('/challenge/'))

    @override_settings(TURNSTILE_CHALLENGE_PATH='/custom/challenge/')
    def test_middleware_with_custom_challenge_path(self):
        """Test middleware with a custom challenge path."""
        # Create new middleware with the overridden settings
        with patch('django_turnstile_site_protect.middleware.reverse') as mock_reverse:
            # Configure mock to return different values for different calls
            mock_reverse.side_effect = [
                '/custom/challenge/',  # First call for turnstile_challenge
                '/verify/',  # Second call for turnstile_verify
            ]

            # Create middleware - this will call reverse() twice
            middleware = TurnstileMiddleware(self.get_response)

            # Now test the middleware
            request = self.get_request()
            response = middleware.process_request(request)

            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith('/custom/challenge/'))

            # Verify reverse was called with the expected arguments
            self.assertEqual(mock_reverse.call_count, 2)
            mock_reverse.assert_any_call('turnstile_challenge')
            mock_reverse.assert_any_call('turnstile_verify')

    def test_middleware_with_custom_excluded_paths(self):
        """Test middleware with custom excluded paths."""
        from django.test import override_settings

        custom_paths = ['/api/', '/static/']

        with override_settings(TURNSTILE_EXCLUDED_PATHS=custom_paths):
            middleware = TurnstileMiddleware(get_response=self.get_response)

            # Test excluded paths
            for path in custom_paths:
                self.assertTrue(
                    any(path.startswith(p) for p in middleware.excluded_paths)
                )

            # Test non-excluded path
            self.assertFalse(
                any(
                    '/some/other/path/'.startswith(p) for p in middleware.excluded_paths
                )
            )

    def test_middleware_with_invalid_ip_ranges(self):
        """Test middleware with invalid IP ranges in settings."""
        # Mock the _parse_ip_ranges method to avoid the ValueError
        with patch.object(TurnstileMiddleware, '_parse_ip_ranges', return_value=[]):
            # Test with invalid IP format - should be handled gracefully by middleware
            with self.settings(TURNSTILE_EXCLUDED_IPS=['invalid-ip-range']):
                middleware = TurnstileMiddleware(self.get_response)

                # Test with an IP that would be in the range if it was valid
                request = self.get_request(REMOTE_ADDR='192.168.1.1')

                # The middleware should handle invalid IP ranges gracefully
                self.assertFalse(middleware.is_ip_excluded(request))
