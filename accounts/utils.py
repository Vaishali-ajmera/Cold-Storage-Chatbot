import re
from django.conf import settings

def get_user_data(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "preferred_language": user.preferred_language,
        "has_set_preferences": user.has_set_preferences,
        "is_admin": user.is_staff,
        "is_sso_user": user.is_sso_user,
    }


def phone_to_email(phone: str) -> str:
    clean_phone = re.sub(r"[^0-9]", "", phone)
    return f"{clean_phone}@{settings.SSO_EMAIL_DOMAIN}"