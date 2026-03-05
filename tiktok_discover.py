"""
TikTok Scraper — Discover & Search Module
Uses Playwright to scrape TikTok search results and filter by engagement.
"""

import re
import time
import random

# ─── CSS Selectors (update these if TikTok redesigns) ─────────────────
SEARCH_CARD_SEL = '[data-e2e="search_top-item-list"] > div, [data-e2e="search-card-desc"]'
VIDEO_LINK_SEL = 'a[href*="/video/"]'
VIEW_COUNT_SEL = '[data-e2e="search-card-like-container"] strong, [data-e2e="video-views"]'
FALLBACK_CARD_SEL = 'div[class*="DivItemCardContainer"], div[class*="DivVideoCard"]'


def parse_count(text: str) -> int:
    """Parse abbreviated counts like '1.5M', '200K', '10B' into integers."""
    text = text.strip().upper().replace(",", "")
    multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
    for suffix, mult in multipliers.items():
        if text.endswith(suffix):
            try:
                return int(float(text[:-1]) * mult)
            except ValueError:
                return 0
    try:
        return int(text)
    except ValueError:
        return 0


def scrape_tiktok(keywords, max_per_keyword=20, min_views=0, min_likes=0,
                  scroll_count=5, headless=True):
    """
    Scrape TikTok search results for given keywords.

    Returns list of dicts: [{"url": str, "views": int, "keyword": str}, ...]
    """
    from playwright.sync_api import sync_playwright

    all_results = []
    seen_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        for keyword in keywords:
            print(f"\n🔍  Searching TikTok for: {keyword}")
            url = f"https://www.tiktok.com/search/video?q={keyword}"

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                print(f"   ⚠  Failed to load search page: {e}")
                continue

            # Wait for content to render
            time.sleep(random.uniform(3, 5))

            # Dismiss cookie/login popups if they appear
            _dismiss_popups(page)

            # Scroll to load more results
            for i in range(scroll_count):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(random.uniform(2, 4))
                print(f"   📜  Scroll {i + 1}/{scroll_count}")

            # Extract video links and metadata
            videos = _extract_videos(page, keyword, min_views, min_likes)

            new_count = 0
            for vid in videos:
                if vid["url"] not in seen_urls and new_count < max_per_keyword:
                    seen_urls.add(vid["url"])
                    all_results.append(vid)
                    new_count += 1

            print(f"   ✅  Found {new_count} videos for '{keyword}'")

        browser.close()

    return all_results


def _dismiss_popups(page):
    """Try to close cookie banners or login modals."""
    dismiss_selectors = [
        'button[data-e2e="modal-close-inner-button"]',
        'div[class*="DivCloseIcon"]',
        'button:has-text("Accept all")',
        'button:has-text("Decline")',
    ]
    for sel in dismiss_selectors:
        try:
            btn = page.query_selector(sel)
            if btn:
                btn.click()
                time.sleep(0.5)
        except Exception:
            pass


def _extract_videos(page, keyword, min_views, min_likes):
    """Extract video URLs and view counts from the current page."""
    results = []

    # Strategy 1: Find all video links on the page
    links = page.query_selector_all('a[href*="/video/"]')

    seen_in_page = set()
    for link in links:
        href = link.get_attribute("href")
        if not href or "/video/" not in href:
            continue

        # Normalize URL
        if href.startswith("/"):
            href = "https://www.tiktok.com" + href

        # Extract video ID to deduplicate
        video_id_match = re.search(r"/video/(\d+)", href)
        if not video_id_match:
            continue
        video_id = video_id_match.group(1)
        if video_id in seen_in_page:
            continue
        seen_in_page.add(video_id)

        # Try to get view count from nearby elements
        views = 0
        try:
            parent = link.evaluate_handle(
                "el => el.closest('div[class*=\"Card\"], div[class*=\"item\"]')"
            )
            if parent:
                view_el = parent.as_element().query_selector(
                    'strong[data-e2e="video-views"], span[class*="SpanCount"], '
                    'strong[class*="Strong"]'
                )
                if view_el:
                    views = parse_count(view_el.inner_text())
        except Exception:
            pass

        # Apply filters
        if min_views and views < min_views and views > 0:
            continue

        results.append({
            "url": href,
            "views": views,
            "keyword": keyword,
        })

    return results


if __name__ == "__main__":
    # Quick test
    results = scrape_tiktok(["gym"], max_per_keyword=5, scroll_count=2, headless=False)
    for r in results:
        print(f"  {r['views']:>10,} views | {r['url']}")
