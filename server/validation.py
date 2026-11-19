"""Small input checks shared by API modules."""
from datetime import date

from .errors import bad_request

CATEGORIES = ("students", "orchestral", "jazz")


def require_text(data: dict, field: str, label: str = None, max_length: int = 5000) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise bad_request(f"Please fill in {label or field}.")
    if len(value) > max_length:
        raise bad_request(f"{(label or field).capitalize()} is too long (limit {max_length} characters).")
    return value.strip()


def optional_text(data: dict, field: str, max_length: int = 5000) -> str:
    value = data.get(field) or ""
    if not isinstance(value, str) or len(value) > max_length:
        raise bad_request(f"'{field}' must be text of at most {max_length} characters.")
    return value.strip()


def require_category(value, label: str = "category") -> str:
    if value not in CATEGORIES:
        raise bad_request(f"The {label} must be one of: {', '.join(CATEGORIES)}.")
    return value


def string_list(data: dict, field: str, limit: int = 50) -> list:
    value = data.get(field) or []
    if not isinstance(value, list) or len(value) > limit or not all(isinstance(v, str) for v in value):
        raise bad_request(f"'{field}' must be a list of text items (at most {limit}).")
    return [v.strip() for v in value if v.strip()]


def require_choice(value, allowed, label: str):
    if value not in allowed:
        raise bad_request(f"The {label} must be one of: {', '.join(allowed)}.")
    return value


def parse_flag(value, label: str) -> bool:
    """True/False from a JSON boolean or a query-string value like 1, 0, true, false."""
    if isinstance(value, bool):
        return value
    if str(value).lower() in ("1", "true", "yes"):
        return True
    if str(value).lower() in ("0", "false", "no"):
        return False
    raise bad_request(f"'{label}' must be true or false.")


def require_date(value, label: str) -> str:
    try:
        date.fromisoformat(str(value))
    except ValueError:
        raise bad_request(f"{label.capitalize()} must be a date like 2026-11-30.")
    return str(value)


def optional_rating(value, label: str):
    """A whole number from 1 to 5, or None."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
        raise bad_request(f"The {label} rating must be a whole number from 1 to 5.")
    return value
