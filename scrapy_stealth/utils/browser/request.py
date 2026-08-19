from __future__ import annotations

import base64
import contextlib
import json
from typing import Any
from urllib.parse import urlparse

from ...exceptions import StealthConnectionError
from ..network.request import StealthRequestPayload, _parse_cookie_pairs


def request_origin(url: str) -> str:
    """Scheme + host (+ port) for same-origin checks."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def _same_origin(current_url: str, target_url: str) -> bool:
    current = urlparse(current_url)
    target = urlparse(target_url)
    return (
        current.scheme.lower() == target.scheme.lower()
        and current.netloc.lower() == target.netloc.lower()
    )


_BROWSER_CDP_SKIP_HEADERS = frozenset({"content-type", "content-length"})


def browser_cdp_headers(extra_headers: dict[str, str]) -> dict[str, str]:
    """Headers for CDP ``set_extra_http_headers`` during browser POST setup."""
    return {
        k: v
        for k, v in extra_headers.items()
        if k.lower() not in _BROWSER_CDP_SKIP_HEADERS
    }


async def prepare_browser_post_context(page: Any, url: str) -> None:
    """Load the target URL so in-page ``fetch()`` is same-origin.

    Uses GET on the target URL (not the site root) because many hosts redirect
    ``/`` elsewhere — e.g. postman-echo.com → www.postman.com — which would
    make a subsequent same-URL ``fetch()`` cross-origin and fail.
    """
    await page.get(url)
    await page.wait()
    current = await page.evaluate("window.location.href")
    if not _same_origin(str(current), url):
        raise StealthConnectionError(
            f"Browser POST setup left {request_origin(url)!r} for {current!r}; "
            "in-page fetch would be cross-origin"
        )


async def apply_browser_cookies(page: Any, url: str, cookie_header: str | None) -> None:
    if not cookie_header:
        return

    import nodriver.cdp.network as network

    for name, value in _parse_cookie_pairs(cookie_header):
        with contextlib.suppress(Exception):
            await page.send(network.set_cookie(name=name, value=value, url=url))


async def apply_browser_headers(page: Any, headers: dict[str, str]) -> None:
    if not headers:
        return

    import nodriver.cdp.network as network

    await page.send(network.set_extra_http_headers(network.Headers(headers)))


def _form_urlencoded_body_js(payload: StealthRequestPayload) -> str | None:
    """Merge hidden form fields (e.g. csrf_token) into urlencoded POST bodies."""
    content_type = payload.headers.get("Content-Type") or payload.extra_headers.get(
        "Content-Type", ""
    )
    if "application/x-www-form-urlencoded" not in content_type.lower():
        return None
    explicit = payload.body.decode(errors="replace") if payload.body else ""
    return (
        "const form = document.querySelector('form');"
        f"const explicit = new URLSearchParams({json.dumps(explicit)});"
        "if (form) {"
        "  const params = new URLSearchParams();"
        "  for (const [k, v] of new FormData(form).entries()) params.set(k, v);"
        "  for (const [k, v] of explicit.entries()) params.set(k, v);"
        "  init.body = params.toString();"
        "} else if (explicit.size) {"
        "  init.body = explicit.toString();"
        "}"
    )


def _build_fetch_expression(payload: StealthRequestPayload, url: str) -> str:
    body_b64 = base64.b64encode(payload.body).decode("ascii") if payload.body else None
    headers = dict(payload.extra_headers)
    form_body_js = _form_urlencoded_body_js(payload)
    if form_body_js:
        body_line = form_body_js
    elif body_b64:
        body_line = (
            f"init.body = Uint8Array.from(atob({json.dumps(body_b64)}), "
            "c => c.charCodeAt(0));"
        )
    else:
        body_line = ""
    return (
        "(async () => {"
        f"const headers = {json.dumps(headers)};"
        "const init = {"
        f"method: {json.dumps(payload.method)},"
        "headers,"
        "credentials: 'include',"
        "redirect: 'follow',"
        "};"
        f"{body_line}"
        f"const resp = await fetch({json.dumps(url)}, init);"
        "const buf = await resp.arrayBuffer();"
        "const bytes = new Uint8Array(buf);"
        "let binary = '';"
        "const chunk = 0x8000;"
        "for (let i = 0; i < bytes.length; i += chunk) {"
        "binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));"
        "}"
        "const bodyB64 = btoa(binary);"
        "const respHeaders = {};"
        "resp.headers.forEach((v, k) => { respHeaders[k] = v; });"
        "return { status: resp.status, bodyB64, headers: respHeaders };"
        "})()"
    )


def _deep_serialized_to_python(node: Any) -> Any:
    """Convert CDP deep-serialization nodes to plain Python values."""
    if node is None or isinstance(node, (str, int, float, bool)):
        return node
    if isinstance(node, list):
        if (
            node
            and isinstance(node[0], (list, tuple))
            and len(node[0]) == 2
            and isinstance(node[0][0], str)
            and isinstance(node[0][1], dict)
            and "type" in node[0][1]
        ):
            return {
                _deep_serialized_to_python(key): _deep_serialized_to_python(val)
                for key, val in node
            }
        return [_deep_serialized_to_python(item) for item in node]
    if isinstance(node, dict):
        if "type" in node and "value" in node:
            kind = node["type"]
            value = node["value"]
            if kind in {"string", "number", "boolean"}:
                return value
            if kind in {"null", "undefined"}:
                return None
            if kind == "object":
                return _deep_serialized_to_python(value)
            return value
        return {k: _deep_serialized_to_python(v) for k, v in node.items()}
    return node


def _coerce_fetch_result(result: Any) -> dict[str, Any]:
    """Normalize nodriver evaluate() output into {status, bodyB64, headers}."""
    if isinstance(result, dict) and "status" in result:
        return result

    value = getattr(result, "value", None)
    if isinstance(value, dict) and value:
        return value

    deep = getattr(result, "deep_serialized_value", None)
    if deep is not None:
        parsed = _deep_serialized_to_python(getattr(deep, "value", deep))
        if isinstance(parsed, dict):
            return parsed

    if isinstance(result, list):
        parsed = _deep_serialized_to_python(result)
        if isinstance(parsed, dict):
            return parsed

    raise StealthConnectionError(
        f"Browser fetch returned unexpected result: {result!r}"
    )


_DECODED_BODY_SKIP_HEADERS = frozenset({"content-encoding", "content-length"})


def _fetch_response_headers(raw: dict[str, str]) -> dict[str, str]:
    """Drop encoding/length headers — fetch ``arrayBuffer()`` is already decoded."""
    return {k: v for k, v in raw.items() if k.lower() not in _DECODED_BODY_SKIP_HEADERS}


def _evaluate_error_message(result: Any) -> str | None:
    """Return a JS exception message when nodriver evaluate() failed."""
    text = getattr(result, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    description = getattr(getattr(result, "exception", None), "description", None)
    if isinstance(description, str) and description.strip():
        return description.strip()
    return None


async def browser_http_fetch(
    page: Any, url: str, payload: StealthRequestPayload
) -> tuple[bytes, int, dict[str, str]]:
    expression = _build_fetch_expression(payload, url)
    result = await page.evaluate(expression, await_promise=True, return_by_value=True)

    if (msg := _evaluate_error_message(result)) is not None:
        raise StealthConnectionError(f"Browser fetch failed for {url!r}: {msg}")

    try:
        payload_result = _coerce_fetch_result(result)
    except StealthConnectionError as exc:
        raise StealthConnectionError(
            f"Browser fetch returned unexpected result for {url!r}: {exc}"
        ) from None

    status = int(payload_result.get("status") or 0)
    body_b64 = payload_result.get("bodyB64") or ""
    resp_headers = _fetch_response_headers(
        {str(k): str(v) for k, v in (payload_result.get("headers") or {}).items()}
    )
    return base64.b64decode(body_b64), status, resp_headers
