import streamlit as st
import numpy as np
from udisc_stats import UdiscStats
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


# Page configuration is handled in main.py

def hole_breakdown(df):
    """Analyze performance on individual holes with detailed score breakdowns."""
    st.title("🎯 Complete Course Breakdown")
    
    if df is None:
        st.warning("Please upload a CSV file first!")
        return
    
    selected_players = st.multiselect("Select players to analyze", df['PlayerName'].unique())

    if not selected_players:
        st.info("Select one or more players to begin analysis.")
        return

    col1, col2 = st.columns(2)
    
    # Initialize stats object
    stats = UdiscStats(df)
    stats.filter_df_by_player(selected_players)
    
    if len(selected_players) > 1:
        # Multi-player analysis - find common courses and layouts
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
    else:
        # Single player analysis
        course_names = stats.get_course_names()
        selected_course = col1.selectbox("Select a course", course_names)
        stats.filter_df_by_course(selected_course)
        
        layouts = stats.get_layouts(selected_course)
        layout = col2.radio("Choose a layout", layouts)
    
    stats.filter_df_by_layout(layout)
    
    # Get holes and pars
    holes = stats.get_holes_from_round()
    
    if not holes:
        st.error("No hole data found for the selected course and layout.")
        return
    
    try:
        pars = stats.get_pars_of_specific_course(selected_course, layout)
    except (ValueError, KeyError) as e:
        st.error(f"Error getting par data: {str(e)}")
        return
    
    # Create comprehensive course analysis
    _create_complete_course_analysis(stats, selected_players, selected_course, layout, holes, pars)


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



def _create_complete_course_analysis(stats, selected_players, selected_course, layout, holes, pars):
    """Create comprehensive analysis showing all holes at once."""
    st.subheader(f"📍 {selected_course} - {layout}")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Course Overview", "🔥 Performance Heatmap", "📊 Detailed Stats", "🎯 Individual Holes"])
    
    with tab1:
        _create_course_overview_grid(stats, selected_players, selected_course, layout, holes, pars)
    
    with tab2:
        _create_performance_heatmap(stats, selected_players, selected_course, layout, holes, pars)
    
    with tab3:
        _create_detailed_stats_table(stats, selected_players, selected_course, layout, holes, pars)
    
    with tab4:
        _create_individual_hole_cards(stats, selected_players, selected_course, layout, holes, pars)


def _create_course_overview_grid(stats, selected_players, selected_course, layout, holes, pars):
    """Create a grid overview of all holes with key metrics."""
    st.subheader("🗺️ Course Overview - All Holes at a Glance")
    

    
    # Calculate metrics for all holes
    hole_data = []
    
    for i, hole in enumerate(holes, 1):
        hole_name = f'Hole{i}'
        par = int(pars[hole_name]) if hole_name in pars else 3
        hole_stats = {
            'hole': i,
            'par': par,
            'players': {}
        }
        
        for player in selected_players:
            player_stats = UdiscStats(stats.raw_df)
            player_stats.filter_df_by_player([player])
            player_stats.filter_df_by_course(selected_course)
            player_stats.filter_df_by_layout(layout)
            
            if not player_stats.df.empty and hole_name in player_stats.df.columns:
                hole_scores = player_stats.df[hole_name].dropna()
                if len(hole_scores) > 0:
                    avg_score = hole_scores.mean()
                    under_par_pct = (len(hole_scores[hole_scores < par]) / len(hole_scores)) * 100
                    hole_stats['players'][player] = {
                        'avg': avg_score,
                        'under_par_pct': under_par_pct,
                        'rounds': len(hole_scores)
                    }
        
        hole_data.append(hole_stats)
    
    # Create grid layout
    cols_per_row = 6
    rows = [hole_data[i:i + cols_per_row] for i in range(0, len(hole_data), cols_per_row)]
    
    for row in rows:
        cols = st.columns(len(row))
        for col, hole_info in zip(cols, row):
            with col:
                _create_hole_card(hole_info)


def _create_hole_card(hole_info):
    """Create a compact card for a single hole."""
    hole_num = hole_info['hole']
    par = hole_info['par']
    
    # Determine card color based on average performance
    if hole_info['players']:
        avg_scores = [p['avg'] for p in hole_info['players'].values()]
        avg_relative = np.mean(avg_scores) - par
        
        if avg_relative < -0.5:
            card_color = "#d4edda"  # Green - easy hole
        elif avg_relative > 0.5:
            card_color = "#f8d7da"  # Red - difficult hole
        else:
            card_color = "#fff3cd"  # Yellow - average hole
    else:
        card_color = "#f8f9fa"  # Gray - no data
    

    
    st.markdown(f"""
    <div style="
        background-color: {card_color};
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        text-align: center;
        margin-bottom: 10px;
    ">
        <h4 style="margin: 0; color: #333;">Hole {hole_num}</h4>
        <p style="margin: 5px 0; font-weight: bold; color: #333;">Par {par}</p>
    """, unsafe_allow_html=True)
    
    for player, stats in hole_info['players'].items():
        avg_score = stats['avg']
        relative_score = avg_score - par
        under_par_pct = stats['under_par_pct']
        
        color = "#28a745" if relative_score < 0 else "#dc3545" if relative_score > 0 else "#6c757d"
        
        st.markdown(f"""
        <div style="font-size: 12px; margin: 2px 0;">
            <strong>{player}:</strong><br>
            <span style="color: {color};">{avg_score:.2f} ({relative_score:+.2f})</span><br>
            <span style="color: #666;">{under_par_pct:.0f}% under par</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


def _create_performance_heatmap(stats, selected_players, selected_course, layout, holes, pars):
    """Create a heatmap showing performance across all holes."""
    st.subheader("🔥 Performance Heatmap")
    st.write("Darker colors indicate better performance (lower scores relative to par)")
    
    # Prepare data for heatmap
    heatmap_data = []
    hole_numbers = []
    
    for i, hole in enumerate(holes, 1):
        hole_name = f'Hole{i}'
        par = int(pars[hole_name]) if hole_name in pars else 3
        hole_numbers.append(f"Hole {i}\n(Par {par})")
        
        row_data = []
        for player in selected_players:
            player_stats = UdiscStats(stats.raw_df)
            player_stats.filter_df_by_player([player])
            player_stats.filter_df_by_course(selected_course)
            player_stats.filter_df_by_layout(layout)
            
            if not player_stats.df.empty and hole_name in player_stats.df.columns:
                hole_scores = player_stats.df[hole_name].dropna()
                if len(hole_scores) > 0:
                    avg_score = hole_scores.mean()
                    relative_score = avg_score - par
                    row_data.append(relative_score)
                else:
                    row_data.append(None)
            else:
                row_data.append(None)
        
        heatmap_data.append(row_data)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=selected_players,
        y=hole_numbers,
        colorscale='RdYlGn_r',  # Red for bad, Green for good
        zmid=0,  # Center at par
        colorbar=dict(title="Score vs Par"),
        hoverongaps=False,
        hovertemplate='<b>%{y}</b><br><b>%{x}</b><br>Score vs Par: %{z:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Performance Heatmap - All Holes",
        xaxis_title="Players",
        yaxis_title="Holes",
        height=max(400, len(holes) * 25),
        yaxis=dict(autorange='reversed')  # Hole 1 at top
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _create_detailed_stats_table(stats, selected_players, selected_course, layout, holes, pars):
    """Create a detailed statistics table for all holes."""
    st.subheader("📊 Detailed Statistics Table")
    
    # Prepare data for table
    table_data = []
    
    for i, hole in enumerate(holes, 1):
        hole_name = f'Hole{i}'
        par = int(pars[hole_name]) if hole_name in pars else 3
        
        row = {'Hole': i, 'Par': par}
        
        for player in selected_players:
            player_stats = UdiscStats(stats.raw_df)
            player_stats.filter_df_by_player([player])
            player_stats.filter_df_by_course(selected_course)
            player_stats.filter_df_by_layout(layout)
            
            if not player_stats.df.empty and hole_name in player_stats.df.columns:
                hole_scores = player_stats.df[hole_name].dropna()
                if len(hole_scores) > 0:
                    avg_score = hole_scores.mean()
                    under_par_count = len(hole_scores[hole_scores < par])
                    under_par_pct = (under_par_count / len(hole_scores)) * 100
                    best_score = hole_scores.min()
                    
                    row[f'{player}_Avg'] = f"{avg_score:.2f}"
                    row[f'{player}_Best'] = int(best_score)
                    row[f'{player}_Under%'] = f"{under_par_pct:.0f}%"
                else:
                    row[f'{player}_Avg'] = "N/A"
                    row[f'{player}_Best'] = "N/A"
                    row[f'{player}_Under%'] = "N/A"
            else:
                row[f'{player}_Avg'] = "N/A"
                row[f'{player}_Best'] = "N/A"
                row[f'{player}_Under%'] = "N/A"
        
        table_data.append(row)
    
    df_table = pd.DataFrame(table_data)
    
    # Style the dataframe
    st.dataframe(
        df_table,
        use_container_width=True,
        height=min(600, len(holes) * 35 + 100)
    )


def _create_individual_hole_cards(stats, selected_players, selected_course, layout, holes, pars):
    """Create expandable cards for each hole with detailed breakdown."""
    st.subheader("🎯 Individual Hole Analysis")
    st.write("Click on any hole to see detailed score breakdown")
    
    for i, hole in enumerate(holes, 1):
        hole_name = f'Hole{i}'
        par = int(pars[hole_name]) if hole_name in pars else 3
        
        with st.expander(f"🏌️ Hole {i} (Par {par})", expanded=False):
            _create_single_hole_analysis(stats, selected_players, selected_course, layout, i, par, pars)


def _create_single_hole_analysis(stats, selected_players, selected_course, layout, hole_number, par, pars):
    """Create detailed analysis for a single hole."""
    # Initialize score breakdown dataframe
    scores_df = pd.DataFrame(columns=['Player', 'Aces', 'Eagles', 'Birdies', 'Pars', 'Bogeys', 'DoubleBogeysOrWorse'])
    
    # Collect statistics for each player
    player_stats_summary = []
    
    for player in selected_players:
        # Create fresh stats object for each player
        player_stats = UdiscStats(stats.raw_df)
        player_stats.filter_df_by_player([player])
        player_stats.filter_df_by_course(selected_course)
        player_stats.filter_df_by_layout(layout)
        
        if player_stats.df.empty:
            continue
        
        # Get scores for the selected hole
        hole_name = f'Hole{hole_number}'
        if hole_name not in player_stats.df.columns:
            continue
            
        hole_scores = player_stats.df[hole_name].dropna()
        
        if len(hole_scores) == 0:
            continue
            
        # Calculate statistics
        avg_score = hole_scores.mean()
        under_par_count = len(hole_scores[hole_scores < par])
        birdie_pct = (under_par_count / len(hole_scores)) * 100
        
        player_stats_summary.append({
            'player': player,
            'avg': avg_score,
            'birdie_pct': birdie_pct,
            'rounds': len(hole_scores)
        })
        
        # Add to score breakdown
        scores_df = player_stats.append_scores_to_df(scores_df, player_stats.df, pars, hole_number)
    
    # Display summary statistics
    if player_stats_summary:
        cols = st.columns(len(player_stats_summary))
        for col, stat in zip(cols, player_stats_summary):
            col.metric(
                f"{stat['player']}",
                f"{stat['avg']:.2f} avg",
                f"{stat['birdie_pct']:.0f}% under par"
            )
    
    # Create score breakdown chart
    if not scores_df.empty:
        _create_mini_score_chart(scores_df, hole_number, par)


def _create_mini_score_chart(scores_df, hole_number, par):
    """Create a compact score breakdown chart."""
    # Define colors for different score types
    colors = ['#FFD700', '#32CD32', '#90EE90', '#808080', '#FF6347', '#8B0000']
    
    fig = go.Figure()
    
    # Add bars for each score type
    score_types = ['Aces', 'Eagles', 'Birdies', 'Pars', 'Bogeys', 'DoubleBogeysOrWorse']
    display_names = ['Aces', 'Eagles', 'Birdies', 'Pars', 'Bogeys', 'Double+']
    
    for i, (score_type, display_name, color) in enumerate(zip(score_types, display_names, colors)):
        fig.add_trace(
            go.Bar(
                x=scores_df['Player'],
                y=scores_df[score_type],
                name=display_name,
                marker_color=color,
                text=scores_df[score_type],
                textposition='outside'
            )
        )
    
    fig.update_layout(
        title=f"Score Distribution - Hole {hole_number} (Par {par})",
        xaxis_title='Player',
        yaxis_title='Count',
        barmode='group',
        height=300,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)


# Check if data is available and run the app
if 'df' in st.session_state and st.session_state.df is not None:
    hole_breakdown(st.session_state.df)
else:
    st.warning("⚠️ No data loaded. Please upload a CSV file from the Upload page first.")