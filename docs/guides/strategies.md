# Strategies

Helper classes for fingerprint rotation and intelligent retries. The middleware uses these internally; you can also call them from spiders.

## Fingerprint rotation

Profiles are chosen **randomly from the pool by default**. Pin one only when debugging or when a site requires a specific fingerprint:

```python
yield scrapy.Request(url, meta={"stealth": {"profile": "chrome150"}})
```

Manual rotation outside session recycle:

```python
from scrapy_stealth.strategies.fingerprint import ProfileRotator

yield scrapy.Request(url, meta={"stealth": {"profile": ProfileRotator().get()}})
```

On ban-streak session recycle, a new default profile is chosen automatically when `profile` is omitted from meta.

## Intelligent retry

```python
from scrapy_stealth.strategies.retry import RetryHandler

retry = RetryHandler()


def parse(self, response):
    if retry.should_retry(response):
        yield retry.build(response.request)
        return
```

Works alongside Scrapy's built-in `RetryMiddleware` and scrapy-stealth ban detection / `driver="auto"` fallback.

## Related

- [Per-request meta](../configuration/meta.md) — `profile`, `proxy`, `driver`
- [Session recycle & stats](../reference/stats.md) — bans, recycles, and `STEALTH_RECYCLE_AFTER_BANS`
- [Smart Proxy Management](proxy-management.md)
