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


def _is_on_niche(caption: str, niche: str = "") -> bool:
    """
    Check if a video caption is on-niche (relevant content we want).
    Returns False if caption hits the blocklist or misses required terms.
    """
    import scraper_config as cfg

    if not caption or len(caption.strip()) < 3:
        return True  # No caption to judge — let it through

    cap_lower = caption.lower()

    # Check blocklist — any match = reject
    for term in cfg.CAPTION_BLOCKLIST:
        if term.lower() in cap_lower:
            return False

    # Check niche-specific required terms (if configured)
    required = cfg.NICHE_REQUIRED_TERMS.get(niche, [])
    if required:
        # At least ONE required term must appear
        if not any(term.lower() in cap_lower for term in required):
            return False

    return True


# Active niche — set by the scraper entry point so filters know which niche we're scraping
_active_niche = ""


def set_active_niche(niche: str):
    """Set the active niche for relevance filtering."""
    global _active_niche
    _active_niche = niche


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
                  scroll_count=5, headless=True, min_engagement_ratio=0.0,
                  min_interactions=0, on_keyword_done=None):
    """
    Scrape TikTok search results for given keywords.

    Args:
        on_keyword_done: Optional callback(keyword, new_results) called after
                         each keyword finishes. Use this to save/download
                         incrementally so nothing is lost on crash.

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
            args=STEALTH_ARGS,
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        for ki, keyword in enumerate(keywords, 1):
            print(f"\n  ── Keyword {ki}/{len(keywords)} ──")
            keyword_results = []

            try:
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
                    time.sleep(random.uniform(3, 5))
                    # Nudge scroll up then back down to trigger lazy loading
                    page.evaluate("window.scrollBy(0, -300)")
                    time.sleep(random.uniform(0.5, 1))
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(random.uniform(1.5, 2.5))
                    # Check if new videos loaded
                    cur_count = len(page.query_selector_all('a[href*="/video/"]'))
                    print(f"   📜  Scroll {i + 1}/{scroll_count} ({cur_count} links)")
                    if cur_count <= prev_count:
                        stale_scrolls += 1
                        if stale_scrolls >= 4:
                            print(f"   ⏹  No new videos loading, stopping early")
                            break
                    else:
                        stale_scrolls = 0
                    prev_count = cur_count

                # Extract video links and metadata
                videos = _extract_videos(page, keyword, min_views, min_likes, min_engagement_ratio, min_interactions)

                new_count = 0
                for vid in videos:
                    if vid["url"] not in seen_urls and new_count < max_per_keyword:
                        seen_urls.add(vid["url"])
                        all_results.append(vid)
                        keyword_results.append(vid)
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

                            liked_videos = _extract_videos(page, keyword, min_views, min_likes, min_engagement_ratio, min_interactions)
                            for vid in liked_videos:
                                if vid["url"] not in seen_urls and new_count < max_per_keyword:
                                    seen_urls.add(vid["url"])
                                    all_results.append(vid)
                                    keyword_results.append(vid)
                                    new_count += 1

                            if new_count > 0:
                                print(f"   ✅  +{new_count} more from 'Most liked' tab")
                    except Exception:
                        pass

            except Exception as e:
                print(f"   ⚠  Error on '{keyword}': {e}")
                print(f"   ⚠  Continuing to next keyword...")

            # Callback after each keyword — save progress immediately
            if on_keyword_done and keyword_results:
                on_keyword_done(keyword, keyword_results)

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


def _extract_videos(page, keyword, min_views, min_likes, min_engagement_ratio=0.0, min_interactions=0):
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
    skipped_niche = 0
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

        # Apply minimum interactions filter (likes + comments + shares)
        if min_interactions:
            total_interactions = likes + comments + shares
            if total_interactions > 0 and total_interactions < min_interactions:
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


def _extract_key_phrases(text):
    """Extract distinctive words from caption, ignoring noise."""
    import string
    # Remove emojis, hashtags, mentions, and common noise
    cleaned = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Strip emojis/unicode
    cleaned = re.sub(r'#\w+', ' ', cleaned)          # Strip hashtags
    cleaned = re.sub(r'@\w+', ' ', cleaned)          # Strip mentions
    cleaned = cleaned.lower()
    cleaned = cleaned.translate(str.maketrans('', '', string.punctuation))
    # Remove common filler words
    noise = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at',
             'to', 'for', 'of', 'and', 'or', 'but', 'its', 'it', 'this', 'that',
             'by', 'from', 'with', 'as', 'be', 'has', 'have', 'had', 'do', 'does',
             'ctto', 'credit', 'credits', 'via', 'fy', 'fyp', 'foryou',
             'foryoupage', 'viral', 'trending', 'edit', 'duet', 'stitch'}
    words = [w for w in cleaned.split() if w and len(w) > 2 and w not in noise]
    return set(words)


def _caption_matches(caption_text, target_caption, threshold=0.5):
    """
    Check if a video caption matches the target viral caption.
    Uses keyword overlap on cleaned text (strips emojis, hashtags, mentions)
    so copies with added noise still match.
    """
    if not caption_text or not target_caption:
        return False

    # Extract meaningful keywords from both
    target_keys = _extract_key_phrases(target_caption)
    cap_keys = _extract_key_phrases(caption_text)

    if not target_keys:
        return False

    # How many of the target's key phrases appear in the caption?
    overlap = len(target_keys & cap_keys) / len(target_keys)
    if overlap >= threshold:
        return True

    # Fallback: check if the core of the caption appears as a substring
    # (handles cases where the whole caption is copy-pasted with prefix/suffix noise)
    target_clean = re.sub(r'[^\w\s]', '', target_caption.lower()).strip()
    cap_clean = re.sub(r'[^\w\s]', '', caption_text.lower()).strip()

    # Check if a significant chunk of target appears in caption
    # Use a sliding window of target words
    target_words = target_clean.split()
    if len(target_words) >= 5:
        # Check if any 5-word sequence from target appears in caption
        for i in range(len(target_words) - 4):
            phrase = ' '.join(target_words[i:i+5])
            if phrase in cap_clean:
                return True

    return False


def _build_search_queries(viral_caption):
    """
    Build multiple search query variations from a viral caption.
    TikTok search returns different results for different phrasings,
    so we cast a wider net by trying several slices of the caption.
    """
    queries = []
    words = viral_caption.split()

    # Full caption (first 80 chars) — primary search
    queries.append(viral_caption[:80].strip())

    # Shorter version — first ~45 chars (sometimes surfaces different results)
    short = viral_caption[:45].strip()
    if short != queries[0]:
        queries.append(short)

    return queries


def _extract_video_cards(page):
    """Extract video card data from the DOM."""
    return page.evaluate("""() => {
        const results = [];
        const cards = document.querySelectorAll(
            'div[data-e2e="search-card-container"], ' +
            'div[data-e2e="search_video-item"], ' +
            'div[class*="DivItemContainer"], ' +
            'div[class*="VideoCard"], ' +
            'div[class*="video-feed-item"], ' +
            'div[class*="DivWrapper"], ' +
            'div[class*="search-card"], ' +
            'li[class*="video"]'
        );

        if (cards.length > 0) {
            for (const card of cards) {
                const link = card.querySelector('a[href*="/video/"]');
                if (!link) continue;
                const href = link.href || '';
                const descEl = card.querySelector(
                    '[data-e2e="search-card-desc"], ' +
                    '[data-e2e="video-desc"], ' +
                    '[class*="SpanText"], ' +
                    '[class*="video-desc"], ' +
                    '[class*="caption"], ' +
                    '[class*="DivContainer"] span, ' +
                    'a[title]'
                );
                let caption = descEl ? descEl.textContent.trim() :
                                (link.title || link.getAttribute('title') || '');
                if (!caption) {
                    caption = card.textContent.trim().substring(0, 300);
                }
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
        }

        if (results.length === 0) {
            const links = document.querySelectorAll('a[href*="/video/"]');
            for (const link of links) {
                const href = link.href || '';
                const caption = link.title || link.getAttribute('title') ||
                               link.textContent.trim().substring(0, 300) || '';
                results.push({href, caption, views: ''});
            }
        }
        return results;
    }""")


def _extract_json_captions(page):
    """Try to extract captions from TikTok's embedded JSON data."""
    return page.evaluate("""() => {
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


def _scroll_page(page, scroll_count):
    """Scroll the page to load more results. Returns total link count."""
    prev_count = 0
    stale_scrolls = 0
    for i in range(scroll_count):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(random.uniform(3, 5))
        page.evaluate("window.scrollBy(0, -300)")
        time.sleep(random.uniform(0.5, 1))
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(random.uniform(1.5, 2.5))
        cur_count = len(page.query_selector_all('a[href*="/video/"]'))
        print(f"   📜  Scroll {i + 1}/{scroll_count} ({cur_count} links)")
        if cur_count <= prev_count:
            stale_scrolls += 1
            if stale_scrolls >= 4:
                print(f"   ⏹  No new videos loading, stopping early")
                break
        else:
            stale_scrolls = 0
        prev_count = cur_count
    return prev_count


def scrape_tiktok_by_caption(viral_caption, max_videos=50, scroll_count=10,
                              headless=True, min_views=0, match_threshold=0.5):
    """
    Search TikTok for videos using a viral caption. Uses API response
    interception to get reliable captions + DOM fallback.

    Strategy:
    1. Intercept TikTok's search API XHR responses → structured JSON with
       full captions, view counts, etc.
    2. Also scrape DOM as fallback
    3. Run multiple search queries (full caption, halves, middle chunk)
    4. Match extracted captions against the viral caption

    Returns list of dicts with url, views, likes, caption, etc.
    """
    from playwright.sync_api import sync_playwright
    from urllib.parse import quote
    import json as _json

    results = []
    seen_urls = set()
    seen_video_ids = set()
    api_videos = {}          # video_id → {caption, views, likes, url, ...}
    total_checked = 0
    total_matched = 0

    has_profile = os.path.exists(BROWSER_PROFILE_DIR)
    if not has_profile:
        print("   ⚠  No saved TikTok session found. Run with --login first.")
        return results

    # Build search queries and time filters
    search_queries = _build_search_queries(viral_caption)

    # TikTok time-range filters — EACH returns a DIFFERENT set of ~24 results
    # This is the key to getting past the 24-result cap
    time_filters = [
        ("", "all time"),
        ("&publish_time=1", "last 24h"),
        ("&publish_time=7", "last week"),
        ("&publish_time=30", "last month"),
        ("&publish_time=90", "last 3 months"),
        ("&publish_time=180", "last 6 months"),
    ]

    # Sort filters — different sort orders surface different videos
    sort_filters = [
        ("", "relevance"),
        ("&sort_by=1", "most liked"),
    ]

    total_combos = len(search_queries) * len(time_filters) * len(sort_filters)
    print(f"\n🔍  Caption search: {len(search_queries)} queries × {len(time_filters)} time ranges × {len(sort_filters)} sorts = {total_combos} searches")

    def _handle_api_response(response):
        """Intercept TikTok search API responses to extract structured video data."""
        try:
            url = response.url
            # TikTok search API endpoints
            if ("/api/search/" not in url and
                "/search/item/" not in url and
                "search_item" not in url and
                "/api/recommend/" not in url):
                return
            if response.status != 200:
                return
            content_type = response.headers.get("content-type", "")
            if "json" not in content_type and "javascript" not in content_type:
                return

            body = response.text()
            # Handle JSONP wrapper if present
            if body.startswith("(") or body.startswith("jsonp"):
                start = body.index("(") + 1
                end = body.rindex(")")
                body = body[start:end]

            data = _json.loads(body)

            # TikTok API returns video list in various locations
            video_list = []
            if isinstance(data, dict):
                # Try common response structures
                for key in ["data", "item_list", "items", "video_list"]:
                    if key in data and isinstance(data[key], list):
                        video_list = data[key]
                        break
                # Nested: data.data, data.item_list, etc.
                if not video_list and "data" in data and isinstance(data["data"], dict):
                    inner = data["data"]
                    for key in ["item_list", "items", "video_list", "videos"]:
                        if key in inner and isinstance(inner[key], list):
                            video_list = inner[key]
                            break

            for item in video_list:
                if not isinstance(item, dict):
                    continue
                # Extract video ID
                vid_id = str(item.get("id", "") or item.get("video_id", "") or
                            item.get("aweme_id", ""))
                if not vid_id or len(vid_id) < 10:
                    continue
                # Extract caption/description
                desc = (item.get("desc", "") or item.get("title", "") or
                       item.get("caption", ""))
                # Extract stats
                stats = item.get("stats", {}) or item.get("statistics", {}) or {}
                views = (stats.get("playCount", 0) or stats.get("play_count", 0) or
                        item.get("play_count", 0) or 0)
                likes = (stats.get("diggCount", 0) or stats.get("digg_count", 0) or
                        item.get("digg_count", 0) or 0)
                shares = (stats.get("shareCount", 0) or stats.get("share_count", 0) or 0)
                comments = (stats.get("commentCount", 0) or stats.get("comment_count", 0) or 0)
                # Extract author for URL
                author = ""
                author_info = item.get("author", {}) or {}
                if isinstance(author_info, dict):
                    author = (author_info.get("uniqueId", "") or
                             author_info.get("unique_id", "") or
                             author_info.get("nickname", ""))

                vid_url = f"https://www.tiktok.com/@{author}/video/{vid_id}" if author else ""

                api_videos[vid_id] = {
                    "video_id": vid_id,
                    "caption": desc,
                    "views": int(views) if views else 0,
                    "likes": int(likes) if likes else 0,
                    "shares": int(shares) if shares else 0,
                    "comments": int(comments) if comments else 0,
                    "url": vid_url,
                    "author": author,
                }

        except Exception:
            pass  # Don't let API parsing errors break the scraper

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            BROWSER_PROFILE_DIR,
            headless=headless,
            args=STEALTH_ARGS,
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        # Set up API response interception
        page.on("response", _handle_api_response)

        search_num = 0
        for qi, query in enumerate(search_queries):
            if len(api_videos) >= max_videos * 3:  # Collect 3x pool to filter from
                break

            for ti, (time_param, time_label) in enumerate(time_filters):
                if len(api_videos) >= max_videos * 3:
                    break

                for si, (sort_param, sort_label) in enumerate(sort_filters):
                    if len(api_videos) >= max_videos * 3:
                        break

                    search_num += 1
                    api_before = len(api_videos)
                    search_url = f"https://www.tiktok.com/search/video?q={quote(query)}{time_param}{sort_param}"
                    print(f"\n   🔎  [{search_num}/{total_combos}] \"{query[:35]}...\" | {time_label} | {sort_label}")

                    try:
                        page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                    except Exception as e:
                        print(f"   ⚠  Failed to load: {e}")
                        continue

                    time.sleep(random.uniform(3, 5))
                    _dismiss_popups(page)
                    time.sleep(random.uniform(1, 2))

                    # Scroll to trigger API pagination + try "Load more" buttons
                    prev_api_count = len(api_videos)
                    prev_dom_count = 0
                    stale_scrolls = 0
                    for i in range(scroll_count):
                        # Scroll down
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(random.uniform(1.5, 3))

                        # Try clicking "Load more" type buttons
                        try:
                            load_more = page.query_selector(
                                'button:has-text("Load more"), '
                                'button:has-text("load more"), '
                                'div[class*="LoadMore"], '
                                'button[class*="more"], '
                                'div[class*="pagination"] button'
                            )
                            if load_more:
                                load_more.click()
                                time.sleep(random.uniform(2, 3))
                        except Exception:
                            pass

                        dom_count = len(page.query_selector_all('a[href*="/video/"]'))
                        cur_api_count = len(api_videos)

                        if dom_count <= prev_dom_count and cur_api_count <= prev_api_count:
                            stale_scrolls += 1
                            if stale_scrolls >= 3:
                                break
                        else:
                            stale_scrolls = 0

                        prev_dom_count = dom_count
                        prev_api_count = cur_api_count

                    # Extract from DOM + embedded JSON as fallback
                    dom_data = _extract_video_cards(page)
                    json_data = _extract_json_captions(page)

                    # Merge JSON data into api_videos
                    for vid_id, info in (json_data or {}).items():
                        if vid_id not in api_videos:
                            api_videos[vid_id] = {
                                "video_id": vid_id,
                                "caption": info.get("caption", ""),
                                "views": info.get("views", 0),
                                "likes": info.get("likes", 0),
                                "shares": 0, "comments": 0,
                                "url": "", "author": "",
                            }

                    # Merge DOM data
                    for item in (dom_data or []):
                        href = item.get("href", "")
                        vid_match = re.search(r'/video/(\d+)', href)
                        if not vid_match:
                            continue
                        vid_id = vid_match.group(1)
                        full_url = href if href.startswith("http") else f"https://www.tiktok.com{href}"
                        if vid_id in api_videos:
                            if not api_videos[vid_id]["url"]:
                                api_videos[vid_id]["url"] = full_url
                        else:
                            api_videos[vid_id] = {
                                "video_id": vid_id,
                                "caption": item.get("caption", ""),
                                "views": parse_count(item.get("views", "")),
                                "likes": 0, "shares": 0, "comments": 0,
                                "url": full_url, "author": "",
                            }

                    gained = len(api_videos) - api_before
                    print(f"   📡  +{gained} new ({len(api_videos)} total in pool)")

                    # Brief delay between searches
                    time.sleep(random.uniform(1, 2.5))

        context.close()

    # Now filter ALL collected videos against the viral caption
    print(f"\n   🔬  Filtering {len(api_videos)} unique videos against caption...")

    for vid_id, info in api_videos.items():
        caption = info.get("caption", "")
        views = info.get("views", 0)
        likes = info.get("likes", 0)
        url = info.get("url", "")

        if not url:
            url = f"https://www.tiktok.com/@_/video/{vid_id}"

        if url in seen_urls or vid_id in seen_video_ids:
            continue

        total_checked += 1
        has_caption = bool(caption and len(caption.strip()) > 5)

        if has_caption:
            if not _caption_matches(caption, viral_caption, match_threshold):
                continue
        else:
            # No caption extracted — skip (we can't verify it matches)
            continue

        if min_views and views > 0 and views < min_views:
            continue

        # Niche relevance filter
        if not _is_on_niche(caption, _active_niche):
            continue

        seen_urls.add(url)
        seen_video_ids.add(vid_id)
        total_matched += 1
        results.append({
            "url": url,
            "views": views,
            "likes": likes,
            "shares": info.get("shares", 0),
            "comments": info.get("comments", 0),
            "keyword": "viral_caption",
            "caption": caption[:100],
        })

        if len(results) >= max_videos:
            break

    print(f"   ✅  Total: {len(api_videos)} unique videos found, {total_checked} had captions, {total_matched} matched")
    return results


def scrape_accounts_from_captions(captions_list, max_account_videos=30,
                                   scroll_count=15, headless=True,
                                   min_views=0, match_threshold=0.35,
                                   skip_profiles=False, min_interactions=0):
    """
    Multi-caption bulk scraper:
    1. Search each caption → find accounts that use them
    2. Visit each discovered account's profile
    3. Scrape ALL their videos (not just the one that matched)

    This is how you get 100+ videos: each matching account has dozens of posts.
    """
    from playwright.sync_api import sync_playwright
    from urllib.parse import quote
    import json as _json

    discovered_authors = {}  # username → {url, matched_caption_preview}
    all_results = []
    seen_urls = set()
    seen_video_ids = set()

    has_profile = os.path.exists(BROWSER_PROFILE_DIR)
    if not has_profile:
        print("   ⚠  No saved TikTok session found. Run with --login first.")
        return []

    # ── Phase 1: Search captions to discover accounts ──────────────
    print(f"\n{'─' * 50}")
    print(f"  PHASE 1: Discover accounts from {len(captions_list)} captions")
    print(f"{'─' * 50}")

    api_videos = {}  # vid_id → info dict (shared across all searches)

    def _handle_api_response(response):
        """Intercept TikTok search API responses."""
        try:
            url = response.url
            if ("/api/search/" not in url and
                "/search/item/" not in url and
                "search_item" not in url and
                "/api/recommend/" not in url):
                return
            if response.status != 200:
                return
            content_type = response.headers.get("content-type", "")
            if "json" not in content_type and "javascript" not in content_type:
                return
            body = response.text()
            if body.startswith("(") or body.startswith("jsonp"):
                start = body.index("(") + 1
                end = body.rindex(")")
                body = body[start:end]
            data = _json.loads(body)
            video_list = []
            if isinstance(data, dict):
                for key in ["data", "item_list", "items", "video_list"]:
                    if key in data and isinstance(data[key], list):
                        video_list = data[key]
                        break
                if not video_list and "data" in data and isinstance(data["data"], dict):
                    inner = data["data"]
                    for key in ["item_list", "items", "video_list", "videos"]:
                        if key in inner and isinstance(inner[key], list):
                            video_list = inner[key]
                            break
            for item in video_list:
                if not isinstance(item, dict):
                    continue
                vid_id = str(item.get("id", "") or item.get("video_id", "") or
                            item.get("aweme_id", ""))
                if not vid_id or len(vid_id) < 10:
                    continue
                desc = (item.get("desc", "") or item.get("title", "") or
                       item.get("caption", ""))
                stats = item.get("stats", {}) or item.get("statistics", {}) or {}
                views = (stats.get("playCount") or stats.get("play_count") or
                        stats.get("viewCount") or stats.get("view_count") or 0)
                likes = (stats.get("diggCount") or stats.get("digg_count") or
                        stats.get("likeCount") or stats.get("like_count") or 0)
                shares = stats.get("shareCount") or stats.get("share_count") or 0
                comments = stats.get("commentCount") or stats.get("comment_count") or 0
                author_info = item.get("author", {}) or {}
                author = (author_info.get("uniqueId", "") or
                         author_info.get("unique_id", "") or
                         author_info.get("nickname", ""))
                vid_url = f"https://www.tiktok.com/@{author}/video/{vid_id}" if author else ""
                api_videos[vid_id] = {
                    "video_id": vid_id, "caption": desc,
                    "views": int(views) if views else 0,
                    "likes": int(likes) if likes else 0,
                    "shares": int(shares) if shares else 0,
                    "comments": int(comments) if comments else 0,
                    "url": vid_url, "author": author,
                }
        except Exception:
            pass

    # Subset of time filters (keep it fast — we just need to find accounts)
    time_filters = [
        ("", "all time"),
        ("&publish_time=7", "last week"),
        ("&publish_time=30", "last month"),
        ("&publish_time=180", "last 6 months"),
    ]
    sort_filters = [("", "relevance"), ("&sort_by=1", "most liked")]

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            BROWSER_PROFILE_DIR,
            headless=headless,
            args=STEALTH_ARGS,
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()
        page.on("response", _handle_api_response)

        for ci, caption in enumerate(captions_list):
            queries = _build_search_queries(caption)
            print(f"\n  📝  Caption {ci+1}/{len(captions_list)}: \"{caption[:50]}...\"")

            for query in queries:
                for time_param, time_label in time_filters:
                    for sort_param, sort_label in sort_filters:
                        api_before = len(api_videos)
                        search_url = f"https://www.tiktok.com/search/video?q={quote(query)}{time_param}{sort_param}"

                        try:
                            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                        except Exception:
                            continue

                        time.sleep(random.uniform(2, 4))
                        _dismiss_popups(page)
                        time.sleep(random.uniform(0.5, 1.5))

                        # Light scroll (3 scrolls — just enough to find accounts)
                        for _ in range(3):
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            time.sleep(random.uniform(1.5, 2.5))

                        # Also extract from embedded JSON
                        json_data = _extract_json_captions(page)
                        for vid_id, info in (json_data or {}).items():
                            if vid_id not in api_videos:
                                api_videos[vid_id] = {
                                    "video_id": vid_id,
                                    "caption": info.get("caption", ""),
                                    "views": info.get("views", 0),
                                    "likes": info.get("likes", 0),
                                    "shares": 0, "comments": 0,
                                    "url": "", "author": "",
                                }

                        gained = len(api_videos) - api_before
                        if gained > 0:
                            print(f"     +{gained} ({len(api_videos)} pool) | {time_label} | {sort_label}")

                        time.sleep(random.uniform(0.5, 1.5))

        # ── Match captions and extract authors ──────────────
        print(f"\n   🔬  Checking {len(api_videos)} videos for caption matches...")

        for vid_id, info in api_videos.items():
            caption_text = info.get("caption", "")
            author = info.get("author", "")
            if not caption_text or len(caption_text.strip()) < 5:
                continue

            # Check against ALL captions in the list
            for target in captions_list:
                if _caption_matches(caption_text, target, match_threshold):
                    if author and author not in discovered_authors:
                        discovered_authors[author] = {
                            "profile_url": f"https://www.tiktok.com/@{author}",
                            "matched_caption": caption_text[:60],
                            "views": info.get("views", 0),
                        }
                    # Also add this specific video to results
                    url = info.get("url", "")
                    if not url:
                        url = f"https://www.tiktok.com/@{author}/video/{vid_id}" if author else ""
                    if url and url not in seen_urls:
                        v_likes = info.get("likes", 0)
                        v_shares = info.get("shares", 0)
                        v_comments = info.get("comments", 0)
                        total_int = v_likes + v_shares + v_comments
                        if min_interactions and total_int > 0 and total_int < min_interactions:
                            continue
                        seen_urls.add(url)
                        seen_video_ids.add(vid_id)
                        all_results.append({
                            "url": url,
                            "views": info.get("views", 0),
                            "likes": v_likes,
                            "shares": v_shares,
                            "comments": v_comments,
                            "keyword": "caption_match",
                            "caption": caption_text[:100],
                            "author": author,
                        })
                    break

        print(f"   ✅  Found {len(discovered_authors)} unique accounts from caption matches")
        print(f"   ✅  {len(all_results)} videos from caption search directly")

        if not discovered_authors or skip_profiles:
            context.close()
            if skip_profiles and discovered_authors:
                print(f"   ⏭  Skipping Phase 2 (--skip-profiles). Keeping {len(all_results)} caption-matched videos.")
            return all_results

        # ── Phase 2: Scrape each discovered account's profile ──────
        print(f"\n{'─' * 50}")
        print(f"  PHASE 2: Scrape {len(discovered_authors)} account profiles")
        print(f"{'─' * 50}")

        profile_api_videos = {}

        def _handle_profile_api(response):
            """Intercept profile/user video list API responses."""
            try:
                url = response.url
                if ("/api/post/" not in url and
                    "/item_list/" not in url and
                    "post/item_list" not in url and
                    "/api/user/" not in url):
                    return
                if response.status != 200:
                    return
                content_type = response.headers.get("content-type", "")
                if "json" not in content_type and "javascript" not in content_type:
                    return
                body = response.text()
                if body.startswith("(") or body.startswith("jsonp"):
                    start = body.index("(") + 1
                    end = body.rindex(")")
                    body = body[start:end]
                data = _json.loads(body)
                video_list = []
                if isinstance(data, dict):
                    for key in ["itemList", "item_list", "items", "data"]:
                        if key in data and isinstance(data[key], list):
                            video_list = data[key]
                            break
                    if not video_list and "data" in data and isinstance(data["data"], dict):
                        inner = data["data"]
                        for key in ["itemList", "item_list", "items"]:
                            if key in inner and isinstance(inner[key], list):
                                video_list = inner[key]
                                break
                for item in video_list:
                    if not isinstance(item, dict):
                        continue
                    vid_id = str(item.get("id", "") or item.get("video_id", "") or
                                item.get("aweme_id", ""))
                    if not vid_id or len(vid_id) < 10:
                        continue
                    desc = item.get("desc", "") or item.get("title", "") or ""
                    stats = item.get("stats", {}) or item.get("statistics", {}) or {}
                    views = (stats.get("playCount") or stats.get("play_count") or
                            stats.get("viewCount") or stats.get("view_count") or 0)
                    likes = (stats.get("diggCount") or stats.get("digg_count") or
                            stats.get("likeCount") or stats.get("like_count") or 0)
                    author_info = item.get("author", {}) or {}
                    author = (author_info.get("uniqueId", "") or
                             author_info.get("unique_id", "") or "")
                    profile_api_videos[vid_id] = {
                        "video_id": vid_id, "caption": desc,
                        "views": int(views) if views else 0,
                        "likes": int(likes) if likes else 0,
                        "url": f"https://www.tiktok.com/@{author}/video/{vid_id}" if author else "",
                        "author": author,
                    }
            except Exception:
                pass

        # Add profile API interceptor
        page.on("response", _handle_profile_api)

        for ai, (username, account_info) in enumerate(discovered_authors.items()):
            profile_url = account_info["profile_url"]
            print(f"\n   👤  [{ai+1}/{len(discovered_authors)}] @{username}")
            print(f"        Matched: \"{account_info['matched_caption'][:45]}...\"")

            profile_api_videos.clear()

            try:
                page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                print(f"        ⚠  Failed to load profile: {e}")
                continue

            time.sleep(random.uniform(3, 5))
            _dismiss_popups(page)
            time.sleep(random.uniform(1, 2))

            # Scroll the profile to load videos
            prev_count = 0
            stale = 0
            for i in range(scroll_count):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(random.uniform(1.5, 3))

                # Try clicking load more
                try:
                    load_more = page.query_selector(
                        'button:has-text("Load more"), button[class*="more"]'
                    )
                    if load_more:
                        load_more.click()
                        time.sleep(random.uniform(1.5, 2.5))
                except Exception:
                    pass

                cur_count = len(page.query_selector_all('a[href*="/video/"]'))
                api_count = len(profile_api_videos)
                if cur_count <= prev_count and api_count <= prev_count:
                    stale += 1
                    if stale >= 3:
                        break
                else:
                    stale = 0
                prev_count = max(cur_count, api_count)

            # Extract videos from profile DOM
            profile_dom_videos = page.evaluate("""() => {
                const results = [];
                const links = document.querySelectorAll('a[href*="/video/"]');
                for (const link of links) {
                    const href = link.href || '';
                    // Try to get view count from nearby elements
                    let views = '';
                    const strongEls = link.querySelectorAll('strong, span');
                    for (const el of strongEls) {
                        const t = el.textContent.trim();
                        if (/^[\\d.]+[KMB]?$/i.test(t) && t.length <= 10) {
                            views = t;
                            break;
                        }
                    }
                    results.push({href, views});
                }
                return results;
            }""")

            # Also extract from embedded JSON
            profile_json = _extract_json_captions(page)

            # Merge all sources
            account_video_count = 0
            for vid_data in (profile_dom_videos or []):
                href = vid_data.get("href", "")
                vid_match = re.search(r'/video/(\d+)', href)
                if not vid_match:
                    continue
                vid_id = vid_match.group(1)
                full_url = href if href.startswith("http") else f"https://www.tiktok.com{href}"

                if full_url in seen_urls or vid_id in seen_video_ids:
                    continue

                # Check if we have API data for this video
                api_info = profile_api_videos.get(vid_id) or {}
                json_info = (profile_json or {}).get(vid_id) or {}

                views = api_info.get("views") or json_info.get("views") or parse_count(vid_data.get("views", ""))
                likes = api_info.get("likes") or json_info.get("likes") or 0

                if min_views and views > 0 and views < min_views:
                    continue

                # Niche relevance filter — reject off-topic content
                vid_caption = api_info.get("caption") or json_info.get("caption", "") or ""
                if vid_caption and not _is_on_niche(vid_caption, _active_niche):
                    continue

                shares = api_info.get("shares", 0)
                comments = api_info.get("comments", 0)
                total_interactions = likes + comments + shares
                if min_interactions and total_interactions > 0 and total_interactions < min_interactions:
                    continue

                seen_urls.add(full_url)
                seen_video_ids.add(vid_id)
                account_video_count += 1

                all_results.append({
                    "url": full_url,
                    "views": views,
                    "likes": likes,
                    "shares": shares,
                    "comments": comments,
                    "keyword": f"@{username}",
                    "caption": vid_caption[:100],
                    "author": username,
                })

                if account_video_count >= max_account_videos:
                    break

            # Also add API-only videos not found in DOM
            for vid_id, api_info in profile_api_videos.items():
                if vid_id in seen_video_ids:
                    continue
                url = api_info.get("url", "")
                if not url:
                    url = f"https://www.tiktok.com/@{username}/video/{vid_id}"
                if url in seen_urls:
                    continue

                views = api_info.get("views", 0)
                if min_views and views > 0 and views < min_views:
                    continue

                # Niche relevance filter
                api_caption = api_info.get("caption", "")
                if api_caption and not _is_on_niche(api_caption, _active_niche):
                    continue

                likes_api = api_info.get("likes", 0)
                total_interactions = likes_api
                if min_interactions and total_interactions > 0 and total_interactions < min_interactions:
                    continue

                seen_urls.add(url)
                seen_video_ids.add(vid_id)
                account_video_count += 1
                all_results.append({
                    "url": url,
                    "views": views,
                    "likes": likes_api,
                    "shares": 0, "comments": 0,
                    "keyword": f"@{username}",
                    "caption": api_caption[:100],
                    "author": username,
                })
                if account_video_count >= max_account_videos:
                    break

            print(f"        ✅  {account_video_count} videos scraped from @{username}")

            time.sleep(random.uniform(2, 4))

        context.close()

    print(f"\n   🎯  TOTAL: {len(all_results)} videos from {len(discovered_authors)} accounts")
    return all_results


def scrape_account(username, max_videos=100, scroll_count=25, headless=True,
                    min_views=0):
    """
    Scrape a single TikTok account's profile.
    Returns (videos_list, captions_list):
      - videos_list: dicts with url, views, likes, caption, etc.
      - captions_list: unique captions (for feeding into bulk caption discovery)
    """
    from playwright.sync_api import sync_playwright
    import json as _json

    username = username.lstrip("@")
    profile_url = f"https://www.tiktok.com/@{username}"

    has_profile = os.path.exists(BROWSER_PROFILE_DIR)
    if not has_profile:
        print("   ⚠  No saved TikTok session found. Run with --login first.")
        return [], []

    all_results = []
    seen_video_ids = set()
    captions = []
    profile_api_videos = {}

    def _handle_profile_api(response):
        """Intercept profile video list API responses."""
        try:
            url = response.url
            # Match profile/user video endpoints
            if ("/api/post/" not in url and
                "/item_list/" not in url and
                "post/item_list" not in url and
                "/api/user/" not in url and
                "/api/recommend/" not in url):
                return
            if response.status != 200:
                return
            content_type = response.headers.get("content-type", "")
            if "json" not in content_type and "javascript" not in content_type:
                return
            body = response.text()
            if body.startswith("(") or body.startswith("jsonp"):
                start = body.index("(") + 1
                end = body.rindex(")")
                body = body[start:end]
            data = _json.loads(body)
            video_list = []
            if isinstance(data, dict):
                for key in ["itemList", "item_list", "items", "data"]:
                    if key in data and isinstance(data[key], list):
                        video_list = data[key]
                        break
                if not video_list and "data" in data and isinstance(data["data"], dict):
                    inner = data["data"]
                    for key in ["itemList", "item_list", "items"]:
                        if key in inner and isinstance(inner[key], list):
                            video_list = inner[key]
                            break
            for item in video_list:
                if not isinstance(item, dict):
                    continue
                vid_id = str(item.get("id", "") or item.get("video_id", "") or
                            item.get("aweme_id", ""))
                if not vid_id or len(vid_id) < 10:
                    continue
                desc = item.get("desc", "") or item.get("title", "") or ""
                stats = item.get("stats", {}) or item.get("statistics", {}) or {}
                views = (stats.get("playCount") or stats.get("play_count") or
                        stats.get("viewCount") or stats.get("view_count") or 0)
                likes = (stats.get("diggCount") or stats.get("digg_count") or
                        stats.get("likeCount") or stats.get("like_count") or 0)
                shares = stats.get("shareCount") or stats.get("share_count") or 0
                comments = stats.get("commentCount") or stats.get("comment_count") or 0
                profile_api_videos[vid_id] = {
                    "video_id": vid_id, "caption": desc,
                    "views": int(views) if views else 0,
                    "likes": int(likes) if likes else 0,
                    "shares": int(shares) if shares else 0,
                    "comments": int(comments) if comments else 0,
                    "url": f"https://www.tiktok.com/@{username}/video/{vid_id}",
                    "author": username,
                }
        except Exception:
            pass

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            BROWSER_PROFILE_DIR,
            headless=headless,
            args=STEALTH_ARGS,
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()
        page.on("response", _handle_profile_api)

        print(f"\n   👤  Loading profile: @{username}")

        try:
            page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"   ⚠  Failed to load profile: {e}")
            context.close()
            return [], []

        time.sleep(random.uniform(4, 6))
        _dismiss_popups(page)
        time.sleep(random.uniform(1, 2))

        # Debug: check what's on the page
        page_url = page.url
        page_title = page.title()
        print(f"   🔗  URL: {page_url}")
        print(f"   📄  Title: {page_title}")

        # Check for various video link patterns on profile pages
        debug_counts = page.evaluate("""() => {
            return {
                'a_video': document.querySelectorAll('a[href*="/video/"]').length,
                'user_post_item': document.querySelectorAll('div[data-e2e="user-post-item"]').length,
                'user_post_item_a': document.querySelectorAll('div[data-e2e="user-post-item"] a').length,
                'item_container': document.querySelectorAll('div[class*="DivItemContainer"]').length,
                'video_feed': document.querySelectorAll('div[class*="VideoFeed"], div[class*="video-feed"]').length,
                'all_links': document.querySelectorAll('a').length,
                'data_e2e_els': document.querySelectorAll('[data-e2e]').length,
            };
        }""")
        print(f"   🔍  DOM: {debug_counts}")

        # Sample hrefs to understand link structure
        sample_links = page.evaluate("""() => {
            const links = document.querySelectorAll('a');
            const hrefs = [];
            for (const link of links) {
                const h = link.href || '';
                if (h.includes('tiktok.com') && (h.includes('/video/') || h.includes('/photo/'))) {
                    hrefs.push(h);
                }
            }
            return hrefs.slice(0, 5);
        }""")
        if sample_links:
            print(f"   🔗  Sample: {sample_links[:3]}")
        else:
            print(f"   ⚠  No /video/ or /photo/ links found in DOM")

        # Scroll to load all videos
        prev_count = 0
        stale = 0
        for i in range(scroll_count):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(random.uniform(1.5, 3))

            try:
                load_more = page.query_selector(
                    'button:has-text("Load more"), button[class*="more"]'
                )
                if load_more:
                    load_more.click()
                    time.sleep(random.uniform(1.5, 2.5))
            except Exception:
                pass

            # Broad selector to catch profile video links
            cur_dom = len(page.query_selector_all(
                'a[href*="/video/"], a[href*="/photo/"], '
                'div[data-e2e="user-post-item"] a'
            ))
            cur_api = len(profile_api_videos)
            cur_count = max(cur_dom, cur_api)

            if i < 3 or cur_count != prev_count:
                print(f"   📜  Scroll {i+1}/{scroll_count} — {cur_dom} DOM / {cur_api} API videos")

            if cur_count <= prev_count:
                stale += 1
                if stale >= 3:
                    break
            else:
                stale = 0
            prev_count = cur_count

        # Extract videos from DOM
        dom_videos = page.evaluate("""() => {
            const results = [];
            const links = document.querySelectorAll('a[href*="/video/"]');
            for (const link of links) {
                const href = link.href || '';
                let views = '';
                const strongEls = link.querySelectorAll('strong, span');
                for (const el of strongEls) {
                    const t = el.textContent.trim();
                    if (/^[\\d.]+[KMB]?$/i.test(t) && t.length <= 10) {
                        views = t;
                        break;
                    }
                }
                results.push({href, views});
            }
            return results;
        }""")

        # Extract from embedded JSON
        json_data = _extract_json_captions(page)

        context.close()

    # Merge everything
    for vid_data in (dom_videos or []):
        href = vid_data.get("href", "")
        vid_match = re.search(r'/video/(\d+)', href)
        if not vid_match:
            continue
        vid_id = vid_match.group(1)
        if vid_id in seen_video_ids:
            continue

        full_url = href if href.startswith("http") else f"https://www.tiktok.com{href}"
        api_info = profile_api_videos.get(vid_id) or {}
        json_info = (json_data or {}).get(vid_id) or {}

        views = api_info.get("views") or json_info.get("views") or parse_count(vid_data.get("views", ""))
        likes = api_info.get("likes") or json_info.get("likes") or 0
        caption = api_info.get("caption") or json_info.get("caption", "") or ""

        if min_views and views > 0 and views < min_views:
            continue

        # Niche relevance filter
        if caption and not _is_on_niche(caption, _active_niche):
            continue

        seen_video_ids.add(vid_id)
        all_results.append({
            "url": full_url,
            "views": views,
            "likes": likes,
            "shares": api_info.get("shares", 0),
            "comments": api_info.get("comments", 0),
            "keyword": f"@{username}",
            "caption": caption[:100],
            "author": username,
        })
        if caption and len(caption.strip()) > 20:
            captions.append(caption)

    # Also add API-only videos
    for vid_id, api_info in profile_api_videos.items():
        if vid_id in seen_video_ids:
            continue
        url = api_info.get("url", f"https://www.tiktok.com/@{username}/video/{vid_id}")
        views = api_info.get("views", 0)
        if min_views and views > 0 and views < min_views:
            continue
        caption = api_info.get("caption", "")
        # Niche relevance filter
        if caption and not _is_on_niche(caption, _active_niche):
            continue
        seen_video_ids.add(vid_id)
        all_results.append({
            "url": url,
            "views": views,
            "likes": api_info.get("likes", 0),
            "shares": api_info.get("shares", 0),
            "comments": api_info.get("comments", 0),
            "keyword": f"@{username}",
            "caption": caption[:100],
            "author": username,
        })
        if caption and len(caption.strip()) > 20:
            captions.append(caption)

    # Deduplicate captions
    unique_captions = list(dict.fromkeys(captions))

    print(f"   ✅  @{username}: {len(all_results)} videos, {len(unique_captions)} unique captions")
    return all_results, unique_captions


if __name__ == "__main__":
    # Quick test
    results = scrape_tiktok(["gym"], max_per_keyword=5, scroll_count=2, headless=False)
    for r in results:
        print(f"  {r['views']:>10,} views | {r['url']}")
