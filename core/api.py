import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
BASE_URL = "https://api.sportmonks.com/v3/football"

# url = "https://api.sportmonks.com/v3/football/teams/25598"


# url = "https://api.sportmonks.com/v3/football/leagues/501?include=seasons"

# params = {"api_token": API_TOKEN}

# response = requests.get(url, params=params).json()
# print(response)

SEASON_ID = 25598  # Scotland Premiership 2025/26

# url = (
#     f"https://api.sportmonks.com/v3/football/seasons/{SEASON_ID}"  # get current season
# )

params = {
    "api_token": API_TOKEN,
    "include": "teams",  # get teams in current season
}


def write_to_json_file(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def read_from_json_file(filename):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def get_teams_in_season(season_id):
    data = read_from_json_file(f"data/standings_{season_id}.json")
    if data:
        return data

    url = f"{BASE_URL}/standings/seasons/{season_id}"
    params = {"api_token": API_TOKEN}
    response = requests.get(url, params=params)
    data = response.json()
    write_to_json_file(f"data/standings_{season_id}.json", data)
    return data


# random function to get arbitrary data
def get_data(season_id, force=False):
    prefix = "leagues"
    data = read_from_json_file(f"data/{prefix}.json")
    if data and not force:
        print("Reading from ", prefix + ".json", "\n")
        return data

    url = f"{BASE_URL}/leagues"
    params = {"api_token": API_TOKEN}
    response = requests.get(url, params=params)
    data = response.json()
    write_to_json_file(f"data/{prefix}.json", data)
    return data


data = get_data(SEASON_ID, force=True)
# for team in data.get("data", {}):
#     print(team)
# response = requests.get(url, params=params).json()

# Print team IDs & names
# for team in response["data"]["teams"]:
#    print(team["id"], team["name"])


# TEAM_ID = 53  # Example: Celtic

# # url = f"https://api.sportmonks.com/v3/football/teams/{TEAM_ID}"

# params = {"api_token": API_TOKEN, "include": "players"}

# res = requests.get(url, params=params).json()

# for p in res["data"]["players"]:
#    print(p["player_id"], p["captain"])

# PLAYER_ID = 262280  # replace with any valid ID from your list

# url = f"https://api.sportmonks.com/v3/football/players/{PLAYER_ID}"

# params = {
#     "api_token": API_TOKEN,
#     "include": "statistics",  # works on free tier for season totals
# }

# response = requests.get(url, params=params)

# print(response)
