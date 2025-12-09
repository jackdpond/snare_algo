
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

def get_pitchers_per_team(team: str, year: str):
    """
    Given a team and a year, retrieve all pitcher ids for that team in that year
    
    Parameters:
        team (str): Three letter string for team name
        year (str): 4 digit year for pitcher logs

    Returns: List of pitcher IDs for corresponding team and year
    """
    # Define url with team and year
    url = f"https://www.baseball-reference.com/teams/{team}/{year}-pitching.shtml"

    # Create headers for request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br"
    }

    # Get the response of the webpage
    response = requests.get(url, headers=headers)

    # Sleep for 6 seconds to abide by terms and conditions
    time.sleep(6)

    # If response failed, abort
    if response.status_code != 200:
        print(f"Failed to get data for {team}")
        return None

    # Get bs object with html.parser
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find pitching table
    pitching_table = soup.find('table', id='players_standard_pitching')

    # Create set for pitcher ids to keep them unique
    pitcher_ids = set()
    # Iterate through entries
    for a in pitching_table.select('tbody a[href^="/players/"][href$=".shtml"]'):
        href = a['href']
        # Get final part of path, cleaning as we go
        # eg '/players/k/kelleke01.shtml' -> 'kelleke01'
        pid = href.split('/')[-1].replace('.shtml', '')
        # Add id to list of ids
        pitcher_ids.add(pid)

    # Return set of Ids as a list
    return list(pitcher_ids)

def get_pitchers_json(output_file: str="data/pitcher_ids.json"):
    """
    Gather all pitcher IDs and organize them in a json
    
    Parameters:
        output_file (str): File path to where you want the json

    Writes all pitcher IDs to a json, organized by year and then by team
    """
    # Create empty dictionary to hold data
    data = dict()

    # Make list of all 30 MLB teams
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

    # Iterate thorugh year range
    for year in range(2014, 2026):
        # year to string and put an empty dictionary as its corresponding value
        year = str(year)
        data[year] = dict()

        # Iterate through teams
        for team in teams:
            # Get list of Pitcher Ids and add them as a list as the value for [year][team]
            pitchers = get_pitchers_per_team(team, year)
            data[year][team] = pitchers

        # Write json to output_file location
        with open(output_file, "w") as f:
            json.dump(data, f, indent=4)


def get_pitcher_log(id: str, year: str):
    """
    Scrape pitcher logs for a given team and year.
    
    Parameters:
        id (str): Pitcher Id as a string
        year (str): Year from which to scrape games
    """
    # Set base url where the pitcher's log is found
    url = f"https://www.baseball-reference.com/players/gl.fcgi?id={id}&t=p&year={year}"

    # Print for debugging
    print(url)

    # Set headers for request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br"
    }

    # Get response from webpage and sleep to comply with terms and conditions
    response = requests.get(url, headers=headers)
    time.sleep(6)

    # Abort and return None if webpage doesn't respond
    if response.status_code != 200:
        print(f"Failed to get data for {id} {year}")
        return None

    # Turn text into soup object
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the game logs table
    table = soup.find('table', {'id': 'players_standard_pitching'})
    if not table:
        print(f"No log found for {id} {year}")
        return None

    # Read the table into a DataFrame using StringIO to avoid deprecation warning
    df = pd.read_html(StringIO(str(table)))[0]
    df['Id'] = id

    # Ignore headliner rows and get rid of indexing column
    df = df[df['Rk'] != 'Rk']
    df.drop(columns=['Rk'], inplace=True)
    
    # Rename home column
    df = df.rename(columns={'Unnamed: 5': 'Home'})

    # Ignore totals row
    df = df.iloc[:-1]
    
    return df

def get_all_pitchers(file: str= 'data/pitcher_ids.json', 
                     start_year: int=2014, 
                     out_file: str="data/pitcher_log"):
    """
    Scrape all pitcher logs one year at a time, and save to CSVs
    
    Parameters:
        file (str): Json with pitcher Ids organized by year and then by team
        start_year (int): Year to start on (going until 2025)
        out_file (str): base of path to save resulting CSV

    Writes pitcher log CSVs to location of your choosing.
    """
    # Read Json with pitcher Ids
    with open(file, "r") as f:
        pitcher_ids = json.load(f)

    # Iterate through years in the range
    for year in range(start_year, 2026):
        # Create empty list to hold logs for each pitcher
        year_logs = []

        # Convert year to string
        year = str(year)

        # Get list of teams for that year (All 30 every time) and iterate through
        teams = pitcher_ids[year].keys()
        for team in teams:
            # Get all pitcher IDs for each team and iterate through
            ids = pitcher_ids[year][team]
            for id in ids:
                # Get the log for each player for each year and append to list of logs
                log = get_pitcher_log(id, year)
                year_logs.append(log)
        
        # Concatenate all logs into a dataframe and save to the base file plus the year
        df_year = pd.concat(year_logs, ignore_index=True)
        df_year.to_csv(f"{out_file}_{year}.csv", index=False)


def get_pitcher_ps_log(pid: str):
    """
    This function is very similar to the get_pitcher_log() but the format and address of the webpage is a bit different. 
    There are also many less teams. Notice no years are included because all years are on the same page.
    
    Parameter:
        pid (str): Pitcher Id. 

    Return all pitcher logs from every playoff game this pitcher played in. Ever.
    """
    # Set base url of webpage
    url = f"https://www.baseball-reference.com/players/gl.fcgi?id={pid}&t=p&post=1"
    print(url)

    # Set header for request
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

    # Get response and sleep to be nice to baseball reference
    response = requests.get(url, headers=headers)
    time.sleep(6)

    # Skip if no response
    if response.status_code != 200:
        print(f"Failed to get postseason data for {pid}")
        return None

    # Create soup object with text from webpage
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the table of games. Skip if not found]
    table = (
            soup.find("table", {"id": "players_standard_pitching"})
        )
    if table is None:
        print(f"No table found for {url}")
        return None

    # Another fail-safe try-except block. Try to read in table, if table is named but empty this will catch it.
    try:
        df = pd.read_html(StringIO(str(table)))[0]
    except ValueError:
        print(f"No table found for {url}")
        return None

    # Create Id column
    df["Id"] = pid

    # Drop headliner rows and get rid of weird Rk column
    if "Rk" in df.columns:
        df = df[df["Rk"] != "Rk"]
        df.drop(columns=["Rk"], inplace=True, errors="ignore")

    # If everything is up to snuff, keep and drop the totals row
    if len(df) > 0 and isinstance(df.iloc[-1]["Date"], str) and "Totals" in df.iloc[-1]["Date"]:
        df = df.iloc[:-1]

    # Rename home column if present. As far as I can tell it's always present.
    if "Unnamed: 5" in df.columns:
        df = df.rename(columns={"Unnamed: 5": "Home"})

    # Return the final dataframe containing pitcher logs for every playoff game for this pitcher.
    return df.reset_index(drop=True)



def get_ps_pitchers(json_file: str="data/pitcher_ids.json", backup: str="data/ps_pitcher_logs.csv"):
    """
    Scrape all playoff pitcher logs one player at a time, and save to a CSV
    
    Parameters:
        json_file (str): Path to pitcher_ids, using the same one as regular season.
        backup (str): Path to checkpointing CSV. I have it defaulted to final file as well.

    Writes all playoff pitcher logs to CSV
    """
    # Handle resume / existing backup
    resume = os.path.exists(backup)
    if resume:
        pdf = pd.read_csv(backup)

        # Get list of pitcher IDs already scraped as to not rescrape them
        pids_done = set(pdf['Id'])
    else:
        # If no file exists there, just start from scratch
        pdf = None
        pids_done = set()

    # Load pitcher IDs from JSON
    with open(json_file, "r") as f:
        pitcher_ids = json.load(f)

    # Collect all IDs from nested dict: {year: {team: [ids...]}}
    ids = []
    for year, teams in pitcher_ids.items():
        for team, team_ids in teams.items():
            ids.extend(team_ids)

    # Remove IDs we've already processed
    ids = list(set(ids) - pids_done)

    # Initialize empty list of dataframes for pitchers, and an empty dataframe to update
    id_dfs = []
    updating_df = pd.DataFrame()
    counter = 0

    # Iterate through pitcher ids from the json file
    for pid in ids:
        # Get dataframe corresponding to pitcher id
        id_df = get_pitcher_ps_log(pid)

        # Skip if the dataframe is empty (lots of pitchers haven't played in the playoffs)
        if id_df is None or id_df.empty:
            continue
        
        # Add dataframe to list
        id_dfs.append(id_df)
        counter += 1

        # Periodically flush to disk every 20 pitchers
        if counter % 20 == 0:
            updating_df = pd.concat([updating_df] + id_dfs, ignore_index=True)
            updating_df.to_csv(backup, index=False)
            id_dfs = []

    # Final concat for any remaining pitchers
    pid_df = pd.concat([updating_df] + id_dfs, ignore_index=True)

    # If resuming, add the old data back in
    if resume:
        pid_df = pd.concat([pdf, pid_df], ignore_index=True)

    # Final save
    pid_df.to_csv(backup, index=False)

    return pid_df





if __name__ == "__main__":
    get_ps_pitchers()