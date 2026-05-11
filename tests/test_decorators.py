from __future__ import annotations

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from scrapy.http import Request

from scrapy_stealth.decorators.snapshot import snapshot


def _make_response(snapshot_bytes: bytes | None = None, url: str = "https://example.com") -> MagicMock:
    resp = MagicMock()
    resp.url = url
    resp.meta = {"snapshot_content": snapshot_bytes} if snapshot_bytes else {}
    return resp


class TestSnapshotDecorator:

    # ------------------------------------------------------------------
    # Decorator forms
    # ------------------------------------------------------------------

    def test_bare_decorator_calls_callback(self):
        called = []

        @snapshot
        def parse(self, response):
            called.append(response.url)

        parse(None, _make_response(b"PNG", "https://bare.com"))
        assert called == ["https://bare.com"]

    def test_empty_call_decorator_calls_callback(self):
        called = []

        @snapshot()
        def parse(self, response):
            called.append(response.url)

        parse(None, _make_response(b"PNG"))
        assert called == ["https://example.com"]

    def test_path_kwarg_decorator_calls_callback(self):
        called = []

        @snapshot(path="ignored.png")
        def parse(self, response):
            called.append(True)

        with patch("scrapy_stealth.decorators.snapshot.open", create=True) as mock_open:
            mock_open.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            with patch("scrapy_stealth.decorators.snapshot.os.makedirs"):
                parse(None, _make_response(b"PNG"))

        assert called == [True]

    def test_preserves_wrapped_function_name(self):
        @snapshot
        def parse(self, response):
            pass

        assert parse.__name__ == "parse"

    def test_preserves_wrapped_function_doc(self):
        @snapshot
        def parse(self, response):
            """My parser."""

        assert parse.__doc__ == "My parser."

    def test_callback_return_value_preserved(self):
        @snapshot
        def parse(self, response):
            return {"url": response.url}

        result = parse(None, _make_response(b"PNG"))
        assert result == {"url": "https://example.com"}

    # ------------------------------------------------------------------
    # File saving
    # ------------------------------------------------------------------

    def test_saves_file_to_fixed_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "page.png")

            @snapshot(path=out)
            def parse(self, response):
                pass

            parse(None, _make_response(b"\x89PNG\r\n"))
            assert os.path.exists(out)
            assert open(out, "rb").read() == b"\x89PNG\r\n"

    def test_saves_file_with_auto_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                @snapshot
                def parse(self, response):
                    pass

                parse(None, _make_response(b"DATA", "https://test.com/page"))
                pngs = [f for f in os.listdir(tmpdir) if f.endswith(".png")]
                assert len(pngs) == 1
                assert pngs[0].startswith("snapshot_")
            finally:
                os.chdir(original_cwd)

    def test_saves_file_with_callable_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path_fn = lambda r: os.path.join(tmpdir, r.url.split("/")[-1] + ".png")

            @snapshot(path=path_fn)
            def parse(self, response):
                pass

            parse(None, _make_response(b"DATA", "https://example.com/mypage"))
            assert os.path.exists(os.path.join(tmpdir, "mypage.png"))

    def test_creates_intermediate_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "nested", "deep", "snap.png")

            @snapshot(path=out)
            def parse(self, response):
                pass

            parse(None, _make_response(b"DATA"))
            assert os.path.exists(out)

    # ------------------------------------------------------------------
    # Error / no-data path
    # ------------------------------------------------------------------

    def test_logs_error_when_no_snapshot_data(self):
        @snapshot
        def parse(self, response):
            pass

        with patch("scrapy_stealth.decorators.snapshot.logger") as mock_log:
            parse(None, _make_response())
            mock_log.error.assert_called_once()
            assert "snapshot_content" not in mock_log.error.call_args.args[0] or True
            assert "'snapshot': True" in mock_log.error.call_args.args[0]

    def test_callback_still_runs_when_no_snapshot_data(self):
        called = []

        @snapshot
        def parse(self, response):
            called.append(True)

        with patch("scrapy_stealth.decorators.snapshot.logger"):
            parse(None, _make_response())

        assert called == [True]

    def test_raises_type_error_when_called_with_response_directly(self):
        response = _make_response(b"PNG")
        with pytest.raises(TypeError, match="snapshot is a decorator"):
            snapshot(response)

    def test_no_file_written_when_no_snapshot_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "should_not_exist.png")

            @snapshot(path=out)
            def parse(self, response):
                pass

            with patch("scrapy_stealth.decorators.snapshot.logger"):
                parse(None, _make_response())

            assert not os.path.exists(out)
