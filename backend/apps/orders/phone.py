import phonenumbers
from django.conf import settings
from django.core.exceptions import ValidationError


def normalize_phone(value: str) -> str:
    try:
        parsed = phonenumbers.parse(value, settings.PHONE_DEFAULT_REGION)
    except phonenumbers.NumberParseException as exc:
        raise ValidationError("Enter a valid phone number.") from exc
    if not phonenumbers.is_valid_number(parsed):
        raise ValidationError("Enter a valid phone number.")
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

