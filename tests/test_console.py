import re

import pytest

from scrapy_stealth.constants import LOGGER_NAME
from scrapy_stealth.utils.core.console import Console, console


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


class TestConsoleInit:
    def test_default_prefix_from_logger_name(self):
        c = Console()
        assert c._prefix == LOGGER_NAME

    def test_custom_prefix(self):
        c = Console(prefix="my-app")
        assert c._prefix == "my-app"

    def test_module_instance_is_console(self):
        assert isinstance(console, Console)

    def test_module_instance_uses_default_prefix(self):
        assert console._prefix == LOGGER_NAME

    def test_init_done_flag_is_class_level(self):
        c1 = Console()
        c2 = Console()
        Console._init_done = False
        c1._ensure_init()
        assert c2._init_done is True  # shared across instances


class TestConsolePrint:
    def test_prefix_appears_in_output(self, capsys):
        c = Console(prefix="test-app")
        c.info("hello")
        out = strip_ansi(capsys.readouterr().out)
        assert "[test-app]" in out

    def test_message_appears_in_output(self, capsys):
        c = Console()
        c.info("test message")
        out = strip_ansi(capsys.readouterr().out)
        assert "test message" in out

    def test_no_symbol_no_leading_space(self, capsys):
        c = Console()
        c._print("plain")
        out = strip_ansi(capsys.readouterr().out)
        assert "plain" in out
        # symbol space should not appear before message
        assert "  plain" not in out


class TestSemanticMethods:
    @pytest.mark.parametrize(
        "method, symbol",
        [
            ("info", "ℹ️"),
            ("success", "✅"),
            ("warning", "⚠️"),
            ("error", "❌"),
            ("critical", "⛔"),
            ("debug", "🐞"),
            ("wait", "⏳"),
            ("star", "⭐"),
        ],
    )
    def test_symbol_in_output(self, capsys, method, symbol):
        c = Console()
        getattr(c, method)("msg")
        out = capsys.readouterr().out
        assert symbol in out

    @pytest.mark.parametrize(
        "method",
        ["info", "success", "warning", "error", "critical", "debug", "wait", "star"],
    )
    def test_message_in_output(self, capsys, method):
        c = Console()
        getattr(c, method)("check message")
        out = strip_ansi(capsys.readouterr().out)
        assert "check message" in out

    def test_each_method_produces_one_line(self, capsys):
        c = Console()
        for method in (
            "info",
            "success",
            "warning",
            "error",
            "critical",
            "debug",
            "wait",
            "star",
        ):
            getattr(c, method)("x")
            out = capsys.readouterr().out
            assert out.count("\n") == 1
