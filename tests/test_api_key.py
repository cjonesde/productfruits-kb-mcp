"""Locks in how the server finds its API key when the launcher env lacks it.

The environment variable wins. When it is missing or blank, the key is read
from the `pass` store. Any failure to read it yields an empty key so the
server can exit with its own clear message.
"""

import os
import subprocess

os.environ.setdefault("PRODUCTFRUITS_API_KEY", "test-key-for-ci")

from unittest.mock import MagicMock

import server


def _completed(stdout: str) -> MagicMock:
    result = MagicMock(spec=subprocess.CompletedProcess)
    result.stdout = stdout
    return result


def test_env_var_wins_and_pass_is_not_called():
    run = MagicMock()

    key = server.resolve_api_key({"PRODUCTFRUITS_API_KEY": "from-env"}, run)

    assert key == "from-env"
    run.assert_not_called()


def test_missing_env_var_falls_back_to_pass_output():
    run = MagicMock(return_value=_completed("from-pass\n"))

    key = server.resolve_api_key({}, run)

    assert key == "from-pass"
    assert run.call_args.args[0] == ["pass", "show", server.PASS_ENTRY]


def test_blank_env_var_falls_back_to_pass_output():
    run = MagicMock(return_value=_completed("from-pass\n"))

    key = server.resolve_api_key({"PRODUCTFRUITS_API_KEY": "   "}, run)

    assert key == "from-pass"


def test_pass_not_installed_returns_empty_key():
    run = MagicMock(side_effect=FileNotFoundError("pass"))

    assert server.resolve_api_key({}, run) == ""


def test_pass_failure_returns_empty_key():
    run = MagicMock(side_effect=subprocess.CalledProcessError(1, "pass"))

    assert server.resolve_api_key({}, run) == ""


def test_pass_timeout_returns_empty_key():
    run = MagicMock(side_effect=subprocess.TimeoutExpired("pass", 10))

    assert server.resolve_api_key({}, run) == ""
