import tomllib
from pathlib import Path

from loop_engineering import __version__


def test_package_version_matches_protocol_version() -> None:
    assert __version__ == "0.3.0"


def test_distribution_registers_only_the_loop_engine_console_script() -> None:
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert metadata["project"]["name"] == "loop-engineering"
    assert metadata["project"]["scripts"] == {
        "loop-engine": "loop_engineering.cli:main"
    }
    assert "loop-engineering" not in metadata["project"]["scripts"]
    assert "loop-agent" not in metadata["project"]["scripts"]
