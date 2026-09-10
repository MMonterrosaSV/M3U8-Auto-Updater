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


def extract_m3u8(url: str, headless: bool = True):
    m3u8_candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def handle_response(response):
            if ".m3u8" in response.url.lower():
                try:
                    body = response.text()
                    m3u8_candidates.append({
                        "url": response.url,
                        "body": body
                    })
                except:
                    m3u8_candidates.append({
                        "url": response.url,
                        "body": None
                    })

        page.on("response", handle_response)

        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"  Warning: {e}")

        page.wait_for_timeout(6000)
        browser.close()

    if not m3u8_candidates:
        print("  No m3u8 URLs detected at all")
        return None

    # Remove obvious junk
    clean = []
    for item in m3u8_candidates:
        u = item["url"].lower()
        if any(bad in u for bad in [
            "ads", "advert", "tracker", "analytics", "pixel",
            "banner", "preview", "thumbnail", "promo"
        ]):
            continue
        clean.append(item)

    if not clean:
        clean = m3u8_candidates

    # Prefer ones that contain a real playlist
    valid = []
    for item in clean:
        if item["body"] and "#EXTM3U" in item["body"].upper():
            valid.append(item)

    if valid:
        best = max(valid, key=lambda x: len(x["url"]))
        print("  Valid m3u8 confirmed")
        return best["url"]

    # Fallback: longest URL
    best = max(clean, key=lambda x: len(x["url"]))
    print("  Using best candidate (could not fully verify body)")
    return best["url"]


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
