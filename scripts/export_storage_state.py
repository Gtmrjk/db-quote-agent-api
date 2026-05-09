import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright


QUOTE_URL = os.getenv(
    "ONECMS_QUOTE_URL",
    "https://www.bhaskar.com/onecms/quote-image-generator",
)
OUTPUT_PATH = Path(os.getenv("ONECMS_STORAGE_STATE_PATH", "storage-state.json"))


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(QUOTE_URL)
        print("Log in fully in the opened browser, including OTP if prompted.")
        input("Press Enter here after the quote generator page is visible...")
        await context.storage_state(path=OUTPUT_PATH)
        await browser.close()

    compact = json.dumps(json.loads(OUTPUT_PATH.read_text()), separators=(",", ":"))
    print(f"Saved {OUTPUT_PATH}")
    print("Paste this value into ONECMS_STORAGE_STATE_JSON:")
    print(compact)


if __name__ == "__main__":
    asyncio.run(main())
