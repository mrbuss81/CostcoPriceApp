# scraper.py
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import time

# Try the external stealth helper if available; otherwise we'll use the fallback
try:
    from playwright_stealth import stealth_sync  # some versions expose this
    HAVE_STEALTH = True
except Exception:
    stealth_sync = None
    HAVE_STEALTH = False

# JS snippet to run on every new page to make Playwright pages look more "real"
STEALTH_JS = """
// make navigator.webdriver false
Object.defineProperty(navigator, 'webdriver', {get: () => false, configurable: true});

// mock languages
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en'], configurable: true});

// mock plugins
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5], configurable: true});

// mock window.chrome
window.chrome = window.chrome || { runtime: {} };

// mock permissions query for notifications (some sites check this)
const originalQuery = window.navigator.permissions && window.navigator.permissions.query;
if (window.navigator.permissions && originalQuery) {
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ? Promise.resolve({ state: Notification.permission }) : originalQuery(parameters)
    );
}
"""

def fetch_costco_price(url: str, headless: bool = False) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=headless, args=[
            # optional flags that sometimes help; remove if they cause issues
            "--disable-blink-features=AutomationControlled",
        ])

        # create context with a real user agent and locale
        context = browser.new_context(
            user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"),
            locale="en-CA",
            java_script_enabled=True,
            viewport={"width": 1280, "height": 800},
            timezone_id="America/Vancouver",
        )

        # apply our init script so every page has these overrides
        # context.add_init_script is preferred so it runs before page JS
        context.add_init_script(STEALTH_JS)

        page = context.new_page()

        # If we have the external stealth helper, call it as well (best-effort)
        if HAVE_STEALTH and stealth_sync is not None:
            try:
                stealth_sync(page)
            except Exception:
                # ignore stealth import errors — we already applied our init script
                pass

        # Warm up: visit homepage first so cookies/region are set
        try:
            page.goto("https://www.costco.ca", wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(1200)
        except PlaywrightTimeout:
            # continue anyway — sometimes homepage takes longer
            pass

        # Now navigate to the product page
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
        except PlaywrightTimeout:
            # if domcontentloaded times out, try a more lenient attempt
            try:
                page.goto(url, wait_until="load", timeout=20000)
            except Exception as e:
                # return a helpful debug string so you can see what happened
                browser.close()
                return f"Navigation failed: {e}"

        # Give the page a moment to render dynamic price elements
        page.wait_for_timeout(1200)

        # robust selector list (adjust or add if you inspect the page)
        selectors = [
            'span[class*="product-price"]',      # common names
            'div[class*="price"] span',          # fallback generic
            '.product-price-amount',             # alt
            '.price',                            # generic
            '[data-test="product-price"]',       # data-test attr
            'span[data-automation="product-price"]'
        ]

        price_text = None
        for selector in selectors:
            try:
                # ping for existence
                page.wait_for_selector(selector, timeout=4000)
                # try several ways to extract text
                txt = page.inner_text(selector).strip()
                if txt:
                    price_text = txt
                    break
            except Exception:
                continue

        # If we didn't find a price, capture a tiny debug snapshot of the page (title + first 500 chars)
        if price_text is None:
            title = page.title()
            content_snippet = page.content()[:2000]  # big, but useful for debugging
            browser.close()
            return f"Price not found. page title: {title}\nHTML snippet:\n{content_snippet}"

        browser.close()
        return price_text


if __name__ == "__main__":
    # Put a real Costco product URL here
    test_url = "https://www.costco.ca/kirkland-signature-2-ply-paper-towels-12-pack.product.100363149.html"
    print(fetch_costco_price(test_url, headless=False))
