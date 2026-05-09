import asyncio
import base64
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from playwright.async_api import Browser, Page, async_playwright

from app.schemas import QuoteRequest
from app.settings import Settings


class QuoteAgentError(RuntimeError):
    status_code = 500


class GenerationFailed(QuoteAgentError):
    status_code = 502


@dataclass
class GeneratedImage:
    content: bytes
    mime_type: str
    source: str


class BhaskarQuoteAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._lock = asyncio.Lock()
        self._playwright = None
        self._browser: Browser | None = None

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def generate(self, request: QuoteRequest) -> GeneratedImage:
        async with self._lock:
            page = await self._new_page()
            try:
                await self._open_tool(page)
                await self._fill_form(page, request)
                content = await self._read_canvas(page, request.image_format)
                return GeneratedImage(content, f"image/{request.image_format}", "canvas")
            finally:
                await page.context.close()

    async def _new_page(self) -> Page:
        if not self._playwright:
            self._playwright = await async_playwright().start()
        if not self._browser or not self._browser.is_connected():
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage", "--no-sandbox"],
            )

        context = await self._browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(self.settings.browser_timeout_ms)
        return page

    async def _open_tool(self, page: Page) -> None:
        tool_file = Path(self.settings.quote_tool_file)
        if not tool_file.is_absolute():
            tool_file = Path.cwd() / tool_file
        if not tool_file.exists():
            raise GenerationFailed(f"Quote generator file not found: {tool_file}")

        await page.goto(tool_file.resolve().as_uri(), wait_until="networkidle")
        await page.locator("#quoteCanvas").wait_for(state="visible")

    async def _fill_form(self, page: Page, request: QuoteRequest) -> None:
        await self._set_value(page, "#quoteInput", request.quote)
        await self._set_value(page, "#authorInput", request.author or "")
        await self._set_value(page, "#designationInput", request.designation or "")

        if request.brand:
            await page.locator("#brandSelect").select_option(request.brand)
            await page.locator("#brandSelect").dispatch_event("change")

        if request.image_base64:
            await self._upload_base64_image(page, request)

        await page.wait_for_function(
            "() => document.querySelector('#quoteCanvas')?.width > 0 && "
            "document.querySelector('#quoteCanvas')?.height > 0"
        )
        await page.wait_for_timeout(250)

    async def _set_value(self, page: Page, selector: str, value: str) -> None:
        locator = page.locator(selector)
        await locator.fill(value)
        await locator.dispatch_event("input")
        await locator.dispatch_event("change")

    async def _upload_base64_image(self, page: Page, request: QuoteRequest) -> None:
        encoded = request.image_base64 or ""
        if encoded.startswith("data:image/"):
            encoded = encoded.split(",", 1)[1]

        suffix = ".jpg" if request.image_mime_type == "image/jpeg" else ".png"
        with NamedTemporaryFile(suffix=suffix) as image_file:
            image_file.write(base64.b64decode(encoded))
            image_file.flush()
            await page.locator("#imageInput").set_input_files(image_file.name)
            with suppress(Exception):
                await page.wait_for_function(
                    "() => document.querySelector('#quoteCanvas')"
                    "?.toDataURL('image/png').length > 1000",
                    timeout=4_000,
                )

    async def _read_canvas(self, page: Page, image_format: str) -> bytes:
        mime_type = f"image/{image_format}"
        data_url = await page.locator("#quoteCanvas").evaluate(
            "(canvas, mimeType) => canvas.toDataURL(mimeType, 0.95)",
            mime_type,
        )
        try:
            _, encoded = data_url.split(",", 1)
            return base64.b64decode(encoded)
        except ValueError as exc:
            raise GenerationFailed("The quote canvas did not produce an image.") from exc
