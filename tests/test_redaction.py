from loop_engineering.redaction import REDACTED, redact


def test_redact_recurses_through_mappings_and_lists() -> None:
    value = {
        "Authorization": "Bearer secret-token",
        "nested": [{"api_key": "sk-private"}, "token=abc123"],
        "safe": "visible",
    }

    assert redact(value) == {
        "Authorization": REDACTED,
        "nested": [{"api_key": REDACTED}, "token=[REDACTED]"],
        "safe": "visible",
    }
