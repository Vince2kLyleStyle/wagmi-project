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

            # Wait for content to fully render
            time.sleep(random.uniform(4, 7))

            # Dismiss cookie/login popups if they appear
            _dismiss_popups(page)

            # Wait a bit more after dismissing popups
            time.sleep(random.uniform(1, 2))

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
    seen_ids = set()

    # Strategy 1: Pull video URLs from page HTML via regex (most reliable)
    try:
        html = page.content()
        url_matches = re.findall(
            r'https?://(?:www\.)?tiktok\.com/@[\w.]+/video/(\d+)', html
        )
        for video_id in url_matches:
            if video_id not in seen_ids:
                seen_ids.add(video_id)
    except Exception:
        pass

    # Strategy 2: Find all anchor tags with /video/ in href
    try:
        links = page.query_selector_all('a[href*="/video/"]')
        for link in links:
            href = link.get_attribute("href") or ""
            match = re.search(r'/video/(\d+)', href)
            if match and match.group(1) not in seen_ids:
                seen_ids.add(match.group(1))
    except Exception:
        pass

    # Strategy 3: Extract from TikTok's embedded JSON data (SIGI_STATE or __NEXT_DATA__)
    try:
        json_data = page.evaluate("""() => {
            // TikTok stores video data in script tags or window objects
            const scripts = document.querySelectorAll('script');
            const urls = [];
            for (const s of scripts) {
                const text = s.textContent || '';
                const matches = text.match(/"id":"(\\d{15,})"/g);
                if (matches) {
                    for (const m of matches) {
                        const id = m.match(/"id":"(\\d+)"/);
                        if (id) urls.push(id[1]);
                    }
                }
            }
            return urls;
        }""")
        for video_id in (json_data or []):
            if video_id not in seen_ids:
                seen_ids.add(video_id)
    except Exception:
        pass

    if not seen_ids:
        # Debug: dump what we can see on the page
        try:
            title = page.title()
            url = page.url
            all_links = page.query_selector_all('a')
            link_count = len(all_links)
            print(f"   ⚠  Debug: page title='{title}', url='{url}', links on page={link_count}")
        except Exception:
            pass
        return results

    print(f"   🔗  Found {len(seen_ids)} unique video IDs")

    # Now try to get view counts for each video
    view_counts = {}
    try:
        # Grab all visible text elements that look like view counts
        view_data = page.evaluate("""() => {
            const data = {};
            // Look for elements with view count text near video links
            const allElements = document.querySelectorAll(
                '[data-e2e*="video-views"], [class*="video-count"], ' +
                'strong[data-e2e], [class*="PlayCount"], [class*="play-count"]'
            );
            for (const el of allElements) {
                const text = el.textContent.trim();
                if (text && /^[\\d.]+[KMB]?$/i.test(text)) {
                    // Find the nearest video link
                    const card = el.closest('div[class*="Card"], div[class*="item"], div[data-e2e]');
                    if (card) {
                        const link = card.querySelector('a[href*="/video/"]');
                        if (link) {
                            const match = link.href.match(/\\/video\\/(\\d+)/);
                            if (match) data[match[1]] = text;
                        }
                    }
                }
            }
            return data;
        }""")
        if view_data:
            view_counts = {vid_id: parse_count(count) for vid_id, count in view_data.items()}
    except Exception:
        pass

    # Build results
    for video_id in seen_ids:
        views = view_counts.get(video_id, 0)

        # Apply view filter (skip if views are known and below threshold)
        if min_views and views > 0 and views < min_views:
            continue

        # Reconstruct URL — we may not have the username, so use a redirect-friendly format
        # TikTok resolves /video/ID even without the username
        url = f"https://www.tiktok.com/@_/video/{video_id}"

        # Try to find the real URL with username from the page
        try:
            real_link = page.query_selector(f'a[href*="/video/{video_id}"]')
            if real_link:
                real_href = real_link.get_attribute("href") or ""
                if real_href.startswith("http"):
                    url = real_href
                elif real_href.startswith("/"):
                    url = "https://www.tiktok.com" + real_href
        except Exception:
            pass

        results.append({
            "url": url,
            "views": views,
            "keyword": keyword,
        })

    return results


if __name__ == "__main__":
    # Quick test
    results = scrape_tiktok(["gym"], max_per_keyword=5, scroll_count=2, headless=False)
    for r in results:
        print(f"  {r['views']:>10,} views | {r['url']}")
