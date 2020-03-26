import os  # OS library
from collections import Counter  # Dict manipulations
import re  # Regular expressions library
from IPython.display import Markdown, display  # Style output display in jupyter notebook
from datetime import datetime  # datetime manipulation

import pandas as pd  # Data import, manipulation and processing

import matplotlib.pyplot as plt  # Graph making


############################################ Classes & Exceptions #######################################

# Exception class made to report errors in the functions of the project
class LigaException(Exception):
    def __init__(self, function, message):
        self.function = function
        self.message = message

    def error_msg(self):
        return 'Error in {} | {}'.format(self.function, self.message)


############################################# General ##################################################

# Creates a directory if it doesn't already exist
def create_dir(dir_name, debug=False):
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
        if debug:
            print("Directory ", dir_name, " Created ")
    else:
        if debug:
            print("Directory ", dir_name, " already exists")


# Prints a string using the Markdown(HTML) style text display tools from IPython notebooks
def printmd(string, color=None):
    colorstr = "<span style='color:{}'>{}</span>".format(color, string)
    display(Markdown(colorstr))


########################################## Download and import Data #####################################

# Reads the data of the file containing all seasons and sorts them by Date
def read_data(file_path):
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
    df = df.sort_values(by='Date')
    return df


########################################## Preprocessing Data ##########################################

# Drops NaN rows of the dataset. By default uses level 1 filter.
# level 1: guarantees that all Full Time Result values are not NaN
# level 2: guarantees that Corner, Faults, and yellow/red cards data is not NaN
# else: guarantees all data is not NaN
def drop_na(df, level=1):
    if level == 1:
        return df[df['FTR'].notna() & df['HTR'].notna()]
    elif level == 2:
        return df[df['HS'].notna()]
    else:
        return df.dropna()


# Returns all matches of a team sort by all Home matches first and then Away matches in df format.
def get_team_matches(df, team):
    home = df.loc[df['HomeTeam'] == team]
    away = df.loc[df['AwayTeam'] == team]
    return pd.concat([home, away])


# Gets the scores of a team in a df
# returns Total scores, Only Home Scores, Only Away scores
def get_team_scores(df, team):
    home = {'H': 0, 'D': 0, 'A': 0}
    away = {'H': 0, 'D': 0, 'A': 0}
    home_dict = {'H': 'Wins', 'D': 'Draws', 'A': 'Loses'}
    away_dict = {'A': 'Wins', 'D': 'Draws', 'H': 'Loses'}

    home_series = df.loc[df['HomeTeam'] == team]['FTR']
    away_series = df.loc[df['AwayTeam'] == team]['FTR']

    for x in home_series:
        home[x] += 1

    for x in away_series:
        away[x] += 1

    for key, value in home_dict.items():
        home[value] = home.pop(key)

    for key, value in away_dict.items():
        away[value] = away.pop(key)

    total = {}
    for k in home.keys():
        total[k] = home[k] + away[k]

    return total, home, away


# returns the points a team has made in a df in the total, home, away format.
def get_points(df, team):
    res = get_team_scores(df, team)
    ret = []
    for x in res:
        ret.append(x['Wins'] * 3 + x['Draws'])
    return tuple(ret)


# returns a season in the format YY-YY for the years especified.
# Optionally a season end date can be given for getting the season data until a certain point in time.
def get_season(df, season, season_end=None):
    r = re.compile('.{2}-.{2}')
    if r.match(season) is None:
        raise LigaException('get_season', 'Season format given is incorrect')

    tokens = season.split('-')
    if (tokens[0] >= tokens[1]):
        raise LigaException('get_season', 'Start season bigger or equal than end season')
    const_dm = '/07/01'
    season_start = datetime.strptime(('20' + tokens[0] + const_dm), '%Y/%m/%d')
    if season_end == None:
        season_end = datetime.strptime(('20' + tokens[1] + const_dm), '%Y/%m/%d')
    return df.loc[(df['Date'] > season_start) & (df['Date'] < season_end)]


# Uses the match date to get the season in which happened
def get_season_from_match(match):
    m_date = match['Date']
    const_d = "07-01"
    date_s = str(m_date.year) + '-' + const_d
    date = datetime.strptime(date_s, "%Y-%m-%d")
    if m_date > date:
        season = "{}-{}".format(str(m_date.year)[-2:], str(m_date.year + 1)[-2:])
    else:
        season = "{}-{}".format(str(m_date.year - 1)[-2:], str(m_date.year)[-2:])
    return season


# add season column to df
def add_season(df):
    df = df.copy()
    df['season'] = df.apply(get_season_from_match, axis=1)
    return df


# calculates the jornadas of a given season
def add_jornada_to_season(df):
    if df.empty:
        return
    df = df.copy()
    teams = df['HomeTeam'].unique()
    teams_counter = dict(zip(teams, [0] * len(teams)))

    def update_counter(match):
        home = match['HomeTeam']
        away = match['AwayTeam']
        teams_counter[home] += 1
        teams_counter[away] += 1
        return teams_counter[home]

    df['jornada'] = df.apply(update_counter, axis=1)

    return df


# adds jornada column to df. Necessary to have added previously the season column.
def add_jornada(df):
    seasons = df['season'].unique()
    divisions = df['division'].unique()

    dfl = []
    for season in seasons:
        for division in divisions:
            dfs = df[(df['season'] == season) & (df['division'] == division)]
            dfl.append(add_jornada_to_season(dfs))

    return pd.concat(dfl)


########################### Data Visualization #########################################

# Prints Team Scores in a graph form
def print_team_scores_graph(df, team):
    total, home, away = get_team_scores(df, team)

    # prepare the figure
    rows = 1
    columns = 3
    titles = ['Total', 'Home', 'Away']
    color_dict = {'Wins': 'g',
                  'Draws': 'dodgerblue',
                  'Loses': 'r'}
    f, axes = plt.subplots(rows, columns, figsize=(18, 8))

    f.suptitle(team, fontsize=16)

    def make_autopct(data):
        def my_autopct(pct):
            total = sum(data.values())
            val = int(round(pct * total / 100.0))
            return '{p:.2f}%\n({v:d})'.format(p=pct, v=val)

        return my_autopct

    for title, data, ax in zip(titles, [total, home, away], axes):
        ax.set_title(title)
        pie_wedge_collection = ax.pie(data.values(), labels=data.keys(),
                                      shadow=True, explode=[0.1, 0.1, 0.1],
                                      autopct=make_autopct(data))

        for pie_wedge in pie_wedge_collection[0]:
            pie_wedge.set_edgecolor('black')
            pie_wedge.set_facecolor(color_dict[pie_wedge.get_label()])
