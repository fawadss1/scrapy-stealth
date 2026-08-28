import pytest

from scrapy_stealth.behaviors.engine import (
    apply_viewport_emulation,
    run_browser_behavior,
    simulate_hover,
)
from scrapy_stealth.behaviors.patterns import landing_interactions
from scrapy_stealth.behaviors.timing import apply_request_timing
from scrapy_stealth.behaviors.viewport import resolve_viewport


class TestResolveViewport:
    def test_safari_ios_mobile(self):
        spec = resolve_viewport("safari_ios_18_0")
        assert spec.mobile is True
        assert spec.width == 390
        assert spec.device_scale_factor == 3.0

    def test_desktop_profile_stable(self):
        a = resolve_viewport("chrome150")
        b = resolve_viewport("chrome150")
        assert a == b
        assert a.mobile is False

    def test_android_profile(self):
        spec = resolve_viewport("firefox_android_147")
        assert spec.mobile is True
        assert spec.width == 412


class TestLandingInteractions:
    def test_generates_mouse_and_scroll(self):
        spec = resolve_viewport("chrome150")
        mouse, scrolls = landing_interactions(spec)
        assert len(mouse) >= 8
        assert 2 <= len(scrolls) <= 4


class TestApplyRequestTiming:
    def test_sleeps_briefly(self, monkeypatch):
        slept: list[float] = []

        def _fake_sleep(seconds: float) -> None:
            slept.append(seconds)

        monkeypatch.setattr("scrapy_stealth.behaviors.timing.time.sleep", _fake_sleep)
        apply_request_timing("chrome150")
        assert len(slept) == 1
        assert 0.03 <= slept[0] <= 0.43


@pytest.mark.asyncio
async def test_simulate_hover_dispatches_cdp_moves(monkeypatch):
    moves: list[tuple[float, float]] = []

    async def fake_move(page, x, y):
        moves.append((x, y))

    monkeypatch.setattr(
        "scrapy_stealth.behaviors.engine._dispatch_mouse_move",
        fake_move,
    )

    await simulate_hover(object(), 10.0, 20.0, 50.0, 80.0, steps=2)
    assert moves == [(10.0, 20.0), (30.0, 50.0), (50.0, 80.0)]


@pytest.mark.asyncio
async def test_run_mouse_path_dispatches_cdp_moves(monkeypatch):
    moves: list[tuple[float, float]] = []

    async def fake_move(page, x, y):
        moves.append((x, y))

    def _no_sleep(*, mobile: bool) -> float:
        return 0.0

    monkeypatch.setattr(
        "scrapy_stealth.behaviors.engine._dispatch_mouse_move",
        fake_move,
    )
    monkeypatch.setattr("scrapy_stealth.behaviors.engine.step_delay_s", _no_sleep)

    from scrapy_stealth.behaviors.engine import _run_mouse_path

    last_x, last_y = await _run_mouse_path(
        object(), [(1.0, 2.0), (3.0, 4.0)], mobile=False
    )
    assert last_x == 3.0 and last_y == 4.0
    assert moves == [(1.0, 2.0), (3.0, 4.0)]


@pytest.mark.asyncio
async def test_run_browser_behavior_invokes_page(monkeypatch):
    calls: list[str] = []

    async def fake_viewport(page, profile):
        calls.append(f"viewport:{profile}")

    async def fake_interactions(page, profile):
        calls.append(f"interactions:{profile}")

    monkeypatch.setattr(
        "scrapy_stealth.behaviors.engine.apply_viewport_emulation",
        fake_viewport,
    )
    monkeypatch.setattr(
        "scrapy_stealth.behaviors.engine.run_browser_interactions",
        fake_interactions,
    )

    page = object()
    await run_browser_behavior(page, "chrome150")
    assert calls == ["viewport:chrome150", "interactions:chrome150"]


@pytest.mark.asyncio
async def test_apply_viewport_emulation_uses_cdp(monkeypatch):
    sent: list[object] = []

    class FakePage:
        async def send(self, cmd):
            sent.append(cmd)

    async def fake_apply(page, spec):
        sent.append(("apply", spec.width, spec.mobile))

    monkeypatch.setattr("scrapy_stealth.behaviors.engine._apply_viewport", fake_apply)

    await apply_viewport_emulation(FakePage(), "safari_ios_18_0")
    assert sent == [("apply", 390, True)]
