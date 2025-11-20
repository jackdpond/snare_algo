
import pandas as pd
import time
import os
from bs4 import BeautifulSoup
import requests
from io import StringIO
import re
import json
import argparse
import numpy as np

def get_pitchers_per_team(team, year):
    url = f"https://www.baseball-reference.com/teams/{team}/{year}-pitching.shtml"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br"
    }

    response = requests.get(url, headers=headers)
    time.sleep(6)
    if response.status_code != 200:
        print(f"Failed to get data for {team}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    pitching_table = soup.find('table', id='players_standard_pitching')

    pitcher_ids = set()
    for a in pitching_table.select('tbody a[href^="/players/"][href$=".shtml"]'):
        href = a['href']
        # '/players/k/kelleke01.shtml' -> 'kelleke01'
        pid = href.split('/')[-1].replace('.shtml', '')
        pitcher_ids.add(pid)

    return list(pitcher_ids)

def get_pitchers_json():
    data = dict()

    teams = teams = [
    "ARI", "ATL", "BAL", "BOS",
    "CHC", "CHW", "CIN", "CLE",
    "COL", "DET", "HOU", "KCR",
    "LAA", "LAD", "MIA", "MIL",
    "MIN", "NYM", "NYY", "OAK",
    "PHI", "PIT", "SDP", "SEA",
    "SFG", "STL", "TBR", "TEX",
    "TOR", "WSN",
    ]

    for year in range(2014, 2026):
        year = str(year)
        data[year] = dict()
        for team in teams:
            pitchers = get_pitchers_per_team(team, year)
            data[year][team] = pitchers

        with open("pitcher_ids.json", "w") as f:
            json.dump(data, f, indent=4)


def get_pitcher_log(id, year):
    """Scrape game logs for a given team and year."""
    url = f"https://www.baseball-reference.com/players/gl.fcgi?id={id}&t=p&year={year}"
    print(url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br"
    }

    response = requests.get(url, headers=headers)
    time.sleep(6)
    if response.status_code != 200:
        print(f"Failed to get data for {id} {year}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the game logs table
    table = soup.find('table', {'id': 'players_standard_pitching'})
    if not table:
        print(f"No log found for {id} {year}")
        return None

    # Read the table into a DataFrame using StringIO to avoid deprecation warning
    df = pd.read_html(StringIO(str(table)))[0]
    df['Id'] = id

    df = df[df['Rk'] != 'Rk']
    df.drop(columns=['Rk'], inplace=True)
    df = df.rename(columns={'Unnamed: 5': 'Home'})

    df = df.iloc[:-1]
    
    return df

def get_all_pitchers(file = 'pitcher_ids.json', start_year = 2014, out_file="pitcher_log", ps=False):
    with open(file, "r") as f:
        pitcher_ids = json.load(f)

    for year in range(start_year, 2026):
        year_logs = []
        year = str(year)
        teams = pitcher_ids[year].keys()
        for team in teams:
            ids = pitcher_ids[year][team]
            for id in ids:
                log = get_pitcher_log(id, year)

                year_logs.append(log)
        
        df_year = pd.concat(year_logs, ignore_index=True)
        df_year.to_csv(f"{out_file}_{year}.csv", index=False)


def get_pitcher_ps_log(pid):
    url = f"https://www.baseball-reference.com/players/gl.fcgi?id={pid}&t=p&post=1"
    print(url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/58.0.3029.110 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
    }

    response = requests.get(url, headers=headers)
    time.sleep(6)  # be nice to BR

    if response.status_code != 200:
        print(f"Failed to get postseason data for {pid}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # BR sometimes uses slightly different ids; try a couple + a fallback
    table = (
        soup.find("table", {"id": "players_standard_pitching"})
    )

    df = pd.read_html(StringIO(str(table)))[0]

    df["Id"] = pid

    if "Rk" in df.columns:
        df = df[df["Rk"] != "Rk"]
        df.drop(columns=["Rk"], inplace=True, errors="ignore")

    if len(df) > 0 and isinstance(df.iloc[-1]["Date"], str) and "Totals" in df.iloc[-1]["Date"]:
        df = df.iloc[:-1]

    if "Unnamed: 5" in df.columns:
        df = df.rename(columns={"Unnamed: 5": "Home"})

    return df.reset_index(drop=True)



def get_batters_per_team(team, year):
    url = f"https://www.baseball-reference.com/teams/{team}/{year}-batting.shtml"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br"
    }

    response = requests.get(url, headers=headers)
    time.sleep(6)
    if response.status_code != 200:
        print(f"Failed to get data for {team} {year} (batting)")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Team batting table
    batting_table = soup.find('table', id='players_standard_batting')
    if batting_table is None:
        print(f"No batting table found for {team} {year}")
        return []

    batter_ids = set()
    # Pull all player profile links that appear in the table body
    for a in batting_table.select('tbody a[href^="/players/"][href$=".shtml"]'):
        href = a['href']
        pid = href.split('/')[-1].replace('.shtml', '')
        batter_ids.add(pid)

    return list(batter_ids)


def get_batters_json():
    data = dict()

    teams = [
        "ARI", "ATL", "BAL", "BOS",
        "CHC", "CHW", "CIN", "CLE",
        "COL", "DET", "HOU", "KCR",
        "LAA", "LAD", "MIA", "MIL",
        "MIN", "NYM", "NYY", "OAK",
        "PHI", "PIT", "SDP", "SEA",
        "SFG", "STL", "TBR", "TEX",
        "TOR", "WSN",
    ]

    teams_25 = [
        "ARI", "ATL", "BAL", "BOS",
        "CHC", "CHW", "CIN", "CLE",
        "COL", "DET", "HOU", "KCR",
        "LAA", "LAD", "MIA", "MIL",
        "MIN", "NYM", "NYY", "ATH",
        "PHI", "PIT", "SDP", "SEA",
        "SFG", "STL", "TBR", "TEX",
        "TOR", "WSN",
    ]

    for year in range(2014, 2026):
        y = str(year)
        data[y] = {}
        print(year)

        if year == 2025:
            teams = teams_25

        for team in teams:
            batters = get_batters_per_team(team, y) or []
            data[y][team] = batters

        with open("batter_ids.json", "w") as f:
            json.dump(data, f, indent=4)


def get_batter_log(id, year):
    """Scrape batting game logs for a given player and year."""
    url = f"https://www.baseball-reference.com/players/gl.fcgi?id={id}&t=b&year={year}"
    print(url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br"
    }

    response = requests.get(url, headers=headers)
    time.sleep(6)
    if response.status_code != 200:
        print(f"Failed to get batting log for {id} {year}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table', {'id': 'players_standard_batting'})
    if not table:
        # Fallback: grab the first table that looks like a batting log
        tables = pd.read_html(StringIO(response.text))
        if not tables:
            print(f"No batting log found for {id} {year}")
            return None
        df = tables[0]
    else:
        df = pd.read_html(StringIO(str(table)))[0]

    df['Id'] = id

    # Clean like the pitcher version
    if 'Rk' in df.columns:
        df = df[df['Rk'] != 'Rk']
        df.drop(columns=['Rk'], inplace=True, errors='ignore')

    # Some pages label the home/away column as an unnamed column; standardize it
    home_col = next((c for c in df.columns if isinstance(c, str) and c.startswith('Unnamed')), None)
    if home_col:
        df = df.rename(columns={home_col: 'Home'})
    elif 'Home' not in df.columns:
        # If truly absent, create it to keep schema consistent
        df['Home'] = pd.NA

    # Drop the last row if it's a totals row
    if len(df) and isinstance(df.index[-1], (int, np.integer)) is False:
        df = df.iloc[:-1]
    elif len(df):
        # Many BR tables end with a totals row that has NaNs in Gcar/Gtm etc.; heuristic:
        maybe_total = df.tail(1)
        if maybe_total.isna().sum().mean() > 0.3:
            df = df.iloc[:-1]

    return df


def get_all_batters(file='batter_ids.json', start_year=2014, out_file="batter_log"):
    """Read batter IDs from JSON (same structure as pitcher_ids.json) and dump per-year batting logs."""
    with open(file, "r") as f:
        batter_ids = json.load(f)

    for year in range(start_year, 2026):
        y = str(year)
        if y not in batter_ids:
            print(f"No batter IDs for {y}; skipping.")
            continue

        year_logs = []
        for team, ids in batter_ids[y].items():
            if not ids:
                continue
            for pid in ids:
                log = get_batter_log(pid, y)
                if log is not None and len(log):
                    year_logs.append(log)

        if year_logs:
            df_year = pd.concat(year_logs, ignore_index=True)
            df_year.to_csv(f"{out_file}_{y}.csv", index=False)
            print(f"Wrote {out_file}_{y}.csv with {len(df_year)} rows")
        else:
            print(f"No batter logs collected for {y}")



if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--start", type=int, default=2014)
    # parser.add_argument("--pitcher", action="store_true", help="scrape pitchers")
    # parser.add_argument("--batter",  action="store_true", help="scrape batters")
    # parser.add_argument("--get_players", action="store_true")
    # args = parser.parse_args()

    # if args.pitcher:
    #     if args.get_players:
    #         get_batters_json()
    #     else:
    #         get_all_pitchers(start_year=args.start)

    # if args.batter:
    #     if args.get_players:
    #         print("getting players batter")
    #         get_batters_json()
    #     else:
    #         get_all_batters(start_year=args.start)
    df = get_pitcher_ps_log('galleza01')
    print(df.head())