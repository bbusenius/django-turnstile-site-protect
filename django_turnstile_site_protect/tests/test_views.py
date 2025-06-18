"""Tests for the Turnstile views."""

from unittest.mock import MagicMock, patch

from django.http import HttpResponseRedirect
from django.test import RequestFactory, TestCase
from django.urls import reverse

from django_turnstile_site_protect.views import challenge_view, verify_view


class TestChallengeView(TestCase):
    """Test cases for the challenge_view."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_challenge_view_get(self):
        """Test GET request to challenge view with custom next URL."""
        request = self.factory.get('/challenge/?next=/protected/')
        request.session = {}

        with self.settings(
            TURNSTILE_SITE_KEY='test-site-key',
            TURNSTILE_MODE='managed',
            TURNSTILE_APPEARANCE='always',
            TURNSTILE_THEME='auto',
            TURNSTILE_LANGUAGE='auto',
            TURNSTILE_SIZE='normal',
        ):
            response = challenge_view(request)

            self.assertEqual(response.status_code, 200)
            content = response.content.decode()
            self.assertIn('test-site-key', content)
            # In the original behavior, the next URL should be included in the form
            self.assertIn('name="next" value="/protected/"', content)
            # Check if the template is being used (check for the Cloudflare Turnstile API URL)
            self.assertIn('challenges.cloudflare.com/turnstile/v0/api.js', content)

    def test_challenge_view_default_next_url(self):
        """Test challenge view with default next URL."""
        request = self.factory.get('/challenge/')
        request.session = {}

        with self.settings(TURNSTILE_SITE_KEY='test-site-key'):
            response = challenge_view(request)
            content = response.content.decode()
            # In the original behavior, the next URL should be "/" in the form
            self.assertIn('name="next" value="/"', content)

    def test_challenge_view_with_different_modes(self):
        """Test challenge view with different TURNSTILE_MODE settings."""
        for mode in ['managed', 'invisible', 'interactive-only']:
            with self.subTest(mode=mode):
                with self.settings(TURNSTILE_MODE=mode):
                    request = self.factory.get('/challenge/')
                    request.session = {}
                    response = challenge_view(request)
                    self.assertEqual(response.status_code, 200)

    def test_challenge_view_with_custom_theme(self):
        """Test challenge view with different theme settings."""
        for theme in ['light', 'dark', 'auto']:
            with self.subTest(theme=theme):
                with self.settings(TURNSTILE_THEME=theme):
                    request = self.factory.get('/challenge/')
                    request.session = {}
                    response = challenge_view(request)
                    self.assertEqual(response.status_code, 200)

    def test_challenge_view_with_custom_appearance(self):
        """Test challenge view with different appearance settings."""
        for appearance in ['always', 'execute', 'interaction-only']:
            with self.subTest(appearance=appearance):
                with self.settings(TURNSTILE_APPEARANCE=appearance):
                    request = self.factory.get('/challenge/')
                    request.session = {}
                    response = challenge_view(request)
                    self.assertEqual(response.status_code, 200)

    def test_challenge_view_with_invalid_next_url(self):
        """Test that challenge view passes through next URL without validation."""
        response = self.client.get(
            reverse('turnstile_challenge'), {'next': 'http://evil.com'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'http://evil.com', response.content)


class TestVerifyView(TestCase):
    """Test cases for the verify_view."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_verify_view_get_redirects_to_challenge(self):
        """Test GET request to verify view redirects to challenge."""
        request = self.factory.get('/verify/')
        request.session = {}

        response = verify_view(request)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, reverse('turnstile_challenge'))

    @patch('django_turnstile_site_protect.views.requests.post')
    def test_verify_view_success(self, mock_post):
        """Test successful verification."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response

        # Create a POST request with a token
        request = self.factory.post(
            '/verify/', {'cf-turnstile-response': 'test-token', 'next': '/protected/'}
        )
        request.session = {}

        with self.settings(TURNSTILE_SECRET_KEY='test-secret-key'):
            response = verify_view(request)

            # Check that the session was updated
            self.assertTrue(request.session.get('turnstile_passed'))
            # Check that we're redirected to the protected URL
            self.assertIsInstance(response, HttpResponseRedirect)
            self.assertEqual(response.url, '/protected/')

            # Check that the API was called with the correct data
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(kwargs['data']['secret'], 'test-secret-key')
            self.assertEqual(kwargs['data']['response'], 'test-token')

    @patch('django_turnstile_site_protect.views.requests.post')
    def test_verify_view_failure(self, mock_post):
        """Test that verification fails with invalid token."""
        # Mock Turnstile API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': False,
            'error-codes': ['invalid-input-response'],
        }
        mock_post.return_value = mock_response

        # Make request with invalid token
        response = self.client.post(
            reverse('turnstile_verify'),
            {'cf-turnstile-response': 'invalid-token', 'next': '/protected/'},
        )

        # Should redirect back to challenge with next parameter
        self.assertRedirects(
            response,
            f"{reverse('turnstile_challenge')}?next=/protected/",
            status_code=302,
            target_status_code=200,
        )

    @patch('django_turnstile_site_protect.views.requests.post')
    def test_verify_view_no_token(self, mock_post):
        """Test that verification fails with no token."""
        response = self.client.post(reverse('turnstile_verify'))
        # In the original behavior, it should redirect to the challenge page with next=/
        self.assertRedirects(
            response,
            f"{reverse('turnstile_challenge')}?next=/",
            status_code=302,
            target_status_code=200,
        )
        # Check that the session wasn't modified
        self.assertNotIn('turnstile_passed', self.client.session)

    @patch('django_turnstile_site_protect.views.requests.post')
    def test_verify_view_api_error(self, mock_post):
        """Test verify view when API call raises an exception."""
        # Mock the API to raise an exception
        mock_post.side_effect = Exception('API Error')

        with self.settings(TURNSTILE_SECRET_KEY='test-secret-key'):
            # Use the test client to ensure middleware is executed
            response = self.client.post(
                '/verify/',
                {'cf-turnstile-response': 'test-token', 'next': '/protected/'},
            )

            # Should redirect to the challenge page
            self.assertEqual(response.status_code, 302)
            self.assertIn('challenge', response.url)
            # Should not set the session flag
            session = self.client.session
            self.assertNotIn('turnstile_passed', session)

    @patch('django_turnstile_site_protect.views.requests.post')
    def test_verify_view_with_custom_session_key(self, mock_post):
        """Test verify view with custom session key setting."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response

        custom_key = 'custom_verification_key'

        request = self.factory.post(
            '/verify/', {'cf-turnstile-response': 'test-token', 'next': '/protected/'}
        )
        request.session = {}

        with self.settings(
            TURNSTILE_SECRET_KEY='test-secret-key', TURNSTILE_SESSION_KEY=custom_key
        ):
            # Check that the custom session key was used
            self.assertTrue(request.session.get(custom_key))
            self.assertNotIn('turnstile_passed', request.session)

    @patch('django_turnstile_site_protect.views.requests.post')
    def test_verify_view_with_invalid_http_methods(self, mock_post):
        """Test verify view with unsupported HTTP methods."""
        for method in ['get', 'put', 'delete', 'patch']:
            with self.subTest(method=method):
                request_factory = getattr(self.factory, method)
                request = request_factory('/verify/')
                request.session = {}

                response = verify_view(request)

                # Should redirect to challenge for unsupported methods
                self.assertIsInstance(response, HttpResponseRedirect)
                self.assertEqual(response.url, reverse('turnstile_challenge'))
                # Should not call the API
                mock_post.assert_not_called()

    @patch('django_turnstile_site_protect.views.requests.post')
    def test_verify_view_with_invalid_next_url(self, mock_post):
        """Test verify view with invalid next URL (should be sanitized)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response

        request = self.factory.post(
            '/verify/',
            {
                'cf-turnstile-response': 'test-token',
                'next': 'http://evil.com/steal-data',
            },
        )
        request.session = {}

        with self.settings(TURNSTILE_SECRET_KEY='test-secret-key'):
            response = verify_view(request)

            # Should redirect to root path for invalid next URLs
            self.assertIsInstance(response, HttpResponseRedirect)
            self.assertEqual(response.url, '/')

    def test_verify_view_unsafe_redirect(self):
        """Test that unsafe redirects are prevented."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = {'success': True}

        with patch(
            'django_turnstile_site_protect.views.requests.post',
            return_value=mock_response,
        ):
            # Create a POST request with an unsafe next URL
            request = self.factory.post(
                '/verify/',
                {
                    'cf-turnstile-response': 'test-token',
                    'next': 'http://evil.com/steal-data',
                },
            )
            request.get_host = lambda: 'example.com'  # Required for host validation
            request.session = {}

            response = verify_view(request)

            # Check that we're redirected to the home page, not the unsafe URL
            self.assertIsInstance(response, HttpResponseRedirect)
            self.assertEqual(response.url, '/')
