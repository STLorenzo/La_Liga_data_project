import urllib3  # URL request library
import certifi  # Certifications library for secure url requests

from pathlib import Path  # Path manipulation
import shutil  # high-level operations on files and collections of files

from IPython.display import Markdown, display  # Style output display in jupyter notebook

import os  # OS library
import zipfile  # zip manipulation library

import pandas as pd  # Data import, manipulation and processing

from data_functions import create_dir  # Private library of functions related to La Liga Dataset


##################################### Functions ######################################

def get_csv_in_string(s):
    return 'http://www.football-data.co.uk/' + s.rsplit('csv"')[0].rsplit('A HREF="', 1)[1] + 'csv'


def decode_csv_string(s):
    tokens = s.rsplit('/', 2)[1:]
    season = tokens[0][:2] + '-' + tokens[0][2:]
    division = tokens[1]
    return season + '_' + division


def get_data(url, dest_folder, verbose=False):
    create_dir(dest_folder)
    # PoolManager needed by urllib3 for requests
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())

    r = http.request('GET', url, preload_content=False)
    s = r.data.decode('utf-8')
    s = s.rsplit('notes.txt', 1)[1].rsplit('Season 2002/2003', 1)[0]
    list_s = s.rsplit('Excel.gif')[1:]
    r.release_conn()

    for csv_url in map(get_csv_in_string, list_s):
        filename = decode_csv_string(csv_url)
        if verbose:
            print("Getting {} data".format(filename))
        r = http.request('GET', csv_url, preload_content=False)
        with open(dest_folder / filename, 'wb') as out:
            shutil.copyfileobj(r, out)
        r.release_conn()

    notes_url = 'http://www.football-data.co.uk/notes.txt'
    r = http.request('GET', notes_url, preload_content=False)
    with open(dest_folder / 'notes.txt', 'wb') as out:
        shutil.copyfileobj(r, out)
    r.release_conn()


def get_columns(matches_folder):
    f = open(matches_folder / "notes.txt", "r")
    f1 = f.readlines()
    columns = []
    for x in f1[:39]:
        if '=' in x:
            c = x.rsplit(' =', 1)[0]
            if 'and' in c:
                c = c.rsplit(' and', 1)[0]
            columns.append(c)
    f.close()
    return columns


def get_df(matches_folder):
    csvs = [x for x in os.listdir(matches_folder) if '.csv' in x]
    columns = get_columns(matches_folder)

    dfs = []

    for csv in csvs:
        header = pd.read_csv(matches_folder / csv, index_col=0, nrows=0).columns.tolist()
        cols = list(set(columns) & set(header))
        df = pd.read_csv(matches_folder / csv, usecols=cols)
        df['division'] = csv[-5]
        try:
            df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y')
        except ValueError:
            df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True, sort=False)
    return df
