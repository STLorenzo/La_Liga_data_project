from pathlib import Path  # Path manipulation
import os  # OS library

import pandas as pd  # Data import, manipulation and processing
from datetime import datetime

from data_functions import *  # Private library of functions related to La Liga Dataset


def get_scores_prop(scores):
    l = ['Wins', 'Draws', 'Loses']
    values = [scores[x] for x in l]
    total = sum(values)
    if total == 0:
        return [0, 0, 0]
    values = [x / total for x in values]
    return values


def get_averages(df, team):
    columns = ['HS', 'AS', 'HST', 'AST', 'HF', 'AF', 'HC', 'AC',
               'HY', 'AY', 'HR', 'AR']

    home_columns = [x for x in columns if 'H' in x]
    away_columns = [x for x in columns if 'A' in x]

    if df.empty:
        ret = [0] * (len(home_columns))
        return ret, ret, ret

    home_means = df.loc[df['HomeTeam'] == team][home_columns].mean().fillna(0).to_list()
    away_means = df.loc[df['AwayTeam'] == team][away_columns].mean().fillna(0).to_list()

    total_means = [x + y for (x, y) in zip(home_means, away_means)]

    return total_means, home_means, away_means


def add_data_row_from_match(df, df_new, match):
    match_date = match['Date']
    home_team = match['HomeTeam']
    away_team = match['AwayTeam']

    season = match['season']
    jornada = match['jornada']
    division = match['division']
    h_team = match['HomeTeam']
    a_team = match['AwayTeam']
    result = match['FTR']

    df_s = get_season(df, season, season_end=match_date)
    ht_scores = get_team_scores(df_s, home_team)
    at_scores = get_team_scores(df_s, away_team)

    ht_means = get_averages(df_s, home_team)
    at_means = get_averages(df_s, away_team)

    scores = [ht_scores[0], ht_scores[1], at_scores[0], at_scores[2]]

    prop_scores = []
    for s in scores:
        for p in get_scores_prop(s):
            prop_scores.append(p)

    means = [ht_means[0], ht_means[1], at_means[0], at_means[2]]

    means = [item for sublist in means for item in sublist]

    row = [season, jornada, division, h_team, a_team]
    row = row + prop_scores + means
    row.append(result)

    df_new.loc[len(df_new)] = row


def create_input_df(df):
    p_prefix = ['ht_', 'at_']
    p_infix = ['total', 'home', 'away']
    p_suf = ['_wins%', '_draws%', '_loses%']
    p_suf2 = ['_shots', '_t_shots', '_fouls', '_corners', '_y_cards', '_r_cards']

    columns = ['season', 'jornada', 'division', 'HomeTeam', 'AwayTeam']
    for pref in p_prefix:
        for inf in p_infix:
            for suf in p_suf:
                if pref[0] == inf[0] or inf[0] == 't':
                    columns.append(pref + inf + suf)

    for pref in p_prefix:
        for inf in p_infix:
            for suf in p_suf2:
                if pref[0] == inf[0] or inf[0] == 't':
                    columns.append(pref + inf + suf)

    columns.append('result')

    input_df = pd.DataFrame(columns=columns)
    for index, match in df.iterrows():
        add_data_row_from_match(df, input_df, match)
    return input_df
