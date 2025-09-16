import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from udisc_stats import UdiscStats

# Page configuration is handled in main.py

def player_stats(df):
    """Display comprehensive statistics for individual players."""
    st.title("👤 Player Statistics")
    
    if df is None:
        st.warning("Please upload a CSV file first!")
        return
    
    # Get players (excluding Par)
    players = [p for p in df['PlayerName'].unique() if p != 'Par']
    
    if not players:
        st.error("No player data found in the uploaded file.")
        return
    
    selected_player = st.selectbox("Select a player", players)
    
    if not selected_player:
        return
    
    # Create stats object for the selected player
    stats = UdiscStats(df)
    stats.filter_df_by_player([selected_player])
    
    if stats.df.empty:
        st.error(f"No data found for {selected_player}")
        return
    
    # Display overall statistics
    _display_overall_stats(stats, selected_player)
    
    # Display course-specific analysis
    _display_course_analysis(stats, selected_player)
    
    # Display performance trends
    _display_performance_trends(stats, selected_player)


def _display_overall_stats(stats, player_name):
    """Display overall player statistics."""
    st.subheader(f"📊 Overall Statistics for {player_name}")
    
    player_data = stats.df
    
    # Calculate key metrics
    total_rounds = len(player_data)
    avg_score_relative = player_data['+/-'].mean()
    avg_rating = player_data['RoundRating'].mean()
    best_round = int(player_data['+/-'].min())
    worst_round = int(player_data['+/-'].max())
    
    # Display metrics in columns
    # Use a more responsive layout for metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Rounds", total_rounds)
        st.metric("Best Round", f"{best_round:+d}")
    with col2:
        st.metric("Average Score", f"{avg_score_relative:+.1f}")
        st.metric("Worst Round", f"{worst_round:+d}")
    
    # Center the average rating
    st.metric("Average Rating", f"{avg_rating:.0f}")
    
    # Best and worst round details
    st.subheader("🏆 Best & Worst Rounds")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🥇 Best Round:**")
        best_round_data = player_data[player_data['+/-'] == best_round].iloc[0]
        st.write(f"**Course:** {best_round_data['CourseName']}")
        st.write(f"**Layout:** {best_round_data['LayoutName']}")
        st.write(f"**Score:** {int(best_round_data['+/-']):+d}")
        st.write(f"**Rating:** {best_round_data['RoundRating']:.0f}")
        st.write(f"**Date:** {best_round_data['StartDate'][:10]}")
    
    with col2:
        st.write("**🥴 Worst Round:**")
        worst_round_data = player_data[player_data['+/-'] == worst_round].iloc[0]
        st.write(f"**Course:** {worst_round_data['CourseName']}")
        st.write(f"**Layout:** {worst_round_data['LayoutName']}")
        st.write(f"**Score:** {int(worst_round_data['+/-']):+d}")
        st.write(f"**Rating:** {worst_round_data['RoundRating']:.0f}")
        st.write(f"**Date:** {worst_round_data['StartDate'][:10]}")


def _display_course_analysis(stats, player_name):
    """Display course-specific performance analysis."""
    st.subheader("🏌️ Course Performance")
    
    player_data = stats.df
    
    if player_data.empty:
        st.warning("No data available for course analysis.")
        return
    
    # Course performance summary
    course_stats = player_data.groupby('CourseName').agg({
        '+/-': ['count', 'mean', 'min'],
        'RoundRating': 'mean'
    }).round(2)
    
    course_stats.columns = ['Rounds Played', 'Avg Score', 'Best Score', 'Avg Rating']
    course_stats = course_stats.sort_values('Rounds Played', ascending=False)
    
    st.dataframe(course_stats, use_container_width=True)
    
    # Course performance chart
    if len(course_stats) > 1:
        # Clean the data for plotting - remove NaN values and ensure positive sizes
        plot_data = course_stats.copy()
        plot_data = plot_data.dropna()  # Remove rows with NaN values
        
        if len(plot_data) > 1:
            # Ensure size values are positive (add offset if needed)
            size_values = plot_data['Avg Rating']
            if size_values.min() <= 0:
                size_values = size_values - size_values.min() + 1
            
            fig = px.scatter(
                plot_data,
                x='Rounds Played',
                y='Avg Score',
                size=size_values,
                hover_name=plot_data.index,
                title=f"{player_name} - Course Performance Overview",
                labels={
                    'Rounds Played': 'Rounds Played',
                    'Avg Score': 'Average Score (relative to par)',
                    'Avg Rating': 'Average Rating'
                },
                custom_data=['Best Score', 'Avg Rating']
            )
            
            fig.update_traces(
                hovertemplate="<b>%{hovertext}</b><br><br>" +
                              "Rounds Played: %{x}<br>" +
                              "Average Score: %{y:+.2f}<br>" +
                              "Best Score: %{customdata[0]:+d}<br>" +
                              "Average Rating: %{customdata[1]:.0f}<extra></extra>"
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data points to create a meaningful scatter plot.")


def _display_performance_trends(stats, player_name):
    """Display performance trends over time."""
    st.subheader("📈 Performance Trends")
    
    player_data = stats.df.copy()
    
    if player_data.empty:
        st.warning("No data available for trend analysis.")
        return
    
    try:
        # Convert date and sort
        player_data['Date'] = pd.to_datetime(player_data['StartDate'])
        player_data = player_data.sort_values('Date')
    except Exception as e:
        st.error(f"Error processing date data: {str(e)}")
        return
    
    # Calculate rolling averages
    player_data['Rolling_Avg_Score'] = player_data['+/-'].rolling(window=5, min_periods=1).mean()
    player_data['Rolling_Avg_Rating'] = player_data['RoundRating'].rolling(window=5, min_periods=1).mean()
    
    # Create trend charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Score trend
        fig_score = go.Figure()
        
        fig_score.add_trace(go.Scatter(
            x=player_data['Date'],
            y=player_data['+/-'],
            mode='markers',
            name='Individual Rounds',
            marker=dict(size=6, opacity=0.6),
            hovertemplate='<b>%{customdata[0]}</b><br>' +
                          'Layout: %{customdata[1]}<br>' +
                          'Score: %{y:+d}<br>' +
                          'Rating: %{customdata[2]:.0f}<br>' +
                          'Date: %{x|%Y-%m-%d}<extra></extra>',
            customdata=player_data[['CourseName', 'LayoutName', 'RoundRating']]
        ))
        
        fig_score.add_trace(go.Scatter(
            x=player_data['Date'],
            y=player_data['Rolling_Avg_Score'],
            mode='lines',
            name='5-Round Average',
            line=dict(width=3, color='red')
        ))
        
        fig_score.update_layout(
            title="Score Trend Over Time",
            xaxis_title="Date",
            yaxis_title="Score (relative to par)",
            height=400
        )
        
        st.plotly_chart(fig_score, use_container_width=True)
    
    with col2:
        # Rating trend
        fig_rating = go.Figure()
        
        fig_rating.add_trace(go.Scatter(
            x=player_data['Date'],
            y=player_data['RoundRating'],
            mode='markers',
            name='Individual Rounds',
            marker=dict(size=6, opacity=0.6),
            hovertemplate='<b>%{customdata[0]}</b><br>' +
                          'Layout: %{customdata[1]}<br>' +
                          'Score: %{customdata[2]:+d}<br>' +
                          'Rating: %{y:.0f}<br>' +
                          'Date: %{x|%Y-%m-%d}<extra></extra>',
            customdata=player_data[['CourseName', 'LayoutName', '+/-']]
        ))
        
        fig_rating.add_trace(go.Scatter(
            x=player_data['Date'],
            y=player_data['Rolling_Avg_Rating'],
            mode='lines',
            name='5-Round Average',
            line=dict(width=3, color='blue')
        ))
        
        fig_rating.update_layout(
            title="Rating Trend Over Time",
            xaxis_title="Date",
            yaxis_title="Round Rating",
            height=400
        )
        
        st.plotly_chart(fig_rating, use_container_width=True)


# Check if data is available and run the app
if 'df' in st.session_state and st.session_state.df is not None:
    player_stats(st.session_state.df)
else:
    st.warning("⚠️ No data loaded. Please upload a CSV file from the Upload page first.")