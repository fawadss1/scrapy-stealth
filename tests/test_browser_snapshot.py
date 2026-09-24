from __future__ import annotations

import base64
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from scrapy_stealth.utils.browser._core import _cdp_snapshot


@dataclass
class _FakeRect:
    width: float
    height: float


@pytest.mark.asyncio
async def test_cdp_snapshot_full_page_uses_content_clip():
    page = MagicMock()
    metrics = (None, None, None, None, None, _FakeRect(width=800, height=2400))
    png_b64 = base64.b64encode(b"full-page-png").decode()
    page.send = AsyncMock(side_effect=[metrics, png_b64])

    with pytest.MonkeyPatch.context() as mp:
        import nodriver.cdp.page as cdp_page

        mp.setattr(cdp_page, "get_layout_metrics", lambda: "get_layout_metrics")
        captured: dict[str, object] = {}

        def capture_screenshot(**kwargs: object) -> str:
            captured.update(kwargs)
            return "capture_screenshot"

        mp.setattr(cdp_page, "capture_screenshot", capture_screenshot)

        result = await _cdp_snapshot(page)

    assert result == b"full-page-png"
    clip = captured["clip"]
    assert clip.width == 800.0
    assert clip.height == 2400.0
    assert captured["capture_beyond_viewport"] is True
