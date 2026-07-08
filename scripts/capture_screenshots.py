"""Capture README screenshots via Playwright."""

import asyncio
import http.server
import socket
import threading
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
OUT = ROOT / "docs" / "screenshots"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _serve_frontend(port: int) -> None:
    import os

    os.chdir(ROOT)
    handler = http.server.SimpleHTTPRequestHandler
    http.server.ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    port = _free_port()
    thread = threading.Thread(target=_serve_frontend, args=(port,), daemon=True)
    thread.start()

    base = f"http://127.0.0.1:{port}/frontend/index.html"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        await page.goto(base, wait_until="networkidle")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=str(OUT / "home.png"), full_page=True)

        await page.fill("#promptInput", "A blog platform with posts, authors, and comments")
        await page.click("#forgeBtn")

        await page.wait_for_selector("#screenResult.active", timeout=120000)
        await page.wait_for_selector("#statEntities:not(:empty)", timeout=120000)
        await page.wait_for_timeout(1500)
        await page.screenshot(path=str(OUT / "overview.png"), full_page=True)

        for name, screen in [
            ("relationships", "relationships"),
            ("schema", "schema"),
            ("playground", "playground"),
        ]:
            await page.click(f'.nav-link[data-screen="{screen}"]')
            await page.wait_for_timeout(800)
            await page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)

        await browser.close()

    print("Saved screenshots to", OUT)


if __name__ == "__main__":
    asyncio.run(main())
