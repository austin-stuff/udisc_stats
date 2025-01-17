import numpy as np
def get_unique_players_with_par(df):
    return df['PlayerName'].unique()

def get_unique_players_without_par(df):
    return [item for item in df['PlayerName'].unique() if 'Par' not in item]

def get_course_names_of_player(df, player):
    return df[df['PlayerName'] == player]['CourseName'].unique()

def get_pars_of_specific_course(df,course, layout):
    return df[(df['PlayerName'] == "Par") & (df['CourseName'] == course) & (df['LayoutName'] == layout)].iloc[0].dropna()

def get_holes_from_round(data):
    return [item for item in data.columns if item.startswith('Hole')]

def get_last_round_scores(data):
    return data[get_holes_from_round(data)].values.tolist()[0]
    
def get_average_score_per_hole(data):
    return data[get_holes_from_round(data)].mean().values.tolist()

def get_best_score_per_hole(data):
    return data[get_holes_from_round(data)].replace(0, np.nan).replace(1, np.nan).min()

def filter_df_by_player(df, players):
    return df[df['PlayerName'].isin(players)].dropna(how='all', axis=1)

def filter_df_by_course(df, course):
    return df[df['CourseName'] == course].dropna(how='all', axis=1)

def get_best_round(data):
    return data[data['Total'] == data['Total'].min()].iloc[0]
    
def get_layouts(df, selected_course):
    return df[df['CourseName'] == selected_course]['LayoutName'].unique()

def filter_df_by_layout(df, layout):
    return df[df['LayoutName'] == layout].dropna(how='all', axis=1)

import pandas as pd
def append_scores_to_df(scores_df, player_df, pars_df, number):

    # Get number of holes for selection
    holes = get_holes_from_round(player_df)

    # Get scores for selected hole
    player_scores = player_df[holes[number - 1]].values.tolist()
    
    if len(player_scores) > 0:
        hole_name = holes[number - 1]
        
        par = int(pars_df[hole_name])
        # Calculate average scores for the selected hole
        avg_total = np.mean(player_scores)

        player = player_df['PlayerName'].iloc[0]

        aces = 0
        eagles = 0
        birdies = 0
        pars = 0
        bogeys = 0
        double_bogeys_or_worse = 0


        for score in player_scores:
            if score == 1:
                aces += 1
            elif score == par - 2:
                eagles += 1
            elif score == par - 1:
                birdies += 1
            elif score == par:
                pars += 1
            elif score == par + 1:
                bogeys += 1
            elif score > par + 1:
                double_bogeys_or_worse += 1

        scores_df.loc[len(scores_df)] = [player, aces, eagles, birdies, pars, bogeys, double_bogeys_or_worse]

    return scores_df