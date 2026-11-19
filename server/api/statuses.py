"""Application statuses and how the v1 names and review decisions map onto them."""
from ..errors import bad_request

STATUS_LABELS = {
    "submitted": "Submitted", "shortlisted": "Shortlisted", "callback": "Callback", "not_selected": "Not selected",
}
LEGACY_STATUS_NAMES = {"new": "submitted", "passed": "not_selected"}  # v1 names, still accepted in filters
DECISION_TO_STATUS = {"shortlist": "shortlisted", "pass": "not_selected"}


def parse_status(value, extra: tuple = ()) -> str:
    """A status key (v1 names accepted), or one of `extra`; 400 with the allowed values otherwise."""
    value = LEGACY_STATUS_NAMES.get(value, value)
    if value not in STATUS_LABELS and value not in extra:
        raise bad_request(f"Status must be one of: {', '.join((*STATUS_LABELS, *extra))}.")
    return value
