# Snapshots

Capture a PNG screenshot of any page rendered by the **browser** driver.

## Request meta

```python
yield scrapy.Request(
    url,
    meta={
        "stealth": {
            "driver": "browser",
            "snapshot": True,
        }
    },
    callback=self.parse,
)
```

PNG bytes are in `response.meta["snapshot_content"]` (full scrollable page, not just the viewport).

## `@snapshot` decorator

```python
from scrapy_stealth.decorators import snapshot


class MySpider(scrapy.Spider):
    @snapshot
    def parse(self, response): ...

    @snapshot(path="stealth_shots/page.png")
    def parse(self, response): ...

    @snapshot(path=lambda r: r.url.split("/")[-1] + ".png")
    def parse(self, response): ...
```

Requires `driver="browser"` and `snapshot=True` in request meta.

## Manual handling

```python
def parse(self, response):
    shot = response.meta.get("snapshot_content")
    if shot:
        with open("page.png", "wb") as f:
            f.write(shot)
        yield {"url": response.url, "screenshot": shot}
```

## Notes

- Static asset blocking is **disabled** when `snapshot=True`
- Snapshot failures log an error; parsing continues without bytes
