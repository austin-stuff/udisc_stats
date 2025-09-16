# 🥏 UDisc Stats App

A comprehensive Streamlit web application for analyzing and visualizing disc golf scorecards from UDisc.

## ✨ Features

- **📁 Data Upload & Management**: Upload UDisc CSV files with automatic data cleaning and persistent storage
- **🏆 Player Comparison**: Compare performance across multiple players with interactive charts
- **🎯 Hole Analysis**: Detailed breakdown of performance on individual holes
- **👤 Player Statistics**: Comprehensive individual player analytics and trends
- **💾 Data Persistence**: SQLite database for storing and reloading datasets

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- UDisc mobile app (for exporting scorecard data)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd udisc_stats
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run main.py
```

### Exporting Data from UDisc

Since UDisc doesn't provide a public API, you'll need to manually export your scorecard data:

1. Open the UDisc app on your mobile device
2. Go to the **'More'** tab
3. Tap on **'Scorecards'**
4. Tap the three lines (☰) in the top right corner
5. Select **'Export to CSV'**
6. Upload the CSV file to the app

## 📊 App Structure

### Main Page (Home)
- Upload and process UDisc CSV files
- Automatic data cleaning and standardization
- Load previously saved datasets
- Data preview and validation
- Quick overview of loaded data

### Analysis Pages

#### 1. Compare Players
- Multi-player performance comparison
- Course and layout filtering
- Multiple visualization types (Average, Last Round, Best Per Hole, Best Round)
- Interactive Plotly charts

#### 2. Hole Breakdown
- Individual hole performance analysis
- Score distribution (aces, eagles, birdies, pars, bogeys)
- Birdie percentages and averages
- Grouped bar charts for detailed breakdowns

#### 3. Player Statistics
- Comprehensive individual player analytics
- Overall performance metrics
- Course-specific performance analysis
- Performance trends over time

## 🛠️ Technical Details

### Architecture
- **Frontend**: Streamlit with Plotly for interactive visualizations
- **Backend**: Pandas for data processing, SQLite for persistence
- **Data Storage**: Parquet files for efficient storage, CSV for reference
- **Session Management**: Streamlit session state for multi-page navigation

### Data Processing
- Automatic removal of incomplete rounds
- Course and layout name standardization
- Relative-to-par score calculations
- SHA-256 based deduplication

### Code Structure
```
├── main.py                 # Main entry point with data upload functionality
├── udisc_stats.py         # Core data processing class
├── db.py                  # Database operations
├── pages/
│   ├── compare_players.py # Player comparison analysis
│   ├── hole_breakdown.py  # Individual hole analysis
│   └── player_stats.py    # Individual player statistics
├── data/                  # SQLite database and uploaded files
└── requirements.txt       # Python dependencies
```

## 🎯 Key Improvements Made

- **Code Consolidation**: Removed duplicate functions and consolidated into a single `UdiscStats` class
- **Enhanced UI**: Added emojis, better layouts, and improved user experience
- **Error Handling**: Comprehensive error handling and user feedback
- **Performance**: Optimized data processing and filtering
- **Documentation**: Added comprehensive docstrings and type hints
- **New Features**: Added individual player statistics page with trend analysis

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the [MIT License](LICENSE).