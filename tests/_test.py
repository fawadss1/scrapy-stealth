import asyncio
from wreq import Client, Emulation


async def main():
    client = Client(
        emulation=Emulation.Chrome137
    )

    resp = await client.get("https://httpbin.org/ip")

    # ✅ Built-in: wreq handles encoding internally
    text = await resp.text()
    print(text)

    # ❗ If you REALLY need raw bytes (for debugging/detection)
    raw = await resp.bytes()

    # Optional: show content-type (NOT encoding)
    content_type = resp.headers.get("content-type", "")
    print("Content-Type:", content_type)


asyncio.run(main())
