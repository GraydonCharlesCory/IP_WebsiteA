"""Small input checks shared by API modules."""
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
