# Installation

## Requirements

- Python **3.11+**
- Scrapy **2.12–2.x**

## Install from PyPI

```bash
pip install scrapy-stealth
```

## Development install

```bash
git clone https://github.com/fawadss1/scrapy-stealth.git
cd scrapy-stealth
pip install -e ".[dev]"
```

## Optional: build docs locally

```bash
pip install -e ".[docs]"
mkdocs serve
```

## Windows note

The `basic` driver uses `wreq`, which requires the **Visual C++ Redistributable** on Windows. If import fails, install both:

- [VC++ x64](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- [VC++ x86](https://aka.ms/vs/17/release/vc_redist.x86.exe)

## Chrome for browser driver

The `browser` and `auto` drivers need **Google Chrome** or **Chromium** on the PATH, unless you set `BROWSER_EXECUTABLE_PATH`.
See [Browser engine](../drivers/browser.md).
