import csv

import cloudscraper
import pandas

URL = "https://1xbet.whoscored.com/statisticsfeed/1/getplayerstatistics"
LEAGUE_FILE = "data/league_stats.csv"
UCL_FILE = "data/ucl_stats.csv"
EUROPA_FILE = "data/europa_stats.csv"


def load_blank():
    return pandas.DataFrame()


def load_league_stats():
    return pandas.read_csv(LEAGUE_FILE)


def load_ucl_stats():
    return pandas.read_csv(UCL_FILE)


def load_europa_stats():
    return pandas.read_csv(EUROPA_FILE)


def fetch_league_stats():
    params = {
        "category": "summary",
        "subcategory": "all",
        "statsAccumulationType": "0",
        "isCurrent": "true",
        "tournamentOptions": "2,3,4,5,22",
        "sortBy": "Rating",
        "field": "Overall",
        "isMinApp": "false",
        "page": "1",
        "numberOfPlayersToPick": "2300",
    }
    scraper = cloudscraper.create_scraper()
    response = scraper.get(URL, params=params, headers={})
    data = response.json()["playerTableStats"]
    write_to_csv(LEAGUE_FILE, data)


def fetch_ucl_stats():
    params = {
        "category": "summary",
        "subcategory": "all",
        "statsAccumulationType": "0",
        "isCurrent": "true",
        "stageId": "24796",
        "tournamentOptions": "12",
        "sortBy": "Rating",
        "field": "Overall",
        "isMinApp": "false",
        "page": "1",
        "numberOfPlayersToPick": "774",
    }
    scraper = cloudscraper.create_scraper()
    response = scraper.get(URL, params=params, headers={})
    data = response.json()["playerTableStats"]
    write_to_csv(UCL_FILE, data)


def fetch_europa_stats():
    params = {
        "category": "summary",
        "subcategory": "all",
        "statsAccumulationType": "0",
        "isCurrent": "true",
        "stageId": "24798",
        "tournamentOptions": "30",
        "sortBy": "Rating",
        "field": "Overall",
        "isMinApp": "false",
        "page": "1",
        "numberOfPlayersToPick": "789",
    }
    scraper = cloudscraper.create_scraper()
    response = scraper.get(URL, params=params, headers={})
    data = response.json()["playerTableStats"]
    write_to_csv(EUROPA_FILE, data)


def write_to_csv(file, data):
    with open(file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


# fetch_league_stats()
# fetch_europa_stats()
# fetch_ucl_stats()
