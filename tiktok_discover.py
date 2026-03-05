"""
TikTok Scraper — Discover & Search Module
Uses Playwright to scrape TikTok search results and filter by engagement.

First run:  python tiktok_scraper.py --login
            (opens browser, you log in manually, session is saved)
After that: python tiktok_scraper.py -k trading
            (uses saved session, no login needed)
"""

import os
import re
import time
import random

# Persistent browser profile directory (saves cookies/login state)
BROWSER_PROFILE_DIR = os.path.join(os.path.dirname(__file__), "tiktok_browser_profile")

# Stealth args — strip automation fingerprints so TikTok doesn't block login
STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-infobars",
]


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


def login_to_tiktok():
    """
    Open a browser window for manual TikTok login.
    Saves the session so future scraping runs don't need login.
    """
    from playwright.sync_api import sync_playwright

    print("\n🔐  TikTok Login — Manual Setup")
    print("   A browser window will open.")
    print("   1. Log into TikTok (use Google, email, or QR code)")
    print("   2. Make sure you can see the home feed")
    print("   3. Close the browser window when done\n")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            BROWSER_PROFILE_DIR,
            headless=False,
            channel="chrome",
            args=STEALTH_ARGS,
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()
        page.goto("https://www.tiktok.com/login", wait_until="domcontentloaded")

        print("   ⏳  Waiting for you to log in... (close the browser when done)")

        # Wait until the browser is closed by the user
        try:
            page.wait_for_event("close", timeout=300000)  # 5 min max
        except Exception:
            pass

        try:
            context.close()
        except Exception:
            pass

    print("   ✅  Login session saved! You can now run the scraper normally.\n")


def scrape_tiktok(keywords, max_per_keyword=20, min_views=0, min_likes=0,
                  scroll_count=5, headless=True):
    """
    Scrape TikTok search results for given keywords.

    Returns list of dicts: [{"url": str, "views": int, "keyword": str}, ...]
    """
    from playwright.sync_api import sync_playwright

    all_results = []
    seen_urls = set()

    # Check if we have a saved browser profile
    has_profile = os.path.exists(BROWSER_PROFILE_DIR)
    if not has_profile:
        print("   ⚠  No saved TikTok session found.")
        print("   ⚠  Run with --login first:  py tiktok_scraper.py --login\n")

    with sync_playwright() as p:
        # Use persistent context with real Chrome to retain login cookies
        context = p.chromium.launch_persistent_context(
            BROWSER_PROFILE_DIR,
            headless=headless,
            channel="chrome",
            args=STEALTH_ARGS,
            viewport={"width": 1280, "height": 900},
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

            # Scroll to load more results (stop early if no new content)
            prev_count = 0
            stale_scrolls = 0
            for i in range(scroll_count):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(random.uniform(2, 3.5))
                # Check if new videos loaded
                cur_count = len(page.query_selector_all('a[href*="/video/"]'))
                print(f"   📜  Scroll {i + 1}/{scroll_count} ({cur_count} links)")
                if cur_count <= prev_count:
                    stale_scrolls += 1
                    if stale_scrolls >= 2:
                        print(f"   ⏹  No new videos loading, stopping early")
                        break
                else:
                    stale_scrolls = 0
                prev_count = cur_count

            # Extract video links and metadata
            videos = _extract_videos(page, keyword, min_views, min_likes)

            new_count = 0
            for vid in videos:
                if vid["url"] not in seen_urls and new_count < max_per_keyword:
                    seen_urls.add(vid["url"])
                    all_results.append(vid)
                    new_count += 1

            print(f"   ✅  Found {new_count} videos for '{keyword}'")

            # Try "Most liked" sort tab for additional results
            if new_count < max_per_keyword:
                try:
                    liked_tab = page.query_selector(
                        'div[data-e2e="search-sort-most-liked"], '
                        'span:has-text("Most liked"), '
                        'div[role="tab"]:has-text("Most liked")'
                    )
                    if liked_tab:
                        liked_tab.click()
                        time.sleep(random.uniform(3, 5))

                        # Scroll the "Most liked" tab
                        prev_count = 0
                        stale_scrolls = 0
                        for i in range(min(scroll_count, 5)):
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            time.sleep(random.uniform(2, 3.5))
                            cur_count = len(page.query_selector_all('a[href*="/video/"]'))
                            if cur_count <= prev_count:
                                stale_scrolls += 1
                                if stale_scrolls >= 2:
                                    break
                            else:
                                stale_scrolls = 0
                            prev_count = cur_count

                        liked_videos = _extract_videos(page, keyword, min_views, min_likes)
                        for vid in liked_videos:
                            if vid["url"] not in seen_urls and new_count < max_per_keyword:
                                seen_urls.add(vid["url"])
                                all_results.append(vid)
                                new_count += 1

                        if new_count > 0:
                            print(f"   ✅  +{new_count} more from 'Most liked' tab")
                except Exception:
                    pass

        context.close()

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

    # Strategy A: Extract from embedded JSON data (most reliable)
    try:
        view_data = page.evaluate("""() => {
            const data = {};
            // Try window globals that TikTok uses to hydrate the page
            for (const key of ['__UNIVERSAL_DATA_FOR_REHYDRATION__', 'SIGI_STATE', '__NEXT_DATA__']) {
                try {
                    const obj = window[key];
                    if (!obj) continue;
                    const str = JSON.stringify(obj);
                    const idMatches = [...str.matchAll(/"id"\\s*:\\s*"(\\d{15,})"/g)];
                    for (const m of idMatches) {
                        const vidId = m[1];
                        const idx = str.indexOf('"' + vidId + '"');
                        if (idx === -1) continue;
                        const chunk = str.substring(idx, idx + 800);
                        const pc = chunk.match(/"playCount"\\s*[:]\\s*"?(\\d+)"?/);
                        if (pc) data[vidId] = pc[1];
                    }
                } catch(e) {}
            }
            // Also scan script tags for playCount patterns
            if (Object.keys(data).length === 0) {
                const scripts = document.querySelectorAll('script');
                for (const s of scripts) {
                    const text = s.textContent || '';
                    if (text.length < 100 || !text.includes('playCount')) continue;
                    const idMatches = [...text.matchAll(/"id"\\s*:\\s*"(\\d{15,})"/g)];
                    for (const m of idMatches) {
                        const vidId = m[1];
                        const idx = text.indexOf('"' + vidId + '"');
                        if (idx === -1) continue;
                        const chunk = text.substring(idx, idx + 800);
                        const pc = chunk.match(/"playCount"\\s*[:]\\s*"?(\\d+)"?/);
                        if (pc) data[vidId] = pc[1];
                    }
                }
            }
            return data;
        }""")
        if view_data:
            view_counts = {vid_id: int(count) for vid_id, count in view_data.items()}
    except Exception:
        pass

    # Strategy B: DOM-based extraction (fallback)
    if not view_counts:
        try:
            view_data = page.evaluate("""() => {
                const data = {};
                const cards = document.querySelectorAll(
                    'div[data-e2e="search-card-container"], ' +
                    'div[class*="DivItemContainer"], ' +
                    'div[class*="VideoCard"], ' +
                    'div[class*="video-feed-item"], ' +
                    'div[class*="DivWrapper"]'
                );
                for (const card of cards) {
                    const link = card.querySelector('a[href*="/video/"]');
                    if (!link) continue;
                    const match = link.href.match(/\\/video\\/(\\d+)/);
                    if (!match) continue;
                    const elems = card.querySelectorAll('strong, span');
                    for (const el of elems) {
                        const t = el.textContent.trim();
                        if (/^[\\d.]+[KMB]?$/i.test(t) && t.length <= 10) {
                            data[match[1]] = t;
                            break;
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
