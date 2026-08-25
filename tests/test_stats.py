from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scrapy_stealth.config import config
from scrapy_stealth.utils.telemetry.stats import StealthStats, proxy_host_for_stats


class TestProxyHostForStats:
    def test_strips_credentials(self):
        assert (
            proxy_host_for_stats("https://user:pass@dc.oxylabs.io:8000")
            == "dc.oxylabs.io:8000"
        )

    def test_none_and_empty(self):
        assert proxy_host_for_stats(None) is None
        assert proxy_host_for_stats("") is None


class TestStealthStats:
    def test_noop_without_collector(self):
        s = StealthStats(None)
        s.inc("stealth/bans")
        s.set("stealth/profile", "chrome_147")
        s.set_proxy("http://user:pass@proxy:8080")

    def test_inc_and_set(self):
        collector = MagicMock()
        s = StealthStats(collector)
        s.inc("stealth/bans", 2)
        collector.inc_value.assert_called_with("stealth/bans", 2)
        s.set("stealth/ban_streak", 3)
        collector.set_value.assert_called_with("stealth/ban_streak", 3)

    def test_set_proxy_redacts_credentials(self):
        collector = MagicMock()
        s = StealthStats(collector)
        s.set_proxy("http://user:secret@proxy.example:8080")
        collector.set_value.assert_called_with("stealth/proxy", "proxy.example:8080")

    def test_record_request_and_ban(self):
        collector = MagicMock()
        s = StealthStats(collector)
        s.record_request("basic")
        s.record_ban("basic", streak=2, banned=True)
        assert collector.inc_value.call_count >= 4

    def test_records_success_response_and_status(self):
        collector = MagicMock()
        s = StealthStats(collector)
        s.record_response("turbo", status=200, banned=False)
        keys = [call.args[0] for call in collector.inc_value.call_args_list]
        assert "stealth/responses" in keys
        assert "stealth/responses/turbo" in keys
        assert "stealth/status/200" in keys
        assert "stealth/successes" in keys
        assert "stealth/successes/turbo" in keys
        assert "stealth/failures" not in keys

    def test_banned_200_is_failure_not_success(self):
        collector = MagicMock()
        s = StealthStats(collector)
        s.record_response("browser", status=200, banned=True)
        keys = [call.args[0] for call in collector.inc_value.call_args_list]
        assert "stealth/failures" in keys
        assert "stealth/failures/browser" in keys
        assert "stealth/successes" not in keys

    def test_records_dns_only_when_active(self):
        collector = MagicMock()
        s = StealthStats(collector)
        s.record_dns("basic", 0)
        assert collector.inc_value.call_count == 0
        collector.set_value.assert_called_with("stealth/dns/active_hosts", 0)

        s.record_dns("basic", 2)
        keys = [call.args[0] for call in collector.inc_value.call_args_list]
        assert "stealth/dns/requests" in keys
        assert "stealth/dns/requests/basic" in keys
        collector.inc_value.assert_any_call("stealth/dns/hosts", 2)

    def test_records_proxy_request(self):
        collector = MagicMock()
        s = StealthStats(collector)
        s.record_proxy_request("turbo")
        collector.inc_value.assert_any_call("stealth/proxy/requests", 1)
        collector.inc_value.assert_any_call("stealth/proxy/requests/turbo", 1)

    def test_records_proxy_connection_failure(self):
        collector = MagicMock()
        s = StealthStats(collector)
        s.record_proxy_connection_failure(
            "turbo", "http://user:secret@dc.oxylabs.io:8000"
        )
        collector.inc_value.assert_any_call("stealth/proxy/connection_failures", 1)
        collector.inc_value.assert_any_call(
            "stealth/proxy/connection_failures/turbo", 1
        )
        collector.set_value.assert_any_call(
            "stealth/proxy/last_connection_failure", "dc.oxylabs.io:8000"
        )

    def test_records_proxy_cooldown_and_rotation(self):
        collector = MagicMock()
        s = StealthStats(collector)
        s.record_proxy_cooldown("basic", "http://user:pass@proxy.example:8080")
        s.record_proxy_rotation("basic")
        collector.inc_value.assert_any_call("stealth/proxy/cooldowns", 1)
        collector.inc_value.assert_any_call("stealth/proxy/cooldowns/basic", 1)
        collector.set_value.assert_any_call(
            "stealth/proxy/last_cooldown", "proxy.example:8080"
        )
        collector.inc_value.assert_any_call("stealth/proxy/rotations", 1)
        collector.inc_value.assert_any_call("stealth/proxy/rotations/basic", 1)


def _make_mock_client(status=200, content=b"<html><body>ok</body></html>"):
    mock_status = MagicMock()
    mock_status.as_int.return_value = status
    mock_resp = MagicMock()
    mock_resp.status = mock_status
    mock_resp.bytes.return_value = content
    mock_resp.headers = {}
    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp
    mock_client.post.return_value = mock_resp
    return mock_client


class TestBasicEngineStats:
    def test_records_bans_and_recycle(self, monkeypatch):
        pytest.importorskip("wreq")
        from scrapy.http import Request

        from scrapy_stealth.engines.basic import BasicEngine

        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 2)
        monkeypatch.setattr(config, "STEALTH_RECYCLE_COOLDOWN_S", 0.0)
        monkeypatch.setattr(config, "STEALTH_PROXIES", [])

        collector = MagicMock()
        values: dict = {}

        def inc_value(key, count=1):
            values[key] = values.get(key, 0) + count

        def set_value(key, value):
            values[key] = value

        collector.inc_value.side_effect = inc_value
        collector.set_value.side_effect = set_value

        mock_cls = MagicMock(return_value=_make_mock_client(status=403))
        with patch("scrapy_stealth.engines.basic.Client", mock_cls):
            engine = BasicEngine(profile="chrome_147")
            engine.set_stats(collector)
            meta_proxy = "https://user:pass@dc.oxylabs.io:8000"
            req = Request(
                "https://example.com",
                meta={"stealth": {"proxy": meta_proxy}},
            )
            engine._execute(req)
            engine._execute(req)

        assert values.get("stealth/bans") == 2
        assert values.get("stealth/bans/basic") == 2
        assert values.get("stealth/responses") == 2
        assert values.get("stealth/failures") == 2
        assert values.get("stealth/status/403") == 2
        assert values.get("stealth/proxy/requests") == 2
        assert values.get("stealth/recycles") == 1
        assert values.get("stealth/recycles/basic") == 1
        assert values.get("stealth/proxy") == "dc.oxylabs.io:8000"
        assert values.get("stealth/profile") is not None

    def test_clean_response_resets_streak_stat(self, monkeypatch):
        pytest.importorskip("wreq")
        from scrapy.http import Request

        from scrapy_stealth.engines.basic import BasicEngine

        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 5)
        collector = MagicMock()
        values: dict = {}
        collector.inc_value.side_effect = lambda k, c=1: values.__setitem__(
            k, values.get(k, 0) + c
        )
        collector.set_value.side_effect = lambda k, v: values.__setitem__(k, v)

        mock_cls = MagicMock(return_value=_make_mock_client(status=200))
        with patch("scrapy_stealth.engines.basic.Client", mock_cls):
            engine = BasicEngine()
            engine.set_stats(collector)
            engine._execute(Request("https://example.com"))

        assert values.get("stealth/ban_streak") == 0
        assert values.get("stealth/bans", 0) == 0
        assert values.get("stealth/responses") == 1
        assert values.get("stealth/successes") == 1
        assert values.get("stealth/status/200") == 1

    def test_records_effective_dns_usage(self, monkeypatch):
        pytest.importorskip("wreq")
        from scrapy.http import Request

        from scrapy_stealth.engines.basic import BasicEngine

        monkeypatch.setattr(config, "STEALTH_DNS_OVERRIDES", {})
        collector = MagicMock()
        values: dict = {}
        collector.inc_value.side_effect = lambda k, c=1: values.__setitem__(
            k, values.get(k, 0) + c
        )
        collector.set_value.side_effect = lambda k, v: values.__setitem__(k, v)

        mock_cls = MagicMock(return_value=_make_mock_client(status=200))
        with patch("scrapy_stealth.engines.basic.Client", mock_cls):
            engine = BasicEngine()
            engine.set_stats(collector)
            engine._execute(
                Request(
                    "https://example.com",
                    meta={"stealth": {"dns": "203.0.113.10"}},
                )
            )

        assert values.get("stealth/dns/requests") == 1
        assert values.get("stealth/dns/requests/basic") == 1
        assert values.get("stealth/dns/hosts") == 1
        assert values.get("stealth/dns/active_hosts") == 1
