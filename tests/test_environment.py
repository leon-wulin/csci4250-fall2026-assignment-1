"""Check that startup validation rejects incorrect interpreter identities."""
from __future__ import annotations

import runpy
from pathlib import Path

import pytest


@pytest.fixture
def environment_check():
    """Load the standalone script without invoking its main entry point."""
    path = Path(__file__).resolve().parents[1] / "scripts/check_environment.py"
    return runpy.run_path(str(path))


def test_rejects_wrong_python(environment_check, monkeypatch, capsys):
    with monkeypatch.context() as patch:
        patch.setattr(environment_check["sys"], "version_info", (3, 11))
        result = environment_check["check_environment"]()
    assert result == 1
    assert "Expected Python 3.12" in capsys.readouterr().out


def test_rejects_wrong_environment(environment_check, monkeypatch, capsys):
    with monkeypatch.context() as patch:
        patch.setattr(environment_check["sys"], "prefix", "C:/invalid-environment")
        result = environment_check["check_environment"]()
    assert result == 1
    assert "not from named environment fons-a1" in capsys.readouterr().out


def test_rejects_mismatched_conda_prefix(environment_check, monkeypatch, capsys):
    with monkeypatch.context() as patch:
        patch.setenv("CONDA_PREFIX", "C:/invalid-prefix")
        result = environment_check["check_environment"]()
    assert result == 1
    assert "do not agree" in capsys.readouterr().out
