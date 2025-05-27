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

## License

MIT
