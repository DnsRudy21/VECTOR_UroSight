from pathlib import Path

from src import config


def test_application_root_is_current_workspace_when_not_frozen():
    assert config.application_root() == Path.cwd()
