import pytest

from scrapy_stealth.utils.headers import get_default_headers, merge_headers


# ---------------------------------------------------------------------------
# get_default_headers
# ---------------------------------------------------------------------------

class TestGetDefaultHeaders:
    def test_chrome_returns_chromium_headers(self):
        hdrs = get_default_headers("chrome_137")
        assert "Sec-Fetch-Dest" in hdrs
        assert "Sec-Fetch-Mode" in hdrs
        assert "Cache-Control" in hdrs

    def test_edge_returns_chromium_headers(self):
        hdrs = get_default_headers("edge_134")
        assert "Sec-Fetch-Dest" in hdrs

    def test_opera_returns_chromium_headers(self):
        hdrs = get_default_headers("opera_119")
        assert "Sec-Fetch-Dest" in hdrs

    def test_firefox_returns_firefox_headers(self):
        hdrs = get_default_headers("firefox_139")
        assert hdrs["Accept-Language"] == "en-US,en;q=0.5"
        assert "Sec-Fetch-Dest" in hdrs

    def test_safari_has_no_sec_fetch_headers(self):
        hdrs = get_default_headers("safari_18_5")
        assert "Sec-Fetch-Dest" not in hdrs
        assert "Sec-Fetch-Mode" not in hdrs
        assert "Sec-Fetch-Site" not in hdrs

    def test_safari_ios_has_no_sec_fetch_headers(self):
        hdrs = get_default_headers("safari_ios_18_1_1")
        assert "Sec-Fetch-Dest" not in hdrs

    def test_okhttp_is_minimal(self):
        hdrs = get_default_headers("okhttp_5")
        assert hdrs["Accept"] == "*/*"
        assert "Sec-Fetch-Dest" not in hdrs
        assert "Accept-Language" not in hdrs

    def test_unknown_profile_falls_back_to_chromium(self):
        hdrs = get_default_headers("unknown_browser_99")
        assert "Sec-Fetch-Dest" in hdrs

    def test_chrome_accept_includes_avif(self):
        hdrs = get_default_headers("chrome_137")
        assert "image/avif" in hdrs["Accept"]

    def test_firefox_accept_excludes_signed_exchange(self):
        hdrs = get_default_headers("firefox_139")
        assert "signed-exchange" not in hdrs["Accept"]


# ---------------------------------------------------------------------------
# sec-ch-ua
# ---------------------------------------------------------------------------

class TestSecChUa:
    def test_chrome_has_sec_ch_ua(self):
        hdrs = get_default_headers("chrome_137")
        assert "sec-ch-ua" in hdrs

    def test_chrome_version_in_sec_ch_ua(self):
        hdrs = get_default_headers("chrome_137")
        assert '"Google Chrome";v="137"' in hdrs["sec-ch-ua"]
        assert '"Chromium";v="137"' in hdrs["sec-ch-ua"]

    def test_chrome_130_version_in_sec_ch_ua(self):
        hdrs = get_default_headers("chrome_130")
        assert '"Google Chrome";v="130"' in hdrs["sec-ch-ua"]

    def test_edge_brand_in_sec_ch_ua(self):
        hdrs = get_default_headers("edge_134")
        assert '"Microsoft Edge"' in hdrs["sec-ch-ua"]

    def test_opera_brand_in_sec_ch_ua(self):
        hdrs = get_default_headers("opera_119")
        assert '"Opera"' in hdrs["sec-ch-ua"]

    def test_sec_ch_ua_mobile_is_false(self):
        hdrs = get_default_headers("chrome_137")
        assert hdrs["sec-ch-ua-mobile"] == "?0"

    def test_sec_ch_ua_platform_is_windows(self):
        hdrs = get_default_headers("chrome_137")
        assert "Windows" in hdrs["sec-ch-ua-platform"]

    def test_safari_has_no_sec_ch_ua(self):
        hdrs = get_default_headers("safari_18_5")
        assert "sec-ch-ua" not in hdrs

    def test_firefox_has_no_sec_ch_ua(self):
        hdrs = get_default_headers("firefox_139")
        assert "sec-ch-ua" not in hdrs


# ---------------------------------------------------------------------------
# merge_headers
# ---------------------------------------------------------------------------

class TestMergeHeaders:
    def test_browser_accept_wins_over_scrapy_default(self):
        browser = {"Accept": "browser-accept", "Sec-Fetch-Dest": "document"}
        scrapy = {"Accept": "text/html,*/*;q=0.8", "User-Agent": "Scrapy/2.15"}
        result = merge_headers(browser, scrapy)
        assert result["Accept"] == "browser-accept"

    def test_user_agent_is_stripped(self):
        browser = {"Accept": "browser-accept"}
        scrapy = {"User-Agent": "Scrapy/2.15"}
        result = merge_headers(browser, scrapy)
        assert "User-Agent" not in result

    def test_cookie_is_kept(self):
        browser = {"Accept": "browser-accept"}
        request = {"Cookie": "session=abc123", "User-Agent": "Scrapy/2.15"}
        result = merge_headers(browser, request)
        assert result["Cookie"] == "session=abc123"

    def test_authorization_is_kept(self):
        browser = {"Accept": "browser-accept"}
        request = {"Authorization": "Bearer token123"}
        result = merge_headers(browser, request)
        assert result["Authorization"] == "Bearer token123"

    def test_custom_header_is_kept(self):
        browser = {"Accept": "browser-accept"}
        request = {"X-Custom-Header": "value"}
        result = merge_headers(browser, request)
        assert result["X-Custom-Header"] == "value"

    def test_accept_language_not_overridden_by_scrapy(self):
        browser = {"Accept-Language": "en-US,en;q=0.9"}
        scrapy = {"Accept-Language": "en"}
        result = merge_headers(browser, scrapy)
        assert result["Accept-Language"] == "en-US,en;q=0.9"

    def test_accept_encoding_not_overridden(self):
        browser = {"Accept-Encoding": "gzip, deflate, br"}
        scrapy = {"Accept-Encoding": "gzip"}
        result = merge_headers(browser, scrapy)
        assert result["Accept-Encoding"] == "gzip, deflate, br"

    def test_empty_request_headers_returns_defaults(self):
        browser = {"Accept": "browser-accept", "Sec-Fetch-Dest": "document"}
        result = merge_headers(browser, {})
        assert result == browser
