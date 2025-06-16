import numpy as np
import pandas as pd
import copy

class UdiscStatsNew:
    def __init__(self, df: pd.DataFrame):
        self.raw_df = df
        self.df = df.copy()

    def filter_df_by_player(self, players):
        self.df = self.df[self.df['PlayerName'].isin(players)].dropna(how='all', axis=1)
    
    def filter_df_by_course(self, course):
        self.df = self.df[self.df['CourseName'] == course].dropna(how='all', axis=1)

    def filter_df_by_layout(self, layout):
        self.df = self.df[self.df['LayoutName'] == layout].dropna(how='all', axis=1)

    def return_course_names(self):
        return self.df['CourseName'].value_counts().index
    
    def return_layouts(self, selected_course):
        return self.df[self.df['CourseName'] == selected_course]['LayoutName'].unique()
    
    def return_pars_of_specific_course(self, course, layout):
        return self.raw_df[
            (self.raw_df['PlayerName'] == "Par") &
            (self.raw_df['CourseName'] == course) &
            (self.raw_df['LayoutName'] == layout)
        ].iloc[0].dropna()
    
    def return_hole_names(self):
        return [item for item in self.df.columns if item.startswith('Hole')]