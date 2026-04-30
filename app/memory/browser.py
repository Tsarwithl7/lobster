# 使用 Playwright 启动一个全局 Chromium 浏览器复用；每次抓取都新建 page 并在结束后关闭，返回 body 文本。


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

async def cleanup_browser() -> None:
    """Close global browser and stop Playwright."""
    global _pw, _browser
    if _browser is not None:
        await _browser.close()
        _browser = None
    if _pw is not None:
        await _pw.stop()
        _pw = None        