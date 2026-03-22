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
from difflib import SequenceMatcher

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
            # channel="chrome",  # Use bundled Chromium instead of system Chrome
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
                  scroll_count=5, headless=True, min_engagement_ratio=0.0):
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
            # channel="chrome",  # Use bundled Chromium instead of system Chrome
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
            videos = _extract_videos(page, keyword, min_views, min_likes, min_engagement_ratio)

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

                        liked_videos = _extract_videos(page, keyword, min_views, min_likes, min_engagement_ratio)
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


def _extract_videos(page, keyword, min_views, min_likes, min_engagement_ratio=0.0):
    """Extract video URLs, view counts, likes, and shares from the current page."""
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

    # Now try to get view counts, likes, and shares for each video
    video_stats = {}  # {video_id: {"views": int, "likes": int, "shares": int}}

    # Strategy A: Extract from embedded JSON data (most reliable)
    try:
        stats_data = page.evaluate("""() => {
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
                        const chunk = str.substring(idx, idx + 1200);
                        const pc = chunk.match(/"playCount"\\s*[:]\\s*"?(\\d+)"?/);
                        const dc = chunk.match(/"diggCount"\\s*[:]\\s*"?(\\d+)"?/);
                        const sc = chunk.match(/"shareCount"\\s*[:]\\s*"?(\\d+)"?/);
                        const cc = chunk.match(/"commentCount"\\s*[:]\\s*"?(\\d+)"?/);
                        if (pc || dc) {
                            data[vidId] = {
                                views: pc ? pc[1] : "0",
                                likes: dc ? dc[1] : "0",
                                shares: sc ? sc[1] : "0",
                                comments: cc ? cc[1] : "0",
                            };
                        }
                    }
                } catch(e) {}
            }
            // Also scan script tags
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
                        const chunk = text.substring(idx, idx + 1200);
                        const pc = chunk.match(/"playCount"\\s*[:]\\s*"?(\\d+)"?/);
                        const dc = chunk.match(/"diggCount"\\s*[:]\\s*"?(\\d+)"?/);
                        const sc = chunk.match(/"shareCount"\\s*[:]\\s*"?(\\d+)"?/);
                        const cc = chunk.match(/"commentCount"\\s*[:]\\s*"?(\\d+)"?/);
                        if (pc || dc) {
                            data[vidId] = {
                                views: pc ? pc[1] : "0",
                                likes: dc ? dc[1] : "0",
                                shares: sc ? sc[1] : "0",
                                comments: cc ? cc[1] : "0",
                            };
                        }
                    }
                }
            }
            return data;
        }""")
        if stats_data:
            for vid_id, stats in stats_data.items():
                video_stats[vid_id] = {
                    "views": int(stats.get("views", 0)),
                    "likes": int(stats.get("likes", 0)),
                    "shares": int(stats.get("shares", 0)),
                    "comments": int(stats.get("comments", 0)),
                }
    except Exception:
        pass

    # Strategy B: DOM-based extraction (fallback — views only)
    if not video_stats:
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
                for vid_id, count in view_data.items():
                    video_stats[vid_id] = {
                        "views": parse_count(count), "likes": 0,
                        "shares": 0, "comments": 0,
                    }
        except Exception:
            pass

    # Build results
    skipped_engagement = 0
    for video_id in seen_ids:
        stats = video_stats.get(video_id, {"views": 0, "likes": 0, "shares": 0, "comments": 0})
        views = stats["views"]
        likes = stats["likes"]
        shares = stats["shares"]
        comments = stats["comments"]

        # Apply view filter (skip if views are known and below threshold)
        if min_views and views > 0 and views < min_views:
            continue

        # Apply engagement ratio filter — likes/views is the best proxy for quality
        if min_engagement_ratio and views > 0 and likes > 0:
            ratio = likes / views
            if ratio < min_engagement_ratio:
                skipped_engagement += 1
                continue

        # Reconstruct URL — we may not have the username, so use a redirect-friendly format
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
            "likes": likes,
            "shares": shares,
            "comments": comments,
            "keyword": keyword,
        })

    if skipped_engagement:
        print(f"   ⏭  Skipped {skipped_engagement} low-engagement videos")

    return results


def _caption_matches(caption_text, target_caption, threshold=0.5):
    """Check if a video caption is similar enough to the target viral caption."""
    if not caption_text or not target_caption:
        return False
    # Normalize both for comparison
    cap = caption_text.lower().strip()
    target = target_caption.lower().strip()
    # Quick check: target words present in caption
    target_words = set(target.split())
    cap_words = set(cap.split())
    if not target_words:
        return False
    overlap = len(target_words & cap_words) / len(target_words)
    if overlap >= threshold:
        return True
    # Fallback: fuzzy ratio
    ratio = SequenceMatcher(None, cap[:len(target)*2], target).ratio()
    return ratio >= threshold


def scrape_tiktok_by_caption(viral_caption, max_videos=50, scroll_count=10,
                              headless=True, min_views=0, match_threshold=0.5):
    """
    Search TikTok for the viral caption text and return only videos
    whose captions match. This filters for videos using the same viral
    copy-paste caption — a strong signal they're decent content.

    Returns list of dicts: [{"url": str, "views": int, "caption": str, ...}]
    """
    from playwright.sync_api import sync_playwright

    # Use first ~60 chars of caption as search query (TikTok search has limits)
    search_query = viral_caption[:80].strip()
    results = []
    seen_urls = set()

    has_profile = os.path.exists(BROWSER_PROFILE_DIR)
    if not has_profile:
        print("   ⚠  No saved TikTok session found. Run with --login first.")
        return results

    print(f"\n🔍  Caption search: \"{search_query[:50]}...\"")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            BROWSER_PROFILE_DIR,
            headless=headless,
            args=STEALTH_ARGS,
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        # Search TikTok for the caption text
        from urllib.parse import quote
        url = f"https://www.tiktok.com/search/video?q={quote(search_query)}"

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"   ⚠  Failed to load search page: {e}")
            context.close()
            return results

        time.sleep(random.uniform(4, 7))
        _dismiss_popups(page)
        time.sleep(random.uniform(1, 2))

        # Scroll to load results
        prev_count = 0
        stale_scrolls = 0
        for i in range(scroll_count):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(random.uniform(2, 3.5))
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

        # Extract video cards with their captions
        video_data = page.evaluate("""() => {
            const results = [];
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
                const href = link.href || '';
                // Get caption/description text from the card
                const descEl = card.querySelector(
                    'span[data-e2e="search-card-desc"], ' +
                    'div[data-e2e="search-card-desc"], ' +
                    'span[class*="SpanText"], ' +
                    'div[class*="DivContainer"] span, ' +
                    'a[title]'
                );
                const caption = descEl ? descEl.textContent.trim() :
                                (link.title || link.getAttribute('title') || '');
                // Get view count
                const strongEls = card.querySelectorAll('strong, span');
                let views = '';
                for (const el of strongEls) {
                    const t = el.textContent.trim();
                    if (/^[\\d.]+[KMB]?$/i.test(t) && t.length <= 10) {
                        views = t;
                        break;
                    }
                }
                results.push({href, caption, views});
            }
            return results;
        }""")

        # Also try extracting captions from embedded JSON
        json_captions = page.evaluate("""() => {
            const data = {};
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
                        const chunk = str.substring(idx, idx + 2000);
                        const desc = chunk.match(/"desc"\\s*:\\s*"([^"]{10,})"/);
                        const pc = chunk.match(/"playCount"\\s*[:]\\s*"?(\\d+)"?/);
                        const dc = chunk.match(/"diggCount"\\s*[:]\\s*"?(\\d+)"?/);
                        if (desc) {
                            data[vidId] = {
                                caption: desc[1],
                                views: pc ? parseInt(pc[1]) : 0,
                                likes: dc ? parseInt(dc[1]) : 0,
                            };
                        }
                    }
                } catch(e) {}
            }
            return data;
        }""")

        matched = 0
        checked = 0

        # Process DOM-extracted cards
        for item in (video_data or []):
            href = item.get("href", "")
            caption = item.get("caption", "")
            views_str = item.get("views", "")

            if not href or "/video/" not in href:
                continue

            vid_match = re.search(r'/video/(\d+)', href)
            if not vid_match:
                continue

            video_id = vid_match.group(1)
            full_url = href if href.startswith("http") else f"https://www.tiktok.com{href}"

            # Check JSON data for richer caption if DOM caption is sparse
            json_info = (json_captions or {}).get(video_id, {})
            if json_info.get("caption") and len(json_info["caption"]) > len(caption):
                caption = json_info["caption"]

            views = json_info.get("views", 0) or parse_count(views_str)
            likes = json_info.get("likes", 0)

            checked += 1

            if full_url in seen_urls:
                continue

            # Filter: must match the viral caption
            if not _caption_matches(caption, viral_caption, match_threshold):
                continue

            # Filter: minimum views
            if min_views and views > 0 and views < min_views:
                continue

            seen_urls.add(full_url)
            matched += 1
            results.append({
                "url": full_url,
                "views": views,
                "likes": likes,
                "shares": 0,
                "comments": 0,
                "keyword": "viral_caption",
                "caption": caption[:100],
            })

            if len(results) >= max_videos:
                break

        # Also check JSON-only videos not found in DOM
        for video_id, info in (json_captions or {}).items():
            url = f"https://www.tiktok.com/@_/video/{video_id}"
            if url in seen_urls:
                continue
            caption = info.get("caption", "")
            views = info.get("views", 0)
            likes = info.get("likes", 0)
            checked += 1

            if not _caption_matches(caption, viral_caption, match_threshold):
                continue
            if min_views and views > 0 and views < min_views:
                continue

            # Try to get real URL
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

            seen_urls.add(url)
            matched += 1
            results.append({
                "url": url,
                "views": views,
                "likes": likes,
                "shares": 0,
                "comments": 0,
                "keyword": "viral_caption",
                "caption": caption[:100],
            })
            if len(results) >= max_videos:
                break

        context.close()

    print(f"   ✅  Checked {checked} videos, {matched} matched the viral caption")
    return results


if __name__ == "__main__":
    # Quick test
    results = scrape_tiktok(["gym"], max_per_keyword=5, scroll_count=2, headless=False)
    for r in results:
        print(f"  {r['views']:>10,} views | {r['url']}")
