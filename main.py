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
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def handle_response(response):
            response_url = response.url.lower()

            # Catch both normal .m3u8 and the special playlist?token= URLs
            if (
                ".m3u8" in response_url
                or ("playlist" in response_url and "token=" in response_url)
                or "chunk.tvnow247.today" in response_url
            ):
                candidates.append(response.url)

        page.on("response", handle_response)

        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"  Warning: {e}")

        page.wait_for_timeout(7000)
        browser.close()

    if not candidates:
        print("  No playlist URLs detected")
        return None

    # Remove obvious junk
    clean = []
    for u in candidates:
        u_lower = u.lower()
        if any(bad in u_lower for bad in ["ads", "advert", "tracker", "analytics", "pixel", "banner"]):
            continue
        clean.append(u)

    if not clean:
        clean = candidates

    # Prefer the ones from chunk.tvnow247.today or containing token=
    preferred = [u for u in clean if "chunk.tvnow247.today" in u or "token=" in u]

    if preferred:
        best = max(preferred, key=len)
    else:
        best = max(clean, key=len)

    print(f"  Found → {best}")
    return best


# Channels
channelList = [
    ["DAZN LA LIGA 1", "https://tvnow247.top/embed/dazn-laliga/","link_8lVb_034NmWNP9JdsIWUlhm5MBx"],
    ["M+ LA LIGA 1", "https://tvnow247.top/embed/movistar-laliga/","link_8lVb_034Nmt6ryNxhI0mVh5q4Oc"],
    ["M+ CHAMPIONS LEAGUE 1", "https://tvnow247.top/embed/movistar-liga-de-campeones/","link_8lVb_034NmvWWuNzkJpCkcgzlyv"],
    ["M+ DEPORTES 1", "https://tvnow247.top/embed/movistar-deportes-4","link_8lVb_034Nn2Mw6Wn3ITpgEYsKgu"],
    ["M+ DEPORTES 2", "https://tvnow247.top/embed/movistar-deportes-2/","link_8lVb_034Nn5YWKZvxcChbeWOEd2"],
    ["M+", "https://tvnow247.top/embed/movistar-supercopa-de-espana/","link_8lVb_034NnXUCpB0efU9gpF5sOm"],
    ["ESPN DEPORTES", "https://tvnow247.top/embed/espn-deportes/","link_8lVb_034NnaO2VBvjNvfVjzwYUe"],
    ["Dsports", "https://wsdeportes.net/?v=dsports","link_8lVb_034NncacnF8WSu7c6d9JCf"],
    ["TUDN MEXICO", "https://tvnow247.top/watch/tudn-mx/","link_8lVb_034NoIbC6ECKiIfK6i2eMP"],
    ["TUDN USA", "https://tvnow247.top/watch/tudn-usa/","link_8lVb_034NoKhut6EOxcGxFI0SdJ"],
    ["TUDN USA BACKUP", "https://wsdeportes.net/?v=tudnus","link_8lVb_034NoMasiuFHzPCAjUdnRH"],
    ["TNT SPORTS 1", "https://tvnow247.top/embed/tnt-sports-1/","link_8lVb_034O37xHnyJw9Qhgmnrq4P"],
    ["TNT SPORTS 2", "https://tvnow247.top/watch/tnt-sports-2/","link_8lVb_034O3Bs1T2h2eBSouPEGI2"],
    ["TNT SPORTS 3", "https://tvnow247.top/watch/tnt-sports-3/","link_8lVb_034O3EIUngaHpbKfYbr1BY"],
    ["SKY SPORTS PREMIER LEAGUE", "https://tvnow247.top/watch/sky-sports-premier-league/","link_8lVb_034O3SJOzLgmTDKzvrS3Sm"],
    ["SKY SPORTS FOOTBALL", "https://tvnow247.top/watch/sky-sports-football/","link_8lVb_034O3W4m9jCRTn0YSbzjHG"],
    ["SKY SPORTS PLUS", "https://tvnow247.top/watch/sky-sports-plus/","link_8lVb_034O3XybhmejWwHUTAKgH8"],
    ["SKY SPORTS MAIN EVENT", "https://tvnow247.top/watch/sky-sports-main-event/","link_8lVb_034O3ZyZEPcZMzAig0BoLd"],
    ["CBS SPORTS", "https://tvnow247.top/watch/cbs-sports-network/","link_8lVb_034O3dMva5dtqQuJIijvFc"],
    
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
