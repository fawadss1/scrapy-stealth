import json
from unittest.mock import MagicMock, patch

import pytest

from scrapy_stealth.utils import updates


def _pypi_payload(version: str, project_url: str | None = None) -> dict:
    return {
        "info": {
            "version": version,
            "project_url": project_url or "https://pypi.org/project/scrapy-stealth/",
        }
    }


class TestGetUpdateUrl:
    def test_returns_none_when_current_is_latest(self):
        payload = _pypi_payload("1.0.0")
        with patch.object(updates, "latest_pypi_release", return_value=payload):
            assert updates.get_update_url("1.0.0") is None

    def test_returns_url_when_newer_release_exists(self):
        payload = _pypi_payload("2.0.0")
        with patch.object(updates, "latest_pypi_release", return_value=payload):
            url = updates.get_update_url("1.0.0")
        assert url == "https://pypi.org/project/scrapy-stealth/2.0.0/"

    def test_handles_prerelease_versions(self):
        payload = _pypi_payload("0.7.0")
        with patch.object(updates, "latest_pypi_release", return_value=payload):
            assert (
                updates.get_update_url("0.6.10a1")
                == "https://pypi.org/project/scrapy-stealth/0.7.0/"
            )

    def test_silent_fail_on_network_error(self):
        with patch.object(
            updates,
            "latest_pypi_release",
            side_effect=OSError("network down"),
        ):
            assert updates.get_update_url("1.0.0") is None

    def test_raises_when_silent_fail_disabled(self):
        with patch.object(
            updates,
            "latest_pypi_release",
            side_effect=OSError("network down"),
        ):
            with pytest.raises(OSError, match="network down"):
                updates.get_update_url("1.0.0", silent_fail=False)


class TestLatestPypiRelease:
    def test_fetches_pypi_project_json(self):
        payload = _pypi_payload("1.2.3")
        body = json.dumps(payload).encode()

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self):
                return body

        with patch("urllib.request.urlopen", return_value=FakeResponse()) as mock_open:
            result = updates.latest_pypi_release("scrapy-stealth")

        assert result == payload
        request = mock_open.call_args.args[0]
        assert request.full_url == "https://pypi.org/pypi/scrapy-stealth/json"


class TestUpdateAvailable:
    def setup_method(self):
        updates._reset_update_check_state()

    def teardown_method(self):
        updates._reset_update_check_state()

    def test_runs_check_once_per_process(self):
        def run_target_immediately(*, target, **kwargs):
            target()
            return MagicMock()

        with (
            patch.object(updates, "get_update_url", return_value=None) as mock_check,
            patch.object(
                updates.threading, "Thread", side_effect=run_target_immediately
            ),
        ):
            updates.update_available()
            updates.update_available()
        mock_check.assert_called_once()

    def test_notifies_when_update_exists(self):
        url = "https://pypi.org/project/scrapy-stealth/9.9.9/"
        with (
            patch.object(updates, "get_update_url", return_value=url),
            patch("scrapy_stealth.utils.console.console") as mock_console,
        ):
            updates._notify_if_update_available()

        mock_console.info.assert_called_once()
        message = mock_console.info.call_args.args[0]
        assert url in message
        assert "pip install -U scrapy-stealth" in message
