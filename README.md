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

## License

MIT
