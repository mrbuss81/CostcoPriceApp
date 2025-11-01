# scraper_debug.py
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import os, time

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => false, configurable: true});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en'], configurable: true});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3], configurable: true});
window.chrome = window.chrome || { runtime: {} };
"""

def fetch_costco_price_debug(url: str, headless: bool = False) -> str:
    debug_path = os.path.join(os.getcwd(), "debug.png")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=headless, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"),
            locale="en-CA",
            viewport={"width": 1366, "height": 900},
            timezone_id="America/Vancouver",
        )
        context.add_init_script(STEALTH_JS)
        page = context.new_page()

        # simple logging hooks
        def on_request(request):
            print(f"-> REQUEST: {request.method} {request.url}")
        def on_response(response):
            try:
                print(f"<- RESPONSE: {response.status} {response.url}")
            except Exception:
                pass
        def on_request_failed(request):
            print(f"XX REQUEST FAILED: {request.url}   failure={request.failure}")
        def on_console(msg):
            print(f"CONSOLE[{msg.type}]: {msg.text}")

        page.on("request", on_request)
        page.on("response", on_response)
        page.on("requestfailed", on_request_failed)
        page.on("console", on_console)

        # Warm up
        try:
            page.goto("https://www.costco.ca", wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(1200)
        except PlaywrightTimeout:
            print("Warning: homepage timeout")

        # Attempt product navigation (observe what happens)
        try:
            print(f"Navigating to product URL: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)
        except PlaywrightTimeout:
            print("Navigation domcontentloaded timed out, trying 'load'...")
            try:
                page.goto(url, wait_until="load", timeout=30000)
                page.wait_for_timeout(1500)
            except Exception as e:
                print(f"Final navigation error: {e}")

        # take screenshot for inspection
        try:
            page.screenshot(path=debug_path, full_page=False)
            print(f"Screenshot saved to: {debug_path}")
        except Exception as e:
            print(f"Failed to screenshot: {e}")

        # try price extraction quickly
        selectors = [
            'span[class*="product-price"]',
            'div[class*="price"] span',
            '.product-price-amount',
            '.price',
            '[data-test="product-price"]',
            'span[data-automation="product-price"]'
        ]
        price_text = None
        for sel in selectors:
            try:
                page.wait_for_selector(sel, timeout=3000)
                txt = page.inner_text(sel).strip()
                if txt:
                    price_text = txt
                    print(f"Found price via {sel}: {txt}")
                    break
            except Exception:
                pass

        title = page.title()
        content_snippet = page.content()[:2000]

        browser.close()

        if price_text:
            return price_text
        else:
            return f"DEBUG: title={title}\nprice_not_found\nHTML_snippet_start:\n{content_snippet[:1000]}\n\nCheck debug.png in project folder."

if __name__ == "__main__":
    test_url = "https://www.costco.ca/kirkland-signature-2-ply-paper-towels-12-pack.product.100363149.html"
    print(fetch_costco_price_debug(test_url, headless=False))
