from __future__ import annotations

from ..constants import LOGGER_NAME

_SYMBOLS: dict[str, str] = {
    "info": "ℹ️",
    "success": "✅",
    "warning": "⚠️",
    "error": "❌",
    "debug": "🐞",
    "critical": "⛔",
    "wait": "⏳",
    "star": "⭐",
}


class Console:
    """Styled console output with a fixed [scrapy-stealth] prefix."""

    _init_done: bool = False

    def __init__(self, prefix: str = LOGGER_NAME) -> None:
        self._prefix = prefix

    @staticmethod
    def _ensure_init() -> None:
        if not Console._init_done:
            from colorama import init

            init()
            Console._init_done = True

    def _print(
        self,
        message: str,
        *,
        symbol: str = "",
        msg_color: str = "CYAN",
    ) -> None:
        from colorama import Fore, Style

        self._ensure_init()
        prefix = (
            f"{Fore.CYAN}[{Style.RESET_ALL}"
            f"{Style.BRIGHT}{Fore.MAGENTA}{self._prefix}{Style.RESET_ALL}"
            f"{Fore.CYAN}]{Style.RESET_ALL}"
        )
        sym = f"{symbol} " if symbol else ""
        text = f"{getattr(Fore, msg_color)}{sym}{message}{Style.RESET_ALL}"
        print(f"{prefix} {text}")

    def info(self, message: str) -> None:
        self._print(message, symbol=_SYMBOLS["info"])

    def success(self, message: str) -> None:
        self._print(message, symbol=_SYMBOLS["success"], msg_color="GREEN")

    def warning(self, message: str) -> None:
        self._print(message, symbol=_SYMBOLS["warning"], msg_color="YELLOW")

    def error(self, message: str) -> None:
        self._print(message, symbol=_SYMBOLS["error"], msg_color="RED")

    def critical(self, message: str) -> None:
        self._print(message, symbol=_SYMBOLS["critical"], msg_color="RED")

    def debug(self, message: str) -> None:
        self._print(message, symbol=_SYMBOLS["debug"], msg_color="WHITE")

    def wait(self, message: str) -> None:
        self._print(message, symbol=_SYMBOLS["wait"], msg_color="LIGHTYELLOW_EX")

    def star(self, message: str) -> None:
        self._print(message, symbol=_SYMBOLS["star"], msg_color="LIGHTMAGENTA_EX")


console = Console()
