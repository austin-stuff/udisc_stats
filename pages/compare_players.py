import streamlit as st
import numpy as np
from udisc_stats import UdiscStats
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Page configuration is handled in main.py

def compare_players(df):
    """Main function for comparing players across courses and layouts."""
    st.title("🏆 Compare Players")
    
    if df is None:
        st.warning("Please upload a CSV file first!")
        return
    
    selected_players = st.multiselect("Select players to compare", df['PlayerName'].unique())

    if not selected_players:
        st.info("Select one or more players to begin comparison.")
        return

    col1, col2, col3 = st.columns(3)
    
    # Initialize stats object
    stats = UdiscStats(df)
    
    if len(selected_players) == 1:
        # Single player analysis
        stats.filter_df_by_player(selected_players)
        course_names = stats.get_course_names()
        
        selected_course = col1.selectbox("Select a course", course_names)
        stats.filter_df_by_course(selected_course)
        
        layouts = stats.get_layouts(selected_course)
        layout = col2.radio("Choose a layout", layouts)
        stats.filter_df_by_layout(layout)
        
        pars = stats.get_pars_of_specific_course(selected_course, layout)
        par_total = pars["Total"]
        
        visualization = col3.radio("Visualization Type", 
                                 ["Average", "Last Round", "Best Per Hole", "Best Round"])
    else:
        # Multi-player analysis - find common courses and layouts
        stats.filter_df_by_player(selected_players)
        
        # Find common courses across all selected players
        common_courses = _find_common_courses(df, selected_players)
        
        if not len(common_courses):
            st.error("Selected players have no courses in common.")
            return
            
        selected_course = col1.selectbox("Select a course", common_courses)
        stats.filter_df_by_course(selected_course)
        
        # Find common layouts for the selected course
        common_layouts = _find_common_layouts(df, selected_players, selected_course)
        
        if not len(common_layouts):
            st.error("Selected players have no layouts in common for this course.")
            return
            
        layout = col2.radio("Choose a layout", common_layouts)
        stats.filter_df_by_layout(layout)
        
        pars = stats.get_pars_of_specific_course(selected_course, layout)
        par_total = pars["Total"]
        
        visualization = col3.radio("Visualization Type", 
                                 ["Average", "Last Round", "Best Per Hole", "Best Round"])

    # Create visualization
    _create_comparison_chart(stats, selected_players, selected_course, layout, 
                           par_total, visualization)


def _find_common_courses(df, players):
    """Find courses that all selected players have played."""
    player_courses = []
    for player in players:
        player_data = df[df['PlayerName'] == player]
        courses = player_data['CourseName'].unique()
        player_courses.append(set(courses))
    
    # Find intersection of all sets
    common_courses = set.intersection(*player_courses) if player_courses else set()
    
    # Order by frequency
    course_counts = df[df['CourseName'].isin(common_courses)]['CourseName'].value_counts()
    return course_counts.index.tolist()


def _find_common_layouts(df, players, course):
    """Find layouts that all selected players have played for a specific course."""
    player_layouts = []
    for player in players:
        player_data = df[(df['PlayerName'] == player) & (df['CourseName'] == course)]
        layouts = player_data['LayoutName'].unique()
        player_layouts.append(set(layouts))
    
    # Find intersection of all sets
    common_layouts = set.intersection(*player_layouts) if player_layouts else set()
    
    # Order by frequency
    layout_counts = df[
        (df['CourseName'] == course) & 
        (df['LayoutName'].isin(common_layouts))
    ]['LayoutName'].value_counts()
    
    return layout_counts.index.tolist()


def _create_comparison_chart(stats, selected_players, selected_course, layout, 
                           par_total, visualization):
    """Create and display the comparison chart."""
    st.subheader(f"📊 {selected_course}: {layout} (Par {par_total})")
    
    fig = go.Figure()
    
    for player in selected_players:
        # Create a fresh stats object for each player
        player_stats = UdiscStats(stats.raw_df)
        player_stats.filter_df_by_player([player])
        player_stats.filter_df_by_course(selected_course)
        player_stats.filter_df_by_layout(layout)
        
        if player_stats.df.empty:
            st.warning(f"No data found for {player}")
            continue
            
        holes = player_stats.get_holes_from_round()
        
        if not holes:
            st.warning(f"No hole data found for {player}")
            continue
            
        hole_numbers = [int(hole[4:]) for hole in holes]
        
        try:
            # Calculate scores based on visualization type
            if visualization == "Best Per Hole":
                scores = player_stats.get_best_score_per_hole().values.tolist()
                total_score = sum(scores)
                st.write(f"**{player}** - Theoretical Best: {total_score} ({total_score - par_total:+d})")
                
            elif visualization == "Average":
                scores = player_stats.get_average_score_per_hole()
                avg_total = player_stats.df["Total"].mean()
                st.write(f"**{player}** - Average: {avg_total:.1f} ({avg_total - par_total:+.1f})")
                
            elif visualization == "Last Round":
                scores = player_stats.get_last_round_scores()
                total_score = sum(scores)
                st.write(f"**{player}** - Last Round: {total_score} ({total_score - par_total:+d})")
                
            elif visualization == "Best Round":
                best_round = player_stats.get_best_round()
                best_score = int(best_round["Total"])
                scores = best_round[holes].values.tolist()
                st.write(f"**{player}** - Best Round: {best_score} ({best_score - par_total:+d})")
            
            # Add trace to plot
            fig.add_trace(
                go.Scatter(
                    x=hole_numbers, 
                    y=scores, 
                    name=player, 
                    mode='markers+lines', 
                    marker=dict(size=8),
                    line=dict(width=2),
                    hovertemplate=f'<b>{player}</b><br>Hole: %{{x}}<br>Score: %{{y}}<extra></extra>'
                )
            )
        except Exception as e:
            st.error(f"Error processing data for {player}: {str(e)}")
            continue

    # Update layout
    if fig.data:  # Only show chart if we have data
        fig.update_layout(
            title=f"{visualization} Scores: {selected_course} - {layout}",
            xaxis_title='Hole Number',
            yaxis_title='Score',
            xaxis=dict(
                tickmode='array',
                tickvals=hole_numbers if 'hole_numbers' in locals() else [],
                showgrid=True,
            ),
            yaxis=dict(showgrid=True),
            hovermode='x unified',
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available to display chart.")


# Check if data is available and run the app
if 'df' in st.session_state and st.session_state.df is not None:
    compare_players(st.session_state.df)
else:
    st.warning("⚠️ No data loaded. Please upload a CSV file from the Upload page first.")