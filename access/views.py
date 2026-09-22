from django.http import Http404


def password_reset_unavailable(request, *args, **kwargs):
    """✨ Every password reset page, refused until email delivery exists (ticket 28). Without a mail server
    allauth's reset form crashes, and the spec promises no email the system cannot send."""
    raise Http404("Password reset is not available.")
