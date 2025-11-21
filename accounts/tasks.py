from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def _send_email(subject, template, context, recipient):
    html_message = render_to_string(template, context)
    plain_message = strip_tags(html_message)
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        html_message=html_message,
        fail_silently=False,
    )


@shared_task(bind=True, max_retries=3)
def send_welcome_email_task(self, email, full_name):
    try:
        _send_email(
            "Welcome to Potato Bazaar News Scraper",
            "emails/welcome_email.html",
            {"full_name": full_name},
            email,
        )
        return f"Welcome email sent to {email}"
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_forgot_password_email_task(self, email, user_name, otp, expiry_minutes):
    """
    Send OTP email for password reset
    """
    try:
        _send_email(
            subject="Password Reset OTP",
            template="emails/forgot_password.html",
            context={
                "user_name": user_name,
                "otp": otp,
                "expiry_minutes": expiry_minutes,
            },
            recipient=email,
        )
        return f"Password reset OTP sent to {email}"

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_password_reset_success_email_task(self, email, user_name):
    """
    Send confirmation email after successful password reset
    """
    try:
        _send_email(
            subject="Password Reset Successful",
            template="emails/password_reset_success.html",
            context={"user_name": user_name},
            recipient=email,
        )
        return f"Password reset confirmation sent to {email}"

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))
