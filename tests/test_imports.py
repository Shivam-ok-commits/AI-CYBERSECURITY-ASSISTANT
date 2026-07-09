from src.config import Settings, settings
from src.main import cli


def test_settings_imports():
    assert isinstance(settings, Settings)


def test_cli_imports():
    assert cli.name == "cli"


def test_api_imports():
    from src.api import app
    assert app.title == "AI Cybersecurity Assistant"
