import streamlit as st
import numpy as np
from udisc_stats import UdiscStats
from new_class import UdiscStatsNew
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from non_streamlit_functions import *

def hole_breakdown(df):
    st.subheader("Select Player/s to Compare")
    selected_players = st.multiselect("Select players", df['PlayerName'].unique())

    if selected_players:

        col1, col2, col3 = st.columns(3)

        if len(selected_players) < 2:
            dfnew = UdiscStatsNew(df)

            dfnew.filter_df_by_player(selected_players)

            # Order the course_names by most played
            course_names = dfnew.return_course_names()

            # Display course dropdown
            selected_course = col1.selectbox("Select a course", course_names)

            # Grab the scores for the selected course
            dfnew.filter_df_by_course(selected_course)

            # Get layouts
            layouts = dfnew.return_layouts(selected_course)

            # Display layout dropdown
            layout = col2.radio("Choose a layout", layouts)

            # Filter the dataframe by selected layout
            dfnew.filter_df_by_layout(layout)            

        else:
            # Filter the dataframe by selected players
            dfnew = UdiscStatsNew(df)
            dfnew.filter_df_by_player(selected_players)

            # Find each player's course names played
            course_names = dfnew.return_course_names()

            # Extract common courses
            player_courses_total = []
            for player_df in dfnew.df.groupby('PlayerName'):
                player = player_df[0]
                player_df = player_df[1]
                player_courses = player_df['CourseName'].unique()

                player_courses_total.append(player_courses)
            for i in range(1, len(player_courses_total)):
                course_names = np.intersect1d(player_courses_total[i-1], player_courses_total[i])

            # Extract common layouts
            player_layouts_total = []
            for player_df in dfnew.df.groupby('PlayerName'):
                player = player_df[0]
                player_df = player_df[1]
                player_layouts = player_df['LayoutName'].unique()
                player_layouts_total.append(player_layouts)
            for i in range(1, len(player_layouts_total)):
                common_layouts = np.intersect1d(player_layouts_total[i-1], player_layouts_total[i])

            # Order the course_names by most played
            course_names = dfnew.df['CourseName'].value_counts().index

            # Display course dropdown
            selected_course = col1.selectbox("Select a course", course_names)

            # Grab the scores for the selected course
            dfnew.filter_df_by_course(selected_course)
            
            layouts = dfnew.return_layouts(selected_course)
            layouts = dfnew.df['LayoutName'].value_counts()
            layouts = [layout for layout in layouts.index if layout in common_layouts]

            # Display layout dropdown
            layout = col2.radio("Choose a layout", layouts)

            # Filter the dataframe by selected layout
            dfnew.filter_df_by_layout(layout)

        # Get number of holes for selection
        holes = dfnew.return_hole_names()       

        number = col3.number_input("Enter Hole", min_value=1, max_value=len(holes), value=1)

        # Get pars for the selected course and layout
        pars = dfnew.return_pars_of_specific_course(selected_course, layout)
        par = int(pars[f'Hole{number}'])

        scores_df = pd.DataFrame(columns=['Player', 'Aces', 'Eagles', 'Birdies', 'Pars', 'Bogeys', 'DoubleBogeysOrWorse'])
        
        avgs = []
        birdie_pcts = []
        # for player in selected_players:
        for player_df in dfnew.df.groupby('PlayerName'):
            player = player_df[0]
            player_df = player_df[1]
            holes = dfnew.return_hole_names()
            
            # Get hole scores for the selected hole
            scores = player_df[f'Hole{number}']

            birdie_pct = len(scores[scores < par ]) / len(scores)
            birdie_pcts.append(birdie_pct)

            avg = scores.mean()
            avgs.append(avg)

            scores_df = append_scores_to_df(scores_df, player_df, pars, number)
        
        # Update colors
        colors = ['yellow', 'lime', 'green', 'lightslategray', 'red', 'purple']
        fig = go.Figure(
            data = [
                go.Bar(x=scores_df.Player, y=scores_df.Aces, name = "Aces", textposition='outside', text=scores_df.Aces),
                go.Bar(x=scores_df.Player, y=scores_df.Eagles, name = "Eagles", textposition='outside', text=scores_df.Eagles),
                go.Bar(x=scores_df.Player, y=scores_df.Birdies, name = "Birdies", textposition='outside', text=scores_df.Birdies),
                go.Bar(x=scores_df.Player, y=scores_df.Pars, name = "Pars", textposition='outside', text=scores_df.Pars),
                go.Bar(x=scores_df.Player, y=scores_df.Bogeys, name = "Bogeys", textposition='outside', text=scores_df.Bogeys),
                go.Bar(x=scores_df.Player, y=scores_df.DoubleBogeysOrWorse, name = "Double Bogeys or Worse", textposition='outside', text=scores_df.DoubleBogeysOrWorse)
            
            ],
            layout=dict(
                barmode='group',
                bargap=0.2
            ),
        )

        # Add custom colors
        for i, trace in enumerate(fig.data):
            trace.marker.color = colors[i]

        st.title(f"{selected_course}: Hole {number}: Par {par}")
        for i in range(len(avgs)):
            st.write(f"Average Score for {selected_players[i]}: {(avgs[i]):.2f} | Birdie Percentage for {selected_players[i]}: {(birdie_pcts[i] * 100):.2f}%")
            col2.write(f"")
        st.plotly_chart(fig)


hole_breakdown(st.session_state.df)