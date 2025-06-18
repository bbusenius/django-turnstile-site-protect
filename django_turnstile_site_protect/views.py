import requests
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


def challenge_view(request):
    """
    Render the Turnstile challenge page.
    """
    # Get next URL from query parameters or default to homepage
    next_url = request.GET.get('next', '/')

    # Get Turnstile configuration from settings
    site_key = getattr(settings, 'TURNSTILE_SITE_KEY', '')
    mode = getattr(settings, 'TURNSTILE_MODE', 'managed')
    appearance = getattr(settings, 'TURNSTILE_APPEARANCE', 'always')
    theme = getattr(settings, 'TURNSTILE_THEME', 'auto')
    language = getattr(settings, 'TURNSTILE_LANGUAGE', 'auto')
    size = getattr(settings, 'TURNSTILE_SIZE', 'normal')

    context = {
        'site_key': site_key,
        'next_url': next_url,
        'mode': mode,
        'appearance': appearance,
        'theme': theme,
        'language': language,
        'size': size,
    }

    return render(request, 'django_turnstile_site_protect/challenge.html', context)


def verify_view(request):
    """
    Verify the Turnstile token and redirect to the original page if successful.
    """
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('turnstile_challenge'))

    # Get the token from the form submission
    token = request.POST.get('cf-turnstile-response')

    # Get the next URL for redirection after verification
    next_url = request.POST.get('next', '/')

    # If no token is provided, redirect back to the challenge page
    if not token:
        return HttpResponseRedirect(f"{reverse('turnstile_challenge')}?next={next_url}")

    # Get the secret key and verification URL from settings
    secret_key = getattr(settings, 'TURNSTILE_SECRET_KEY', '')
    verification_url = getattr(
        settings,
        'TURNSTILE_VERIFICATION_URL',
        'https://challenges.cloudflare.com/turnstile/v0/siteverify',
    )
    session_key = getattr(settings, 'TURNSTILE_SESSION_KEY', 'turnstile_passed')

    # Verify the token with Cloudflare Turnstile API
    data = {
        'secret': secret_key,
        'response': token,
        'remoteip': request.META.get('REMOTE_ADDR', ''),
    }

    try:
        response = requests.post(verification_url, data=data)
        result = response.json()

        # If verification is successful, set the session flag and redirect
        if result.get('success'):
            request.session[session_key] = True

            # Ensure the URL is safe before redirecting
            if url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}
            ):
                return HttpResponseRedirect(next_url)
            else:
                return HttpResponseRedirect('/')
    except Exception:
        # Log the error or handle it as needed
        pass

    # If verification fails or an error occurs, redirect back to the challenge page
    return HttpResponseRedirect(f"{reverse('turnstile_challenge')}?next={next_url}")
