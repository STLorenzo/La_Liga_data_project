from pathlib import Path # Path manipulation
import os # OS library
from collections import Counter # Dict manipulations
import re # Regular expressions library
from IPython.display import Markdown, display # Style output display in jupyter notebook
from datetime import datetime # datetime manipulation

import pandas as pd # Data import, manipulation and processing 

import matplotlib.pyplot as plt # Graph making

class LigaException(Exception):
    def __init__(self, function, message):
        self.function = function
        self.message = message
        
    def error_msg(self):
        return 'Error in {} | {}'.format(self.function, self.message)

def create_dir(dir_name, debug=False):
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
        if debug:
            print("Directory " , dir_name ,  " Created ")
    else:
        if debug:
            print("Directory " , dir_name ,  " already exists")

def drop_na(df, level = 1):
    if level == 1:
        return df[df['FTR'].notna() & df['HTR'].notna()]
    elif level == 2:
        return df[df['HS'].notna()]
    else:
        return df.dropna()

def read_data(file_path):
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
    df = df.sort_values(by='Date')
    return df

def printmd(string, color=None):
    colorstr = "<span style='color:{}'>{}</span>".format(color, string)
    display(Markdown(colorstr))

def get_team_matches(df, team):
        home = df.loc[df['HomeTeam'] == team]
        away = df.loc[df['AwayTeam'] == team]
        return pd.concat([home, away])

def get_team_scores(df, team):
    home_dict = {'H' : 'Wins', 'D' : 'Draws', 'A' : 'Loses'}
    away_dict = {'A' : 'Wins', 'D' : 'Draws', 'H' : 'Loses'}
    
    home = df.loc[df['HomeTeam'] == team]['FTR'].value_counts().rename(home_dict).to_dict()
    away = df.loc[df['AwayTeam'] == team]['FTR'].value_counts().rename(away_dict).to_dict()

    total = dict(Counter(home)+Counter(away))

    return total, home, away

def get_points(df, team):
    res = get_team_scores(df, team)
    ret = []
    for x in res:
        ret.append(x['Wins']*3 + x['Draws'])
    return tuple(ret)

def get_season(df, season):
    r = re.compile('.{2}-.{2}')
    if r.match(season) is None:
        raise LigaException('get_season', 'Season format given is incorrect')
        
    tokens = season.split('-')
    if( tokens[0] >= tokens[1]):
        raise LigaException('get_season', 'Start season bigger or equal than end season')
    const_dm = '/07/01'
    season_start = datetime.strptime(('20' + tokens[0] + const_dm), '%Y/%m/%d')
    season_end = datetime.strptime(('20' + tokens[1] + const_dm), '%Y/%m/%d')
    return df.loc[(df['Date'] >= season_start) & (df['Date'] <= season_end)]

def print_team_scores_graph(df, team):
    total, home, away = get_team_scores(df, team)

    # prepare the figure
    rows = 1
    columns = 3
    titles = ['Total', 'Home', 'Away']
    color_dict = {'Wins' : 'g',
                 'Draws' : 'dodgerblue',
                 'Loses' : 'r'}
    f,axes=plt.subplots(rows,columns,figsize=(18,8))
    
    f.suptitle(team, fontsize=16)

    def make_autopct(data):
        def my_autopct(pct):
            total = sum(data.values())
            val = int(round(pct*total/100.0))
            return '{p:.2f}%\n({v:d})'.format(p=pct,v=val)
        return my_autopct

    for title, data, ax in zip(titles, [total, home, away], axes):
        ax.set_title(title)
        pie_wedge_collection = ax.pie(data.values(), labels=data.keys(),
                                      shadow = True, explode=[0.1,0.1,0.1],
                                      autopct=make_autopct(data))
        
        for pie_wedge in pie_wedge_collection[0]:
            pie_wedge.set_edgecolor('black')
            pie_wedge.set_facecolor(color_dict[pie_wedge.get_label()])









