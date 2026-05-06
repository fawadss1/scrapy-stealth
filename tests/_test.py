import asyncio
import nodriver as uc
import time
import logging

# Keep logs clean
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

PROXY_URL = ""
TARGET = "https://httpbin.org/ip"


async def visible_fetch():
    print("🚀 Starting visible fetch (Headless=False)...")

    # 1. Start browser with headless=False
    # We keep image disabling active because it's the biggest speed boost
    browser = await uc.start(
        headless=False,
        browser_args=[
            "--blink-settings=imagesEnabled=false",
            "--disable-gpu",
            "--no-sandbox"
        ]
    )

    try:
        start_time = time.perf_counter()

        # 2. Create the authenticated context
        tab = await browser.create_context(proxy_server=PROXY_URL)

        # 3. Navigate
        print(f"📡 Requesting {TARGET}...")
        page = await tab.get(TARGET)

        # 4. Wait for the JSON data to render on screen
        # This is faster than a sleep() because it reacts the moment the text exists
        await page.wait_for("pre", timeout=15)

        # 5. Extract data
        content = await page.evaluate("document.body.innerText")

        end_time = time.perf_counter()

        print("\n" + "=" * 40)
        print(f"✅ DATA: {content.strip()}")
        print(f"⏱️  SPEED: {end_time - start_time:.2f} seconds")
        print("=" * 40)

        # Optional: Keep the browser open for a moment so you can see it
        await asyncio.sleep(2)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        browser.stop()


if __name__ == "__main__":
    uc.loop().run_until_complete(visible_fetch())
