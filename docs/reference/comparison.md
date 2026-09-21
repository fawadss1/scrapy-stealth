# Comparison

How scrapy-stealth compares to other Scrapy stealth / browser integrations.

| Feature                      | scrapy-stealth | scrapy-impersonate | scrapy-playwright | scrapy-splash | Scrapy (default) |
|------------------------------|:--------------:|:------------------:|:-----------------:|:-------------:|:----------------:|
| TLS fingerprint spoofing     |      Yes       |        Yes         |        No         |      No       |        No        |
| HTTP/2 support               |      Yes       |        Yes         |        Yes        |      No       |        No        |
| Browser impersonation        |      Yes       |        Yes         |      partial      |      No       |        No        |
| Proxy rotation (built-in)    |      Yes       |         No         |        No         |      No       |        No        |
| Smart Proxy Management       |      Yes       |         No         |        No         |      No       |        No        |
| Fingerprint rotation         |      Yes       |         No         |        No         |      No       |        No        |
| Anti-bot detection           |      Yes       |         No         |        No         |      No       |        No        |
| Smart browser selection      |      Yes       |         No         |        No         |      No       |        No        |
| Smart retry logic            |      Yes       |         No         |        No         |      No       |        No        |
| Per-request engine switching |      Yes       |         No         |        No         |      No       |        No        |
| Headless browser required    |      Yes       |         No         |        Yes        |      Yes      |        No        |
| JavaScript rendering         |      Yes       |         No         |        Yes        |      Yes      |        No        |
| Behavioral fingerprinting    |      Yes       |         No         |      manual       |      No       |        No        |
| Screenshot / snapshot        |      Yes       |         No         |        Yes        |      Yes      |        No        |
| Native Scrapy integration    |      Yes       |        Yes         |        Yes        |      Yes      |       Yes        |
| Memory footprint             |      Low       |        Low         |       High        |     High      |       Low        |

!!! note
`scrapy-playwright` uses a real browser TLS stack but does not spoof fingerprint profiles like scrapy-stealth.
`scrapy-impersonate` provides TLS/HTTP2 impersonation but lacks built-in rotation, detection, or per-request engine switching.
JavaScript rendering is available via the optional `browser` driver — use it selectively for pages that require a full browser.
