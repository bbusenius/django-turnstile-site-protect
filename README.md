# Django Turnstile Site Protect

A Django package for site-wide protection using Cloudflare Turnstile. This package helps protect entire Django sites from AI bots by presenting a Turnstile challenge to users on their first visit.

## Features

- Simple integration with any Django project
- Site-wide protection with Cloudflare Turnstile
- Session-based authentication to avoid challenging verified users
- Customizable challenge page
- Support for multiple Turnstile modes (Managed, Non-Interactive, Invisible)

## Installation

```bash
pip install git+https://github.com/USERNAME/django-turnstile-site-protect.git@main
```

Or add to your requirements.txt:

```
git+https://github.com/USERNAME/django-turnstile-site-protect.git@main
```

## Quick Start

1. First, obtain your Cloudflare Turnstile site key and secret key from the [Cloudflare Dashboard](https://dash.cloudflare.com/?to=/:account/turnstile).

2. Add `django_turnstile_site_protect` to your `INSTALLED_APPS` in settings.py:

   ```python
   INSTALLED_APPS = [
       # ...
       'django_turnstile_site_protect',
       # ...
   ]
   ```

3. Add the Turnstile middleware to your `MIDDLEWARE` in settings.py (after SessionMiddleware):

   ```python
   MIDDLEWARE = [
       # ...
       'django.contrib.sessions.middleware.SessionMiddleware',
       # ...
       'django_turnstile_site_protect.middleware.TurnstileMiddleware',
       # ...
   ]
   ```

4. Configure Turnstile settings in settings.py:

   ```python
   # Cloudflare Turnstile settings
   TURNSTILE_SITE_KEY = 'your_site_key_here'
   TURNSTILE_SECRET_KEY = 'your_secret_key_here'
   TURNSTILE_VERIFICATION_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
   TURNSTILE_SESSION_KEY = 'turnstile_passed'  # Optional, default is 'turnstile_passed'
   TURNSTILE_MODE = 'managed'  # Optional, default is 'managed'
   ```

5. Include the Turnstile URLs in your project's urls.py:

   ```python
   from django.urls import path, include

   urlpatterns = [
       # ...
       path('turnstile/', include('django_turnstile_site_protect.urls')),
       # ...
   ]
   ```

## Customization

You can customize the challenge page by overriding the template. Create a file at:

```
templates/django_turnstile_site_protect/challenge.html
```

And include your custom HTML while ensuring the Turnstile widget is included.

## Settings

### Config options

- `TURNSTILE_SITE_KEY`: Your Cloudflare Turnstile site key (required)
- `TURNSTILE_SECRET_KEY`: Your Cloudflare Turnstile secret key (required)
- `TURNSTILE_VERIFICATION_URL`: URL for token verification (optional, defaults to 'https://challenges.cloudflare.com/turnstile/v0/siteverify')
- `TURNSTILE_SESSION_KEY`: Session key to store verification status (optional, defaults to 'turnstile_passed')
- `TURNSTILE_MODE`: Turnstile widget mode (optional, defaults to 'managed', can be 'managed', 'non-interactive', or 'invisible')
- `TURNSTILE_APPEARANCE`: When to show the widget (optional, defaults to 'always', can be 'always', 'execute', or 'interaction-only')
- `TURNSTILE_THEME`: Widget theme (optional, defaults to 'auto', can be 'auto', 'light', or 'dark')
- `TURNSTILE_LANGUAGE`: Widget language (optional, defaults to 'auto')
- `TURNSTILE_SIZE`: Widget size (optional, defaults to 'normal', can be 'normal' or 'compact')
- `TURNSTILE_EXCLUDED_PATHS`: List of URL paths to exclude from protection (optional, defaults to [])
- `TURNSTILE_EXCLUDED_IPS`: List of IP addresses or IP ranges to exclude from protection (optional, defaults to []). Supports both individual IPs and ranges in the format `start_ip-end_ip`.
- `TURNSTILE_EXCLUDED_DOMAINS`: List of domain names to exclude from protection (optional, defaults to []). Supports exact matches and wildcard subdomains using the format `*.example.com`.

### Environment variables

- `TURNSTILE_ENABLED`: Toggle to enable/disable the middleware (optional, defaults to 'True'). Set to 'False' to disable the middleware. This is useful for unit tests in CI environments.

## Disabling the Middleware for Testing

For unit tests, especially in CI environments, you may want to disable the Turnstile middleware to prevent test failures due to Turnstile challenges. You can do this by setting the `TURNSTILE_ENABLED` environment variable to `False`:

```python
# In your test setup code
import os
os.environ['TURNSTILE_ENABLED'] = 'False'
```

Or in your CI configuration file:

```yaml
env:
  TURNSTILE_ENABLED: 'False'
```

Accepted values to disable the middleware are (case-insensitive):
- `False`
- `0`
- `no`
- `off`

Any other value (or if the variable is not set) will keep the middleware enabled.

## Session Management

This package uses Django's built-in session framework to track whether a user has passed the Turnstile challenge. The following information will help you manage these sessions effectively:

### Session Duration

By default, Django sessions last for 2 weeks. You can customize this by setting `SESSION_COOKIE_AGE` in your project's settings.py:

```python
# Set session duration to 1 day (in seconds)
SESSION_COOKIE_AGE = 86400
```

Note that changing this setting will only affect new sessions - existing sessions will retain their original expiration time.

Other relevant Django session settings:

```python
# If set to True, sessions expire when the user closes their browser
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Default is False

# If True, cookies will only be sent via HTTPS connections
SESSION_COOKIE_SECURE = True  # Recommended for production

# If True, prevents JavaScript from accessing the session cookie
SESSION_COOKIE_HTTPONLY = True  # Recommended for security

# Change the name of the session cookie
SESSION_COOKIE_NAME = 'sessionid'  # Default is 'sessionid'
```

### Cleaning Up Expired Sessions

If you're using database-backed sessions (the default), you should periodically run Django's `clearsessions` management command to remove expired sessions from the database:

```bash
python manage.py clearsessions
```

Consider setting up a cron job to run this command daily:

```
0 3 * * * cd /path/to/your/django/project && /path/to/your/python /path/to/your/manage.py clearsessions
```

### Clearing All Sessions

In some cases, you may want to invalidate all existing sessions (for example, after changing security settings). You can do this with:

```python
from django.contrib.sessions.models import Session
Session.objects.all().delete()
```

This will log out all users and force them to complete the Turnstile challenge again on their next visit.

## IP Address Exemptions

You can exempt specific IP addresses or IP ranges from the Turnstile challenge. This is useful for:

- Allowing internal networks to access the site without verification
- Bypassing verification for specific trusted locations
- Development and testing environments

To configure IP exemptions, add the `TURNSTILE_EXCLUDED_IPS` setting to your settings.py:

```python
TURNSTILE_EXCLUDED_IPS = [
    # Individual IPs
    '192.168.1.100',
    '10.0.0.1',
    
    # IP ranges in the format 'start_ip-end_ip'
    '192.168.1.0-192.168.1.255',    # Entire /24 subnet
    '10.0.0.0-10.255.255.255',      # All private 10.x.x.x addresses
    '172.16.0.0-172.31.255.255',    # Private IP range
    
    # For local development
    '127.0.0.1',
    '::1',  # IPv6 localhost
]
```

When a user connects from one of these IP addresses, they will bypass the Turnstile challenge completely.

### How It Works

The middleware checks the client's IP address against the configured list:

1. First, it looks at the `X-Forwarded-For` header (commonly set by proxies and load balancers)
2. If that's not available, it falls back to `REMOTE_ADDR`
3. It then checks if the IP matches any individual IP or falls within any of the configured ranges

IPs are converted to their integer representation internally for efficient range checking.

## Domain Exemptions

For multisite installations (like Wagtail sites with public and intranet instances), you can exempt specific domains from Turnstile verification. This is particularly useful when one site needs protection while the other doesn't, for example:

- When running public and intranet sites on the same codebase
- When intranet sites already have authentication requirements
- For development or staging environments on specific domains

To configure domain exemptions, add the `TURNSTILE_EXCLUDED_DOMAINS` setting to your settings.py:

```python
TURNSTILE_EXCLUDED_DOMAINS = [
    # Exact domain matches
    'intranet.example.org',
    'staff.example.org',
    
    # Wildcard subdomains
    '*.internal.example.org',  # Exempts any.internal.example.org, but not internal.example.org itself
]
```

When a user visits a site with one of these domains, they will bypass the Turnstile challenge completely.

### How It Works

The middleware checks the request's host against the configured list:

1. First, it extracts the hostname from the request (removing any port number)
2. It then checks for exact matches against the list of excluded domains
3. For wildcard entries (starting with `*.`), it checks if the hostname is a subdomain of the specified domain

This allows granular control over which sites or subdomains require Turnstile verification.

## Wagtail Cache

If you're using this package with [wagtail-cache](https://github.com/coderedcorp/wagtail-cache), you need to ensure that both the `SessionMiddleware` and `TurnstileMiddleware` come **before** the Wagtail Cache middleware in your `MIDDLEWARE` config:

```python
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',  # This must come first
    'django_turnstile_site_protect.middleware.TurnstileMiddleware',  # Then Turnstile
    'wagtailcache.cache.UpdateCacheMiddleware',  # Then Wagtail Cache
    # ... other middleware ...
    'wagtailcache.cache.FetchFromCacheMiddleware',
]
```

This order ensures that:
1. Sessions are loaded before any caching decisions are made
2. Turnstile verification checks run before caching
3. Redirects to the challenge page happen before content is served from or saved to the cache

## Testing

The package includes a comprehensive test suite covering middleware functionality, views, and configuration handling. To run the tests, you'll need pytest and its Django plugin.

### Prerequisites

All testing dependencies are included in the `requirements-dev.txt` file. Install them with:

```bash
pip install -r requirements-dev.txt
```

### Running Tests

Run all tests:

```bash
python -m pytest -v
```

Run specific test modules:

```bash
# Test middleware only
python -m pytest django_turnstile_site_protect/tests/test_middleware.py

# Test views only
python -m pytest django_turnstile_site_protect/tests/test_views.py
```

### Testing Notes

- Tests automatically disable the middleware using environment variables
- The test suite mocks external API calls to Cloudflare

## License

MIT
