from __future__ import annotations

import asyncio
import random
from typing import Any

from ..utils.core.logger import get_logger
from .patterns import landing_interactions, step_delay_s
from .viewport import ViewportSpec, resolve_viewport

logger = get_logger()

_JS_KEY = """
(key) => {
  const opts = {key, bubbles: true, cancelable: true};
  document.dispatchEvent(new KeyboardEvent('keydown', opts));
  document.dispatchEvent(new KeyboardEvent('keyup', opts));
}
"""


async def _dispatch_mouse_move(page: Any, x: float, y: float) -> None:
    import nodriver.cdp.input_ as input_

    await page.send(input_.dispatch_mouse_event(type_="mouseMoved", x=x, y=y))


async def _dispatch_mouse_wheel(page: Any, x: float, y: float, delta_y: float) -> None:
    import nodriver.cdp.input_ as input_

    await page.send(
        input_.dispatch_mouse_event(
            type_="mouseWheel",
            x=x,
            y=y,
            delta_x=0.0,
            delta_y=delta_y,
        )
    )


async def simulate_hover(
    page: Any,
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    *,
    steps: int = 10,
) -> None:
    """Move the cursor smoothly from start to end via CDP input events."""
    for i in range(steps + 1):
        t = i / steps
        x = start_x + (end_x - start_x) * t
        y = start_y + (end_y - start_y) * t
        await _dispatch_mouse_move(page, x, y)


async def _apply_viewport(page: Any, spec: ViewportSpec) -> None:
    try:
        import nodriver.cdp.emulation as emulation
    except ImportError:
        logger.debug("nodriver CDP emulation unavailable — skipping viewport override")
        return

    await page.send(
        emulation.set_device_metrics_override(
            width=spec.width,
            height=spec.height,
            device_scale_factor=spec.device_scale_factor,
            mobile=spec.mobile,
        )
    )
    if spec.mobile:
        await page.send(emulation.set_touch_emulation_enabled(enabled=True))


async def _run_mouse_path(
    page: Any, path: list[tuple[float, float]], *, mobile: bool
) -> tuple[float, float]:
    if not path:
        return 0.0, 0.0

    last_x, last_y = path[0]
    for x, y in path:
        await _dispatch_mouse_move(page, x, y)
        last_x, last_y = x, y
        await asyncio.sleep(step_delay_s(mobile=mobile))
    return last_x, last_y


async def _run_scrolls(
    page: Any,
    scrolls: list[int],
    *,
    mobile: bool,
    at_x: float,
    at_y: float,
) -> None:
    for delta in scrolls:
        await _dispatch_mouse_wheel(page, at_x, at_y, float(delta))
        await asyncio.sleep(step_delay_s(mobile=mobile))


async def _maybe_keyboard_nudge(page: Any) -> None:
    if random.random() >= 0.35:
        return
    key = "ArrowDown" if random.random() < 0.7 else "Tab"
    await page.evaluate(_JS_KEY, key)


async def apply_viewport_emulation(page: Any, profile: str) -> None:
    spec = resolve_viewport(profile)
    try:
        await _apply_viewport(page, spec)
    except Exception as exc:
        logger.debug("Browser viewport emulation skipped: %s", exc)


async def run_browser_interactions(page: Any, profile: str) -> None:
    spec = resolve_viewport(profile)
    mouse_path, scrolls = landing_interactions(spec)
    try:
        cursor_x, cursor_y = await _run_mouse_path(page, mouse_path, mobile=spec.mobile)
        await _run_scrolls(
            page,
            scrolls,
            mobile=spec.mobile,
            at_x=cursor_x,
            at_y=cursor_y,
        )
        await _maybe_keyboard_nudge(page)
    except Exception as exc:
        logger.debug("Browser interaction replay skipped: %s", exc)


async def run_browser_behavior(page: Any, profile: str) -> None:
    """Apply viewport emulation and replay a human-like interaction preset."""
    await apply_viewport_emulation(page, profile)
    await run_browser_interactions(page, profile)
