import re
from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "[REDACTED]"
SENSITIVE_KEYS = {
    "authorization",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "password",
    "secret",
    "token",
}
INLINE_SECRET = re.compile(
    r"(?i)(bearer\s+|(?:api[_-]?key|token|password|secret)\s*[=:]\s*)\S+"
)
PRIVATE_KEY = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.DOTALL,
)


def redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): REDACTED if str(key).lower() in SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact(item) for item in value]
    if isinstance(value, str):
        without_keys = PRIVATE_KEY.sub(REDACTED, value)
        return INLINE_SECRET.sub(lambda match: f"{match.group(1)}{REDACTED}", without_keys)
    return value
