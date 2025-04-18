from django.urls import path
from .views import challenge_view, verify_view


urlpatterns = [
    path('challenge/', challenge_view, name='turnstile_challenge'),
    path('verify/', verify_view, name='turnstile_verify'),
]
