from loop_engineering import __version__


def test_package_version_matches_protocol_version() -> None:
    assert __version__ == "0.2.0"
