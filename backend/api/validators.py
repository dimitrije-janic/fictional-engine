import re
from ipaddress import ip_address, AddressValueError

# Keep in sync with ServerState enum in models.py
VALID_STATES = {"active", "offline", "retired"}

# RFC 1123 compliant label pattern: alphanumeric, hyphens in middle, max 63 chars
_LABEL_PATTERN = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$')


def validate_ip_address(ip: str) -> bool:
    try:
        ip_address(ip)
        return True
    except (AddressValueError, ValueError):
        return False


def validate_state(state: str) -> bool:
    return state in VALID_STATES


def validate_hostname(hostname: str) -> bool:
    """
    Validate hostname according to RFC 1123.

    Rules:
    - Total length: 1-255 characters
    - Each label (segment between dots): 1-63 characters
    - Labels must start and end with alphanumeric
    - Labels can contain hyphens in the middle
    - No consecutive dots allowed
    """
    if not hostname or len(hostname) > 255:
        return False

    # Split into labels and validate each
    labels = hostname.split('.')

    # Check for empty labels (consecutive dots or leading/trailing dots)
    if any(label == '' for label in labels):
        return False

    return all(_LABEL_PATTERN.match(label) for label in labels)
