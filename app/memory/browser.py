from __future__ import annotations

from playwright.async_api import async_playwright, Browser

_browser: Browser | None = None


async def get_browser() -> Browser:
    global _browser
    if _browser is None:
        pw = await async_playwright().start()
        _browser = await pw.chromium.launch(headless=True)
    return _browser


async def fetch_page(url: str) -> str:
    browser = await get_browser()
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return await page.inner_text("body")
    finally:
        await page.close()