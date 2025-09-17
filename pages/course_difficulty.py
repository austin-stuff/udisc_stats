import streamlit as st
import pandas as pd
import altair as alt
from udisc_stats import UdiscStats

def course_difficulty_analysis(df):
    """
    Analyzes and displays the difficulty of courses based on player performance.
    """
    st.title("⛳ Course Difficulty Analysis")

    if df is None:
        st.warning("Please upload a CSV file first!")
        return

    players = [p for p in df['PlayerName'].unique() if p != 'Par']
    if not players:
        st.error("No player data found in the uploaded file.")
        return

    selected_player = st.selectbox("Select a player to analyze", players)
    if not selected_player:
        return

    stats = UdiscStats(df)
    stats.filter_df_by_player([selected_player])
    player_data = stats.df

    if player_data.empty:
        st.error(f"No data available for {selected_player}.")
        return

    st.subheader(f"Course Difficulty for {selected_player}")

    course_stats = player_data.groupby(['CourseName', 'LayoutName']).agg(
        Rounds=('CourseName', 'size'),
        Avg_Score=('+/-', 'mean'),
        Best_Score=('+/-', 'min'),
        Worst_Score=('+/-', 'max')
    ).reset_index()

    # Add a number input to filter by minimum rounds played
    min_rounds = st.number_input(
        "Minimum rounds played to display course:",
        min_value=1,
        max_value=int(course_stats['Rounds'].max()),
        value=1,
        step=1
    )

    filtered_stats = course_stats[course_stats['Rounds'] >= min_rounds].copy()

    if filtered_stats.empty:
        st.info("No courses match the selected filter. Adjust the slider to see more courses.")
        return

    filtered_stats['Difficulty_Rating'] = filtered_stats['Avg_Score']
    # No longer need to sort and re-index for the chart
    # filtered_stats = filtered_stats.sort_values(by='Difficulty_Rating', ascending=False)
    # filtered_stats = filtered_stats.reset_index(drop=True)
    # filtered_stats.index += 1

    chart = alt.Chart(filtered_stats).mark_circle().encode(
        x=alt.X(
            'Avg_Score',
            title='Average Score (+/-)',
            scale=alt.Scale(domain=[filtered_stats['Avg_Score'].min() - 1, filtered_stats['Avg_Score'].max() + 1])
        ),
        y=alt.Y(
            'Best_Score',
            title='Best Score (+/-)',
            scale=alt.Scale(domain=[filtered_stats['Best_Score'].min() - 1, filtered_stats['Best_Score'].max() + 1])
        ),
        size=alt.Size(
            'Rounds',
            title='Rounds Played',
            scale=alt.Scale(range=[100, 1000])
        ),
        color=alt.Color('CourseName', title='Course'),
        tooltip=['CourseName', 'LayoutName', 'Rounds', 'Avg_Score', 'Best_Score', 'Worst_Score']
    ).properties(
        title='Course Difficulty Landscape'
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

if 'df' in st.session_state and st.session_state.df is not None:
    course_difficulty_analysis(st.session_state.df)
else:
    st.warning("⚠️ No data loaded. Please upload a CSV file from the Upload page first.")