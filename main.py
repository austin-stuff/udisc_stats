import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from non_streamlit_functions import *
import plotly.express as px
import plotly.graph_objects as go
import os
#test

def singleplayer(df):
    # try:
        st.subheader("Select Player and Course to View Stats")
        
        #player_names = get_unique_players_with_par(df)
        player_names = get_unique_players_without_par(df)

        selected_player = st.selectbox("Select a player", player_names)

        # Filter course names based on selected player
        course_names = get_course_names_of_player(df, selected_player)

        # Display course dropdown
        selected_course = st.selectbox("Select a course", course_names)

        

        player_df = filter_df_by_player(df, [selected_player])

        player_scores = filter_df_by_course(player_df, selected_course)

        layouts = get_layouts(df, selected_course)

        layout = st.selectbox("Choose a layout", layouts)

        player_scores = filter_df_by_layout(player_scores, layout)

        pars = get_pars_of_specific_course(df, selected_course, layout)


        # Display streaks (player streaks, birdie streaks, bogey streaks, par streaks, double bogey streaks, triple bogey streaks per hole)
        streaks = st.checkbox("Display Streaks")
        if streaks:
            cols = st.columns(3)
            col1, col2, col3 = cols
            col1.subheader("Under Par Streaks")
            holes = get_holes_from_round(player_scores)
            
            for hole in holes:
                under_streak = 0
                for score in player_scores[hole]:
                    # If score is less than the par, then it is a birdie
                    if score < pars[hole]:
                        under_streak += 1
                    else:
                        break
                # If streak is greather than 1, display the number as color green
                if under_streak > 0:
                    col1.markdown(f'<span style="color: green;">{hole}: {under_streak}</span>', unsafe_allow_html=True)

            col2.subheader("Par Streaks")
            for hole in holes:
                par_streak = 0
                for score in player_scores[hole]:
                    # If score is equal to the par, then it is a par
                    if score == pars[hole]:
                        par_streak += 1
                    else:
                        break
                if par_streak > 0:
                    col2.markdown(f'<span style="color: gray;">{hole}: {par_streak}</span>', unsafe_allow_html=True)

            col3.subheader("Over Par Streaks")
            for hole in holes:
                over_streak = 0
                for score in player_scores[hole]:
                    # If score is greater than the par, then it is a bogey
                    if score > pars[hole]:
                        over_streak += 1
                    else:
                        break
                if over_streak > 0:
                    col3.markdown(f'<span style="color: red;">{hole}: {over_streak}</span>', unsafe_allow_html=True)
        
        # Show side by sidehistogram of scores per hole for the course
        histogram = st.checkbox("Display Histogram")
        if histogram:
            holes = get_holes_from_round(player_scores)
            
            # Create subplots for side-by-side histograms
            fig, axes = plt.subplots(1, len(holes), figsize=(15, 5), sharey=True)

            # Iterate through each hole and create histograms
            for i, hole in enumerate(holes):
                ax = axes[i]
                ax.hist(player_scores[hole], bins=range(1, 8), edgecolor='black', linewidth= 1)

                ax.set_title(hole)
                ax.set_xlabel('Score')
                # Set x axis ticks to be 1 to 6
                ax.set_xticks(range(1, 7))
                #ax.set_xticks((min(player_scores[hole]), max(player_scores[hole])))
                
                # add grid
                ax.grid(True)
                

                # Color code the bars based on score
                for j, bar in enumerate(ax.patches):
                    if j < pars[hole] - 1:
                        bar.set_color('green')
                        bar.set_edgecolor('black')
                    elif j > pars[hole] - 1:
                        bar.set_color('red')
                        bar.set_edgecolor('black')
                    else:
                        bar.set_color('gray')
                        bar.set_edgecolor('black')

                
                if i == 0:
                    ax.set_ylabel('Frequency')


            # Set the plot title
            fig.suptitle(f'Score Distribution for {selected_player} on {selected_course}', fontsize=16)

            # Adjust spacing between subplots
            #plt.tight_layout()

            # Show the plot in Streamlit
            st.pyplot(fig)

        if histogram:
            holes = get_holes_from_round(player_scores)

            fig = px.histogram(
                player_scores,
                x=holes,
                #color_discrete_sequence=['green', 'red', 'gray'],  # You can customize the colors here
                labels={'variable': 'Hole', 'value': 'Score'},
                color = "value",
                facet_col='variable',
                facet_col_wrap=3,  # Number of columns in the subplot grid
            )

            fig.update_layout(
                title=f'Score Distribution for {selected_player} on {selected_course}',
                xaxis=dict(title='Score'),
                yaxis=dict(title='Frequency'),
            )

            st.plotly_chart(fig)

        visualization = st.selectbox("Visualization Type",["Average", "Last Round", "Best"])

        if not player_scores.empty:
            holes = get_holes_from_round(player_scores)
            par = pars[holes].values.tolist()

            if visualization == "Last Round":                
                # Plot scores for each hole
                scores = get_last_round_scores(player_scores)
                
            elif visualization == "Average":
                # Calculate average scores for each hole
                scores = get_average_score_per_hole(player_scores)

            elif visualization == "Best":
                # Calculate best (lowest) scores for each hole
                scores = get_best_score_per_hole(player_scores)

        else:
            st.write(f"No data found for {selected_player} on {selected_course}")
        
        plt.figure(figsize=(10, 6))
        plt.plot(holes, scores)
        plt.scatter(holes, scores, marker='o', color='blue', label=selected_player)
        for i, j in zip(holes, scores):
            plt.text(i, j + 0.1, f'{j:.2f}', ha='center')
        plt.plot(holes, par)
        plt.scatter(holes, par, marker='o', color='orange', label="Par")
        plt.xlabel('Hole')
        plt.ylabel('Score')
        plt.title(f"{visualization} scores for {selected_player} on {selected_course}")
        plt.xticks(rotation=45)
        plt.yticks(np.arange(1, max(scores) + 2, step=1))
        plt.grid(True)
        plt.legend()
        st.pyplot(plt)

    # except Exception as e:
    #     st.write(f"Exception: {e}")


def compareplayers(df):
    # try:
        st.subheader("Select Player/s to Compare")
        selected_players = st.multiselect("Select players", df['PlayerName'].unique())

        if selected_players:

            col1, col2, col3 = st.columns(3)

            if len(selected_players) < 2:
                player_scores = filter_df_by_player(df, selected_players)

                # Order the course_names by most played
                course_names = player_scores['CourseName'].value_counts().index

                # Display course dropdown
                selected_course = col1.selectbox("Select a course", course_names)

                # Grab the scores for the selected course
                player_scores = filter_df_by_course(player_scores, selected_course)

                # Get layouts
                layouts = get_layouts(df, selected_course)

                # Display layout dropdown
                layout = col2.radio("Choose a layout", layouts)

                # Filter the dataframe by selected layout
                player_scores = filter_df_by_layout(player_scores, layout)

                # Get pars for the selected course and layout
                pars = get_pars_of_specific_course(df, selected_course, layout)
                par = pars["Total"]

                visualization = col3.radio("Visualization Type",["Average", "Last Round", "Best Per Hole", "Best Round"])
            else:
                # Filter the dataframe by selected players
                player_scores = filter_df_by_player(df, selected_players)

                # Find each player's course names played
                course_names = player_scores['CourseName'].unique()

                # Extract common courses
                player_courses_total = []
                for player in selected_players:
                    player_stats = filter_df_by_player(df, [player])
                    player_courses = player_stats['CourseName'].unique()

                    player_courses_total.append(player_courses)
                for i in range(1, len(player_courses_total)):
                    course_names = np.intersect1d(player_courses_total[i-1], player_courses_total[i])

                # Only keep the common courses
                player_scores = player_scores[player_scores['CourseName'].isin(course_names)]

                # Extract common layouts
                player_layouts_total = []
                for player in selected_players:
                    player_stats = filter_df_by_player(player_scores, [player])
                    player_layouts = player_stats['LayoutName'].unique()

                    player_layouts_total.append(player_layouts)
                for i in range(1, len(player_layouts_total)):
                    layouts = np.intersect1d(player_layouts_total[i-1], player_layouts_total[i])

                # Only keep the common layouts
                player_scores = player_scores[player_scores['LayoutName'].isin(layouts)]

                # Order the course_names by most played
                course_names = player_scores['CourseName'].value_counts().index

                # Display course dropdown
                selected_course = col1.selectbox("Select a course", course_names)

                # Grab the scores for the selected course
                player_scores = filter_df_by_course(player_scores, selected_course)

                # Extract common layouts
                player_layouts_total = []
                for player in selected_players:
                    player_stats = filter_df_by_player(player_scores, [player])
                    player_layouts = player_stats['LayoutName'].unique()

                    player_layouts_total.append(player_layouts)
                for i in range(1, len(player_layouts_total)):
                    layouts = np.intersect1d(player_layouts_total[i-1], player_layouts_total[i])


                # Sort layouts by most played
                layouts = player_scores['LayoutName'].value_counts().index

                # Display layout dropdown
                layout = col2.radio("Choose a layout", layouts)

                # Filter the dataframe by selected layout
                player_scores = filter_df_by_layout(player_scores, layout)

                # Get pars for the selected course and layout
                pars = get_pars_of_specific_course(df, selected_course, layout)
                par = pars["Total"]
                
                visualization = col3.radio("Visualization Type",["Average", "Last Round", "Best Per Hole", "Best Round"])
            
            fig = px.scatter(title=f"Comparison of {visualization} scores")

            # Put a title text in the middle of the page
            st.title(f"{selected_course}: {layout}: Par {par}")

            for player in selected_players:
                holes = get_holes_from_round(player_scores)
                # get numbers from holes
                
                player_df = filter_df_by_player(player_scores, [player])

                if not player_scores.empty:

                    if visualization == "Best Per Hole":
                        scores = get_best_score_per_hole(player_df)

                        st.write(f"Theoretical Best Score for {player}: {sum(scores) - par}")

                    elif visualization == "Average":
                        avg_total = player_df["Total"].mean()
                        scores = get_average_score_per_hole(player_df)

                        st.write(f"Average Score for {player}: {(avg_total - par):.2f}")
                    
                    elif visualization == "Last Round":
                        scores = get_last_round_scores(player_df)

                        st.write(f"Last round score for {player}: {sum(scores) - par}")
                    
                    elif visualization == "Best Round":
                        player_best_round = get_best_round(player_df)
                        print(player_best_round)
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

def hole_breakdown(df):
    st.subheader("Select Player/s to Compare")
    selected_players = st.multiselect("Select players", df['PlayerName'].unique())

    if selected_players:

        col1, col2, col3 = st.columns(3)

        if len(selected_players) < 2:
            player_scores = filter_df_by_player(df, selected_players)

            # Order the course_names by most played
            course_names = player_scores['CourseName'].value_counts().index

            # Display course dropdown
            selected_course = col1.selectbox("Select a course", course_names)

            # Grab the scores for the selected course
            player_scores = filter_df_by_course(player_scores, selected_course)

            # Get layouts
            layouts = get_layouts(df, selected_course)

            # Display layout dropdown
            layout = col2.radio("Choose a layout", layouts)

            # Filter the dataframe by selected layout
            player_scores = filter_df_by_layout(player_scores, layout)

            

        else:
            # Filter the dataframe by selected players
            player_scores = filter_df_by_player(df, selected_players)

            # Find each player's course names played
            course_names = player_scores['CourseName'].unique()

            # Extract common courses
            player_courses_total = []
            for player in selected_players:
                player_stats = filter_df_by_player(df, [player])
                player_courses = player_stats['CourseName'].unique()

                player_courses_total.append(player_courses)
            for i in range(1, len(player_courses_total)):
                course_names = np.intersect1d(player_courses_total[i-1], player_courses_total[i])

            # Only keep the common courses
            player_scores = player_scores[player_scores['CourseName'].isin(course_names)]

            # Extract common layouts
            player_layouts_total = []
            for player in selected_players:
                player_stats = filter_df_by_player(player_scores, [player])
                player_layouts = player_stats['LayoutName'].unique()

                player_layouts_total.append(player_layouts)
            for i in range(1, len(player_layouts_total)):
                layouts = np.intersect1d(player_layouts_total[i-1], player_layouts_total[i])

            # Only keep the common layouts
            player_scores = player_scores[player_scores['LayoutName'].isin(layouts)]

            # Order the course_names by most played
            course_names = player_scores['CourseName'].value_counts().index

            # Display course dropdown
            selected_course = col1.selectbox("Select a course", course_names)

            # Grab the scores for the selected course
            player_scores = filter_df_by_course(player_scores, selected_course)

            # Extract common layouts
            player_layouts_total = []
            for player in selected_players:
                player_stats = filter_df_by_player(player_scores, [player])
                player_layouts = player_stats['LayoutName'].unique()

                player_layouts_total.append(player_layouts)

            for i in range(1, len(player_layouts_total)):
                layouts = np.intersect1d(player_layouts_total[i-1], player_layouts_total[i])

            # Sort layouts by most played
            layouts = player_scores['LayoutName'].value_counts().index

            # Display layout dropdown
            layout = col2.radio("Choose a layout", layouts)

            # Filter the dataframe by selected layout
            player_scores = filter_df_by_layout(player_scores, layout)

            
        
        # Get number of holes for selection
        holes = get_holes_from_round(player_scores)

        

        number = col3.number_input("Enter Hole", min_value=1, max_value=len(holes), value=1)

        # Get pars for the selected course and layout
        pars = get_pars_of_specific_course(df, selected_course, layout)
        par = int(pars[f'Hole{number}'])

        # Put a title text in the middle of the page
        
        scores_df = pd.DataFrame(columns=['Player', 'Aces', 'Eagles', 'Birdies', 'Pars', 'Bogeys', 'DoubleBogeysOrWorse'])
        
        avgs = []
        birdie_pcts = []
        for player in selected_players:
            
            
            # Get player df            
            player_df = filter_df_by_player(player_scores, [player])
            
            # Get hole scores for the selected hole
            scores = player_df[f'Hole{number}']

            birdie_pct = len(scores[scores < par ]) / len(scores)
            birdie_pcts.append(birdie_pct)

            avg = scores.mean()
            avgs.append(avg)

            scores_df = append_scores_to_df(scores_df, player_df, pars, number)

            # print(player_df)

        
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

def overall_stats(df):
    st.subheader("Select Player/s to Compare")
    selected_players = st.multiselect("Select players", df['PlayerName'].unique())

    if selected_players:
        for player in selected_players:
            player_df = filter_df_by_player(df, [player])
            player_scores = player_df["+/-"]
            avg = player_scores.mean()
            st.write(f"Average Score for {player}: {avg:.2f}")

            # Get average roundrating
            roundratings = player_df["RoundRating"]
            avg_rating = roundratings.mean()
            st.write(f"Average Round Rating for {player}: {avg_rating:.2f}")

            # Get highest roundrating, and display the round info
            max_rating = roundratings.max()
            info = player_df.loc[player_df["RoundRating"] == max_rating]
            course = info["CourseName"].values[0]
            layout = info["LayoutName"].values[0]

            info = filter_df_by_course(info, course)

            par = filter_df_by_player(df, ["Par"])
            par = filter_df_by_course(par, course)
            par = filter_df_by_layout(par, layout)
            
            # Convert par df to only the first row
            par = par.iloc[0:1, :]
            # Append info to par df
            info = pd.concat([par, info], axis=0).drop(columns=["CourseName", "LayoutName", "EndDate"]).dropna(axis=1)

            st.write(f"Highest Round Rating for {player}: {max_rating:.2f}: {course} {layout}") 
            st.dataframe(info)

            # Get lowest roundrating, and display the round info
            min_rating = roundratings.min()
            info = player_df.loc[player_df["RoundRating"] == min_rating]
            course = info["CourseName"].values[0]
            layout = info["LayoutName"].values[0]

            par = filter_df_by_player(df, ["Par"])
            par = filter_df_by_course(par, course)
            par = filter_df_by_layout(par, layout)

            # Convert par df to only the first row
            par = par.iloc[0:1, :]
            # Append info to par df
            info = pd.concat([par, info], axis=0).drop(columns=["CourseName", "LayoutName", "StartDate"]).dropna(axis=1)

            st.write(f"Lowest Round Rating for {player}: {min_rating:.2f} : {course} {layout}")
            st.dataframe(info)

            st.write("----------------------------------------------------------------------------------------")
            
def round_breakdown(df):

    st.subheader("Select Player/s to Compare")
    selected_player = st.selectbox("Select a player", df['PlayerName'].unique())

    sort_by = st.radio("Sort by", ["Date", "RoundRating", "+/-"])
    asc_or_desc = st.radio("Ascending or Descending", ["Ascending", "Descending"])

    player_df = filter_df_by_player(df, [selected_player])

    if sort_by == "Date":
        player_df = player_df.sort_values(by="EndDate", ascending=asc_or_desc == "Ascending")
    elif sort_by == "RoundRating":
        player_df = player_df.sort_values(by="RoundRating", ascending=asc_or_desc == "Ascending")
    elif sort_by == "+/-":
        player_df = player_df.sort_values(by="+/-", ascending=asc_or_desc == "Ascending")

    st.dataframe(player_df)


def upload_CSV():
    st.title("Upload your UDisc CSV file here")

    uploaded_file = st.file_uploader("To find your CSV file... Open the UDisc app, go to the 'More' tab, click on 'Scorecards', click the three lines in the top right corner, and then click 'Export to CSV'!", type=["csv"])

    return uploaded_file


st.set_page_config(layout="wide")

option = st.sidebar.radio("Choose your display method", ["Upload CSV", "Compare Players", "Single Player Stats", "Hole Breakdown", "Overall Stats", "Round Breakdown"])

if option == "Upload CSV":
    uploaded_file = upload_CSV()
    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        df = df.loc[~(df.iloc[:, 3:] == 0).any(axis=1)]

        # Change indian riffle course name
        df['CourseName'] = df['CourseName'].replace(['Indian Riffle Park/Kettering'], 'Indian Riffle Disc Golf Course')

        # Change belmont course name
        df['CourseName'] = df['CourseName'].replace(['Belmont Park'], 'Belmont Park Disc Golf Course')

        # Rename Karohl Park course name to Karohl Park Disc Golf Course
        df['CourseName'] = df['CourseName'].replace(['Karohl Park'], 'Karohl Park Disc Golf Course')

        # Rename LayoutName of 2018 Redesign to Main 18 Hole Layout
        df['LayoutName'] = df['LayoutName'].replace(['2018 Redesign'], 'Main 18 Hole Layout')

        # Rename LayoutName of Belmont to Short Tees with Long 16
        df['LayoutName'] = df['LayoutName'].replace(['Belmont'], 'Short Tees with Long 16')

        # # Rename LayoutName of Short Tees to Short Tees with Long 16
        # df['LayoutName'] = df['LayoutName'].replace(['Short Tees'], 'Short Tees with Long 16')

        # # Rename LayoutName of Short Tees Long Baskets to 18 Holes - Short Tees
        # df['LayoutName'] = df['LayoutName'].replace(['Short Tees Long Baskets'], '18 Holes - Short Tees')

        

        # Save the dataframe to a temp csv file for the user
        df.to_csv("temp.csv", index=False)

elif option == "Single Player Stats":
    # Read in the temp csv file
    df = pd.read_csv("temp.csv")
    singleplayer(df)

elif option == "Compare Players":
    # Read in the temp csv file
    df = pd.read_csv("temp.csv")
    compareplayers(df)

elif option == "Hole Breakdown":
    # Read in the temp csv file
    df = pd.read_csv("temp.csv")
    hole_breakdown(df)

elif option == "Overall Stats":
    # Read in the temp csv file
    df = pd.read_csv("temp.csv")
    overall_stats(df)

elif option == "Round Breakdown":
    # Read in the temp csv file
    df = pd.read_csv("temp.csv")
    round_breakdown(df)