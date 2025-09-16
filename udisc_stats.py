import numpy as np
import pandas as pd
from typing import List, Union


class UdiscStats:
    """
    A comprehensive class for analyzing UDisc scorecard data.
    Provides filtering, statistical analysis, and data processing methods.
    """
    
    def __init__(self, df: pd.DataFrame):
        self.raw_df = df.copy()
        self.df = df.copy()

    def reset_filters(self):
        """Reset the dataframe to its original state."""
        self.df = self.raw_df.copy()

    def get_unique_players_with_par(self) -> np.ndarray:
        """Get all unique player names including 'Par'."""
        return self.df['PlayerName'].unique()

    def get_unique_players_without_par(self) -> List[str]:
        """Get all unique player names excluding 'Par'."""
        return [item for item in self.df['PlayerName'].unique() if 'Par' not in item]

    def get_course_names_of_player(self, player: str) -> np.ndarray:
        """Get all course names that a specific player has played."""
        return self.raw_df[self.raw_df['PlayerName'] == player]['CourseName'].unique()

    def get_pars_of_specific_course(self, course: str, layout: str) -> pd.Series:
        """Get par values for a specific course and layout."""
        par_data = self.raw_df[
            (self.raw_df['PlayerName'] == "Par") & 
            (self.raw_df['CourseName'] == course) & 
            (self.raw_df['LayoutName'] == layout)
        ]
        
        if par_data.empty:
            raise ValueError(f"No par data found for course '{course}' and layout '{layout}'")
        
        return par_data.iloc[0].dropna()

    def get_holes_from_round(self, data: pd.DataFrame = None) -> List[str]:
        """Get list of hole column names from the dataframe."""
        df_to_use = data if data is not None else self.df
        return [item for item in df_to_use.columns if item.startswith('Hole')]

    def get_last_round_scores(self, data: pd.DataFrame = None) -> List[float]:
        """Get scores from the most recent round."""
        df_to_use = data if data is not None else self.df
        holes = self.get_holes_from_round(df_to_use)
        return df_to_use[holes].values.tolist()[0]

    def get_average_score_per_hole(self, data: pd.DataFrame = None) -> List[float]:
        """Calculate average score for each hole."""
        df_to_use = data if data is not None else self.df
        holes = self.get_holes_from_round(df_to_use)
        return df_to_use[holes].mean().values.tolist()

    def get_best_score_per_hole(self, data: pd.DataFrame = None) -> pd.Series:
        """Get the best (lowest) score for each hole, excluding aces and invalid scores."""
        df_to_use = data if data is not None else self.df
        holes = self.get_holes_from_round(df_to_use)
        return df_to_use[holes].replace(0, np.nan).replace(1, np.nan).min()

    def filter_df_by_player(self, players: Union[str, List[str]]):
        """Filter dataframe by player name(s). Modifies self.df in place."""
        if isinstance(players, str):
            players = [players]
        self.df = self.df[self.df['PlayerName'].isin(players)].dropna(how='all', axis=1)

    def filter_df_by_course(self, course: str):
        """Filter dataframe by course name. Modifies self.df in place."""
        self.df = self.df[self.df['CourseName'] == course].dropna(how='all', axis=1)

    def filter_df_by_layout(self, layout: str):
        """Filter dataframe by layout name. Modifies self.df in place."""
        self.df = self.df[self.df['LayoutName'] == layout].dropna(how='all', axis=1)

    def get_best_round(self, data: pd.DataFrame = None) -> pd.Series:
        """Get the round with the lowest total score."""
        df_to_use = data if data is not None else self.df
        return df_to_use[df_to_use['Total'] == df_to_use['Total'].min()].iloc[0]

    def get_layouts(self, selected_course: str) -> np.ndarray:
        """Get all layouts for a specific course."""
        return self.raw_df[self.raw_df['CourseName'] == selected_course]['LayoutName'].unique()

    def get_course_names(self) -> pd.Index:
        """Get course names ordered by frequency of play."""
        return self.df['CourseName'].value_counts().index

    def append_scores_to_df(self, scores_df: pd.DataFrame, player_df: pd.DataFrame, 
                           pars_df: pd.Series, hole_number: int) -> pd.DataFrame:
        """
        Append score breakdown (aces, eagles, birdies, etc.) for a specific hole to a summary dataframe.
        """
        holes = self.get_holes_from_round(player_df)
        
        if hole_number > len(holes):
            return scores_df
            
        hole_name = holes[hole_number - 1]
        player_scores = player_df[hole_name].values.tolist()

        if len(player_scores) > 0:
            par = int(pars_df[hole_name])
            player = player_df['PlayerName'].iloc[0]

            # Initialize counters
            aces = eagles = birdies = pars_count = bogeys = double_bogeys_or_worse = 0

            # Count score types
            for score in player_scores:
                if score == 1:
                    aces += 1
                elif score == par - 2:
                    eagles += 1
                elif score == par - 1:
                    birdies += 1
                elif score == par:
                    pars_count += 1
                elif score == par + 1:
                    bogeys += 1
                elif score > par + 1:
                    double_bogeys_or_worse += 1

            # Add row to dataframe
            new_row = pd.DataFrame({
                'Player': [player],
                'Aces': [aces],
                'Eagles': [eagles],
                'Birdies': [birdies],
                'Pars': [pars_count],
                'Bogeys': [bogeys],
                'DoubleBogeysOrWorse': [double_bogeys_or_worse]
            })
            scores_df = pd.concat([scores_df, new_row], ignore_index=True)

        return scores_df
