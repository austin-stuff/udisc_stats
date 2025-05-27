import numpy as np
import pandas as pd

class UdiscStats:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def get_unique_players_with_par(self):
        return self.df['PlayerName'].unique()

    def get_unique_players_without_par(self):
        return [item for item in self.df['PlayerName'].unique() if 'Par' not in item]

    def get_course_names_of_player(self, player):
        return self.df[self.df['PlayerName'] == player]['CourseName'].unique()

    def get_pars_of_specific_course(self, course, layout):
        return self.df[
            (self.df['PlayerName'] == "Par") & 
            (self.df['CourseName'] == course) & 
            (self.df['LayoutName'] == layout)
        ].iloc[0].dropna()

    @staticmethod
    def get_holes_from_round(data: pd.DataFrame):
        return [item for item in data.columns if item.startswith('Hole')]

    @staticmethod
    def get_last_round_scores(data: pd.DataFrame):
        holes = UdiscStats.get_holes_from_round(data)
        return data[holes].values.tolist()[0]

    @staticmethod
    def get_average_score_per_hole(data: pd.DataFrame):
        holes = UdiscStats.get_holes_from_round(data)
        return data[holes].mean().values.tolist()

    @staticmethod
    def get_best_score_per_hole(data: pd.DataFrame):
        holes = UdiscStats.get_holes_from_round(data)
        # replace 0 and 1 with NaN then get min
        return data[holes].replace(0, np.nan).replace(1, np.nan).min()

    def filter_df_by_player(self, players):
        return self.df[self.df['PlayerName'].isin(players)].dropna(how='all', axis=1)

    def filter_df_by_course(self, course):
        return self.df[self.df['CourseName'] == course].dropna(how='all', axis=1)

    @staticmethod
    def get_best_round(data: pd.DataFrame):
        return data[data['Total'] == data['Total'].min()].iloc[0]

    def get_layouts(self, selected_course):
        return self.df[self.df['CourseName'] == selected_course]['LayoutName'].unique()

    def filter_df_by_layout(self, layout):
        return self.df[self.df['LayoutName'] == layout].dropna(how='all', axis=1)

    @staticmethod
    def append_scores_to_df(scores_df, player_df, pars_df, number):
        holes = UdiscStats.get_holes_from_round(player_df)
        player_scores = player_df[holes[number - 1]].values.tolist()

        if len(player_scores) > 0:
            hole_name = holes[number - 1]
            par = int(pars_df[hole_name])
            avg_total = np.mean(player_scores)
            player = player_df['PlayerName'].iloc[0]

            aces = eagles = birdies = pars = bogeys = double_bogeys_or_worse = 0

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
