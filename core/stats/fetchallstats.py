import cloudscraper
import csv
import os
from time import sleep


scraper = cloudscraper.create_scraper()

# ============================
# TOURNAMENTS + STAGE IDS HERE
# ============================

TOURNAMENTS = {
    "PremierLeague": {"tournamentOptions": 2, "stageId": 24533},
    "LaLiga": {"tournamentOptions": 4, "stageId": 24662},
    "Bundesliga": {"tournamentOptions": 3, "stageId": 24478},
    "SerieA": {"tournamentOptions": 5, "stageId": 24500},
    "Ligue1": {"tournamentOptions": 22, "stageId": 24609},
    #"ChampionsLeague": {"tournamentOptions": 12, "stageId": 24796},
    #"EuropaLeague": {"tournamentOptions": 13, "stageId": 24797},
}

CATEGORIES = ["summary", "defensive", "offensive"]



# ===============================
# SAFE CSV APPEND FUNCTION
# ===============================

def append_to_csv(filename, rows):
    """Append list of dicts to CSV; write header only once."""
    file_exists = os.path.isfile(filename)

    if not rows:
        return

    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())

        if not file_exists:
            writer.writeheader()

        writer.writerows(rows)



# ===============================
# FETCH DATA FOR ONE PAGE
# ===============================

def fetch_page(tournament, category, page):
    params = {
        "category": category,
        "subcategory": "all",
        "statsAccumulationType": 0,
        "isCurrent": "true",
        "stageId": tournament["stageId"],
        "tournamentOptions": tournament["tournamentOptions"],
        "sortBy": "Rating",
        "field": "Overall",
        "page": page,
        "numberOfPlayersToPick": 200,
        "isMinApp": "true",
    }

    headers = {"User-Agent": "Mozilla/5.0"}

    url = "https://www.whoscored.com/statisticsfeed/1/getplayerstatistics"

    resp = scraper.get(url, params=params, headers=headers)

    if resp.status_code != 200:
        print(f"Failed page {page} → HTTP {resp.status_code}")
        return None

    try:
        data = resp.json()
        return data.get("playerTableStats", [])
    except:
        print("JSON decode error.")
        print(resp.text[:200])
        return None



# ===============================
# FETCH ALL PAGES FOR ONE CATEGORY
# ===============================

def fetch_category(league_name, tournament, category):
    page = 1
    print(f"\n=== {league_name} / {category} ===")

    all_rows = []
    while True:
        print(f"Fetching page {page}...")

        rows = fetch_page(tournament, category, page)

        if not rows:
            print("No more data.")
            break

        all_rows.extend(rows)
        page += 1
        sleep(1)  # avoid rate limiting

    return all_rows



# ===============================
# MAIN FUNCTION
# ===============================

def fetch_all_leagues():
    for league_name, tournament in TOURNAMENTS.items():
        for category in CATEGORIES:

            rows = fetch_category(league_name, tournament, category)

            if not rows:
                print(f"No data for {league_name} — {category}")
                continue

            filename = f"{league_name}_{category}.csv"
            append_to_csv(filename, rows)

            print(f"✅ Saved {len(rows)} rows to {filename}")



# ===============================
# RUN SCRIPT
# ===============================

if __name__ == "__main__":
    fetch_all_leagues()
    print("\n✅ ALL DONE!")
