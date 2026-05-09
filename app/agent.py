import asyncio
import base64
import json
import re
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from playwright.async_api import Browser, Page, TimeoutError as PlaywrightTimeoutError, async_playwright

from app.schemas import QuoteRequest
from app.settings import Settings


class QuoteAgentError(RuntimeError):
    status_code = 500


class AuthenticationRequired(QuoteAgentError):
    status_code = 424


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
                await self._open_generator(page)
                await self._fill_quote_form(page, request)
                image = await self._trigger_generation(page)
                return image
            finally:
                await page.close()

    async def _new_page(self) -> Page:
        if not self._playwright:
            self._playwright = await async_playwright().start()
        if not self._browser or not self._browser.is_connected():
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage", "--no-sandbox"],
            )

        context_options = {
            "user_agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        }
        if self.settings.onecms_storage_state_json:
            context_options["storage_state"] = json.loads(self.settings.onecms_storage_state_json)

        context = await self._browser.new_context(**context_options)
        page = await context.new_page()
        page.set_default_timeout(self.settings.browser_timeout_ms)
        return page

    async def _open_generator(self, page: Page) -> None:
        await page.goto(self.settings.onecms_quote_url, wait_until="domcontentloaded")
        await self._login_if_needed(page)
        await page.goto(self.settings.onecms_quote_url, wait_until="networkidle")
        if await self._looks_like_login(page):
            raise AuthenticationRequired(
                "OneCMS still shows the login page. Set ONECMS_USERNAME and ONECMS_PASSWORD, "
                "or provide ONECMS_STORAGE_STATE_JSON for accounts that require OTP."
            )

    async def _login_if_needed(self, page: Page) -> None:
        if not await self._looks_like_login(page):
            return
        if not self.settings.onecms_username or not self.settings.onecms_password:
            raise AuthenticationRequired(
                "The generator is behind OneCMS login. Configure ONECMS_USERNAME and ONECMS_PASSWORD."
            )

        await page.locator("#email, input[name='email'], input[type='text']").first.fill(
            self.settings.onecms_username
        )
        await page.locator("#password, input[name='password'], input[type='password']").first.fill(
            self.settings.onecms_password
        )
        await page.locator("#loginFrmBtn, button[type='submit']").first.click()
        await page.wait_for_load_state("networkidle")

        if await self._page_has_otp(page):
            raise AuthenticationRequired(
                "This OneCMS account appears to require OTP. Log in once locally and set "
                "ONECMS_STORAGE_STATE_JSON with the captured Playwright storage state."
            )

    async def _looks_like_login(self, page: Page) -> bool:
        return await page.locator("#email, input[name='email'], #password, input[name='password']").count() > 0

    async def _page_has_otp(self, page: Page) -> bool:
        return await page.locator("input[name='otp'], .ap-otp-input, #digit_1").count() > 0

    async def _fill_quote_form(self, page: Page, request: QuoteRequest) -> None:
        await self._fill_by_candidates(
            page,
            request.quote,
            [
                "textarea[name*='quote' i]",
                "textarea[id*='quote' i]",
                "textarea[placeholder*='quote' i]",
                "textarea",
                "[contenteditable='true']",
            ],
        )

        if request.author:
            await self._fill_by_candidates(
                page,
                request.author,
                [
                    "input[name*='author' i]",
                    "input[id*='author' i]",
                    "input[placeholder*='author' i]",
                    "input[name*='source' i]",
                    "input[placeholder*='source' i]",
                ],
                required=False,
            )

        for label, value in {
            "language": request.language,
            "template": request.template,
            "size": request.size,
            "theme": request.theme,
        }.items():
            if value:
                await self._choose_option(page, label, value)

    async def _fill_by_candidates(
        self,
        page: Page,
        value: str,
        selectors: list[str],
        required: bool = True,
    ) -> bool:
        for selector in selectors:
            locator = page.locator(selector).first
            with suppress(PlaywrightTimeoutError):
                await locator.wait_for(state="visible", timeout=2_500)
                await locator.fill(value)
                return True
        if required:
            raise GenerationFailed("Could not find the quote text field after login.")
        return False

    async def _choose_option(self, page: Page, label: str, value: str) -> None:
        option_re = re.compile(re.escape(value), re.IGNORECASE)
        select = page.locator(f"select[name*='{label}' i], select[id*='{label}' i]").first
        if await select.count():
            with suppress(Exception):
                await select.select_option(label=value)
                return
            with suppress(Exception):
                await select.select_option(value=value)
                return

        target = page.get_by_text(option_re).first
        with suppress(Exception):
            await target.click(timeout=2_000)

    async def _trigger_generation(self, page: Page) -> GeneratedImage:
        before_images = await self._image_count(page)
        button = page.get_by_role("button", name=re.compile("generate|create|download|submit|preview", re.I)).first
        with suppress(Exception):
            async with page.expect_download(timeout=12_000) as download_info:
                await button.click()
            download = await download_info.value
            with TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / (download.suggested_filename or "quote.png")
                await download.save_as(path)
                return GeneratedImage(path.read_bytes(), self._mime_for_path(path), "download")

        await button.click()
        await page.wait_for_load_state("networkidle")
        with suppress(PlaywrightTimeoutError):
            await page.wait_for_function(
                "(count) => document.images.length > count || document.querySelector('canvas')",
                arg=before_images,
                timeout=15_000,
            )

        canvas = page.locator("canvas").last
        if await canvas.count():
            data_url = await canvas.evaluate("canvas => canvas.toDataURL('image/png')")
            return self._from_data_url(data_url, "canvas")

        image = page.locator("img").last
        if await image.count():
            src = await image.get_attribute("src")
            if src and src.startswith("data:image/"):
                return self._from_data_url(src, "data-url")
            screenshot = await image.screenshot(type="png")
            return GeneratedImage(screenshot, "image/png", "image-screenshot")

        screenshot = await page.screenshot(type="png", full_page=True)
        return GeneratedImage(screenshot, "image/png", "page-screenshot")

    async def _image_count(self, page: Page) -> int:
        return await page.locator("img").count()

    def _from_data_url(self, data_url: str, source: str) -> GeneratedImage:
        header, encoded = data_url.split(",", 1)
        mime_type = header.removeprefix("data:").split(";")[0]
        return GeneratedImage(base64.b64decode(encoded), mime_type, source)

    def _mime_for_path(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            return "image/jpeg"
        if suffix == ".webp":
            return "image/webp"
        return "image/png"
