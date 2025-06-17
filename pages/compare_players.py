import streamlit as st
import numpy as np
from udisc_stats import UdiscStats
from new_class import UdiscStatsNew
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def new(df):
    st.title("Compare Players")
    selected_players = st.multiselect("Select players", df['PlayerName'].unique())

    if selected_players:

        col1, col2, col3 = st.columns(3)

        if len(selected_players) < 2:
            dfnew = UdiscStatsNew(df)
            df = UdiscStats(df)
            
            df.filter_df_by_player(selected_players)
            dfnew.filter_df_by_player(selected_players)

            # Order the course_names by most played
            course_names = dfnew.return_course_names()
            course_names = dfnew.df['CourseName'].value_counts().index
            # course_names = df.df['CourseName'].value_counts().index

            # Display course dropdown
            selected_course = col1.selectbox("Select a course", course_names)

            # Grab the scores for the selected course
            dfnew.filter_df_by_course(selected_course)
            player_scores = df.filter_df_by_course(selected_course)

            # Get layouts
            layouts = dfnew.return_layouts(selected_course)
            # layouts = df.get_layouts(selected_course)

            # Display layout dropdown
            layout = col2.radio("Choose a layout", layouts)

            # Filter the dataframe by selected layout
            dfnew.filter_df_by_layout(layout)
            df.filter_df_by_layout(layout)

            # Get pars for the selected course and layout
            pars = dfnew.return_pars_of_specific_course(selected_course, layout)
            # pars = df.get_pars_of_specific_course(selected_course, layout)
            par = pars["Total"]

            visualization = col3.radio("Visualization Type",["Average", "Last Round", "Best Per Hole", "Best Round"])
        else:
            dfnew = UdiscStatsNew(df)
            
            # Filter the dataframe by selected players
            dfnew.filter_df_by_player(selected_players)

            # Find each player's course names played
            course_names = dfnew.return_course_names()

            # Extract common courses
            player_courses_total = []
            for player_df in dfnew.df.groupby('PlayerName'):
                player = player_df[0]
                player_df = player_df[1]
                # player_stats = filter_df_by_player(df, [player])
                player_courses = player_df['CourseName'].unique()

                player_courses_total.append(player_courses)

            for i in range(1, len(player_courses_total)):
                course_names = np.intersect1d(player_courses_total[i-1], player_courses_total[i])
        
            # Only keep the common courses
            dfnew.df = dfnew.df[dfnew.df['CourseName'].isin(course_names)]
            course_names = dfnew.df['CourseName'].value_counts().index

            # Display course dropdown
            selected_course = col1.selectbox("Select a course", course_names)

            # Extract common layouts
            player_layouts_total = []
            for player_df in dfnew.df.groupby('PlayerName'):
                player = player_df[0]
                player_df = player_df[1]
                player_layouts = player_df['LayoutName'].unique()
                player_layouts_total.append(player_layouts)
            for i in range(1, len(player_layouts_total)):
                common_layouts = np.intersect1d(player_layouts_total[i-1], player_layouts_total[i])

            

            # Grab the scores for the selected course
            dfnew.filter_df_by_course(selected_course)

            # Get common layouts
            layouts = dfnew.return_layouts(selected_course)
            layouts = dfnew.df['LayoutName'].value_counts()
            layouts = [layout for layout in layouts.index if layout in common_layouts]

            # Display layout dropdown
            layout = col2.radio("Choose a layout", layouts)

            # Filter the dataframe by selected layout
            dfnew.filter_df_by_layout(layout)

            # Get pars for the selected course and layout
            pars = dfnew.return_pars_of_specific_course(selected_course, layout)
            par = pars["Total"]
            
            visualization = col3.radio("Visualization Type",["Average", "Last Round", "Best Per Hole", "Best Round"])
        
        fig = px.scatter(title=f"Comparison of {visualization} scores")

        # Put a title text in the middle of the page
        st.title(f"{selected_course}: {layout}: Par {par}")

        # for player in selected_players:
        for player_df in dfnew.df.groupby('PlayerName'):
            player = player_df[0]
            player_df = player_df[1]
            # holes = get_holes_from_round(player_scores)
            holes = dfnew.return_hole_names()
            # get numbers from holes
            
            # player_df = filter_df_by_player(player_scores, [player])
            # player_df

            if not player_df.empty:

                if visualization == "Best Per Hole":
                    # scores = get_best_score_per_hole(player_df)
                    scores = player_df[holes].replace(0, np.nan).replace(1, np.nan).min().values.tolist()

                    st.write(f"Theoretical Best Score for {player}: {sum(scores) - par}")

                elif visualization == "Average":
                    avg_total = player_df["Total"].mean()
                    # scores = get_average_score_per_hole(player_df)
                    scores = player_df[holes].mean().values.tolist()

                    st.write(f"Average Score for {player}: {(avg_total - par):.2f}")
                
                elif visualization == "Last Round":
                    # scores = get_last_round_scores(player_df)
                    scores = player_df[holes].values.tolist()[0]

                    st.write(f"Last round score for {player}: {sum(scores) - par}")
                
                elif visualization == "Best Round":
                    # player_best_round = get_best_round(player_df)
                    player_best_round = player_df[player_df["Total"] == player_df["Total"].min()].iloc[0]
                    best_score = int(player_best_round["Total"])

                    scores = player_best_round[holes].values.tolist()
        
                    st.write(f"Best score for {player}: {best_score}, {best_score - par}")
                    

            else:
                st.write("No data found for selected players")

            holes = [int(hole[4:]) for hole in holes]

            fig.add_trace(
                go.Scatter(x=holes, y=scores, name=player, mode='markers+lines', marker=dict(size=10), text=[f'Hole: {hole}, Score: {score}' for hole, score in zip(holes, scores)])
                )
            

        fig.update_layout(
            title=f"{visualization} scores on {selected_course} {layout} layout for {', '.join(selected_players)}",
            xaxis_title='Hole',
            yaxis_title='Score',
            xaxis=dict(
                tickmode='array',
                tickvals=holes,
                showgrid=True,
            ),
        )

        st.plotly_chart(fig)
# except Exception as e:
#     st.write(f"Exception: {e}")

new(st.session_state.df)