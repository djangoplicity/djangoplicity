"""
Tools for sending email.
"""

from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives

def mail_images_managers(subject, message, fail_silently=False, connection=None,
                  html_message=None):
    """Sends a message to the image managers, as defined by the IMAGES_MANAGERS setting."""
    if not hasattr(settings, 'IMAGES_MANAGERS'):
        return

    if settings.IMAGES_MANAGERS:
        mail = EmailMultiAlternatives(
            '%s%s' % (settings.EMAIL_SUBJECT_PREFIX, subject), message,
            settings.SERVER_EMAIL, [a[1] for a in settings.IMAGES_MANAGERS],
            connection=connection,
        )
        if html_message:
            mail.attach_alternative(html_message, 'text/html')
        mail.send(fail_silently=fail_silently)
