from playwright.sync_api import sync_playwright
import requests
import json
import os

API_KEY = os.getenv("API_KEY")


def update_short_link(api_key: str, link_id: str, original_url: str, title: str = None, path: str = None):
    if not original_url:
        print("  Skipping update (no valid m3u8 found)")
        return None

    url = f"https://api.short.io/links/{link_id}"

    payload = {
        "originalURL": original_url
    }

    if title:
        payload["title"] = title
    if path:
        payload["path"] = path

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        print("  Link updated successfully")
        return response.json()
    else:
        print(f"  Update failed: {response.status_code} - {response.text}")
        return None


def is_valid_m3u8(url: str) -> bool:
    """Check if the URL is a real working m3u8 playlist"""
    try:
        r = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        if r.status_code != 200:
            return False
        text = r.text[:800].lower()
        return "#extm3u" in text
    except Exception:
        return False


def extract_m3u8(url: str, headless: bool = True):
    m3u8_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def on_request(request):
            if ".m3u8" in request.url.lower():
                m3u8_urls.add(request.url)

        def on_response(response):
            if ".m3u8" in response.url.lower():
                m3u8_urls.add(response.url)

        page.on("request", on_request)
        page.on("response", on_response)

        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"  Warning: {e}")

        page.wait_for_timeout(5000)
        browser.close()

    if not m3u8_urls:
        return None

    # ---------- FILTERING ----------
    candidates = []

    for u in m3u8_urls:
        u_lower = u.lower()

        # Skip obvious junk
        if any(bad in u_lower for bad in [
            "ads", "advert", "tracker", "analytics", "pixel",
            "error", "404", "forbidden", "thumbnail", "preview",
            "banner", "promo"
        ]):
            continue

        candidates.append(u)

    if not candidates:
        candidates = list(m3u8_urls)

    # Sort by length (longer URLs are often better) and test them
    candidates = sorted(candidates, key=len, reverse=True)

    for candidate in candidates:
        print(f"  Testing: {candidate[:80]}...")
        if is_valid_m3u8(candidate):
            print("  → Valid m3u8 found")
            return candidate

    print("  → No valid m3u8 after testing")
    return None


# Channels
channelList = [
    ["M+ CHAMPIONS LEAGUE 1", "https://tvnow247.top/embed/movistar-liga-de-campeones/", "lnk_7Q9u_Xeqfu7a54n7fCJ4CcGLTm"],
    ["M+ LA LIGA 1", "https://tvnow247.top/embed/movistar-laliga/", "lnk_7Q9u_uJNYPSsx7Y7bSmcYIfgg5"],
    ["Dazn La Liga", "https://tvnow247.top/embed/dazn-laliga/", "lnk_7Q9u_smbJ8VHPUsC9r1rz72R1g"],
    ["TNT SPORTS 1 UK", "https://tvnow247.top/embed/tnt-sports-1/", "lnk_7Q9u_lTgnfvHKZ1X5Cfcavm59F"],
    ["ESPN DEPORTES", "https://tvnow247.top/embed/espn-deportes/", "link_7Q9u_034LUN9niVnpONdrRmHJcM"],
    ["M+ DEPORTES 1", "https://tvnow247.top/embed/movistar-deportes-4", "link_7Q9u_034LURlhtFmAFNKAYO6n0d"],
    ["HBO USA", "https://tvnow247.top/embed/hbo-usa/","link_7Q9u_034LgYqOcjA360ayMYM8fp"],
    ["M+ DEPORTES 2", "https://tvnow247.top/embed/movistar-deportes-2/","link_7Q9u_034LgfnaLff6J8kR7ROKMz"],
    ["M+", "https://tvnow247.top/embed/movistar-supercopa-de-espana/","link_7Q9u_034LgnxeGnsxZqK0dhE26x"],
    ["CUATRO", "https://tvnow247.top/embed/cuatro-spain/","link_7Q9u_034LgsDnJnWjE7N2fkyQhX"],
    ["TELECINCO", "https://tvnow247.top/embed/telecinco","link_7Q9u_034Lgvx7xL3IKr4KzERSnz"],
    ["TF1", "https://tvnow247.top/embed/tf1-france/","link_7Q9u_034Lh03TJLuzajpxMEQt2j"],
    ["HBO 2", "https://tvnow247.top/embed/hbo2-usa/","link_7Q9u_034Lh5lQ2GnPzRaozCswyZ"],
    ["ESPN ARGENTINA", "https://pelotalibretv.uno/en-vivo/espn-1","link_7Q9u_034M0mAvzdTMxtXJwKPvMR"],
]


if __name__ == "__main__":
    print("Starting update job...")
    for name, embed_url, link_id in channelList:
        print(f"\nProcessing: {name}")
        new_m3u8 = extract_m3u8(embed_url, headless=True)
        if new_m3u8:
            print(f"  Final URL → {new_m3u8}")
            update_short_link(API_KEY, link_id, new_m3u8)
        else:
            print("  No valid m3u8 found")
    print("\nJob finished.")
