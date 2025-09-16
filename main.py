import streamlit as st
import pandas as pd
from io import StringIO
from db import (
    initialize_database,
    list_uploads,
    load_upload_df,
    save_upload,
)

# Configure the page
st.set_page_config(
    page_title="UDisc Stats App",
    page_icon="🥏",
    layout="wide",
    initial_sidebar_state="expanded"
)

def clean_udisc_data(df):
    """Clean and standardize UDisc CSV data."""
    # Remove rows with all zeros in score columns (incomplete rounds)
    df = df.loc[~(df.iloc[:, 3:] == 0).any(axis=1)]

    # Standardize course names
    course_name_mapping = {
        'Indian Riffle Park/Kettering': 'Indian Riffle Disc Golf Course',
        'Belmont Park': 'Belmont Park Disc Golf Course',
        'Karohl Park': 'Karohl Park Disc Golf Course'
    }
    df['CourseName'] = df['CourseName'].replace(course_name_mapping)

    # Standardize layout names
    layout_name_mapping = {
        '2018 Redesign': 'Main 18 Hole Layout',
        'Belmont': 'Short Tees with Long 16'
    }
    df['LayoutName'] = df['LayoutName'].replace(layout_name_mapping)
    
    return df

def display_upload_instructions():
    """Display instructions for exporting CSV from UDisc."""
    with st.expander("📱 How to Export CSV from UDisc", expanded=False):
        st.markdown("""
        ### Steps to export your scorecard data:
        1. Open the **UDisc app** on your mobile device
        2. Go to the **'More'** tab (bottom navigation)
        3. Tap on **'Scorecards'**
        4. Tap the **three lines** (☰) in the top right corner
        5. Select **'Export to CSV'**
        6. Share or save the CSV file to upload here
        """)

def display_saved_uploads():
    """Display and handle loading of previously saved uploads."""
    with st.expander("📂 Load Previously Saved Data", expanded=False):
        saved_uploads = list_uploads()
        
        if not saved_uploads:
            st.info("No saved uploads yet. Upload a CSV below to save it for future use.")
            return
        
        # Create readable labels for saved uploads
        option_labels = [
            f"ID {rec.id}: {rec.filename} ({rec.num_rows} rounds, {rec.uploaded_at[:10]})"
            for rec in saved_uploads
        ]
        
        selected_label = st.selectbox(
            "Choose a saved dataset:",
            option_labels,
            index=0,
            key="saved_upload_selector"
        )
        
        col1, col2 = st.columns([1, 3])
        
        if col1.button("📥 Load Dataset", type="primary"):
            selected_index = option_labels.index(selected_label)
            selected_record = saved_uploads[selected_index]
            
            try:
                df_loaded = load_upload_df(selected_record.id)
                st.session_state.df = df_loaded
                st.session_state.uploaded_file_name = selected_record.filename
                st.session_state.last_saved_upload_id = selected_record.id
                
                st.success(f"✅ Loaded '{selected_record.filename}' ({selected_record.num_rows} rounds)")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Failed to load dataset: {e}")

def handle_file_upload():
    """Handle CSV file upload and processing."""
    uploaded_file = st.file_uploader(
        "📁 Upload your UDisc CSV file",
        type=["csv"],
        help="Select the CSV file exported from your UDisc app"
    )
    
    if uploaded_file is None:
        return
    
    # Check if this is a new file or already loaded
    if (st.session_state.df is not None and 
        st.session_state.uploaded_file_name == uploaded_file.name):
        st.info(f"✅ File '{uploaded_file.name}' is already loaded.")
        return
    
    # Process the uploaded file
    try:
        with st.spinner("Processing CSV file..."):
            bytes_data = uploaded_file.getvalue()
            stringio = StringIO(bytes_data.decode('utf-8'))
            df = pd.read_csv(stringio)
            
            # Clean and standardize the data
            df = clean_udisc_data(df)
            
            # Store in session state
            st.session_state.df = df
            st.session_state.uploaded_file_name = uploaded_file.name
            
            # Save to database for future use
            try:
                record = save_upload(uploaded_file.name, bytes_data, df)
                st.session_state.last_saved_upload_id = record.id
                
                st.success(
                    f"✅ Successfully processed '{uploaded_file.name}'\n\n"
                    f"📊 **{record.num_rows}** rounds loaded\n\n"
                    f"💾 Saved as dataset ID {record.id}"
                )
                
            except Exception as e:
                st.warning(f"⚠️ File processed but couldn't save for later use: {e}")
                st.success(f"✅ Successfully processed '{uploaded_file.name}'")
    
    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
        st.error("Please ensure you've uploaded a valid UDisc CSV file.")
        
        # Clear potentially corrupted data
        st.session_state.df = None
        st.session_state.uploaded_file_name = None

def display_data_preview():
    """Display preview of currently loaded data."""
    if st.session_state.df is None:
        return
    
    st.subheader("📊 Data Preview")
    
    # Show summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    total_rounds = len(st.session_state.df)
    unique_players = len(st.session_state.df['PlayerName'].unique()) - 1  # Exclude 'Par'
    unique_courses = len(st.session_state.df['CourseName'].unique())
    date_range = f"{st.session_state.df['StartDate'].min()[:10]} to {st.session_state.df['StartDate'].max()[:10]}"
    
    col1.metric("Total Rounds", total_rounds)
    col2.metric("Players", unique_players)
    col3.metric("Courses", unique_courses)
    col4.metric("Date Range", date_range)
    
    # Show data preview
    st.dataframe(
        st.session_state.df.head(10),
        use_container_width=True,
        height=300
    )
    
    # Clear data button
    if st.button("🗑️ Clear Data", type="secondary"):
        st.session_state.df = None
        st.session_state.uploaded_file_name = None
        st.success("Data cleared successfully!")
        st.rerun()

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None
if 'last_saved_upload_id' not in st.session_state:
    st.session_state.last_saved_upload_id = None

# Initialize database
initialize_database()

st.title("🥏 UDisc Stats App")

# Show current data status
if st.session_state.df is not None:
    st.success(f"✅ **Current Dataset:** {st.session_state.uploaded_file_name}")
    col1, col2, col3, col4 = st.columns(4)
    
    total_rounds = len(st.session_state.df)
    unique_players = len(st.session_state.df['PlayerName'].unique()) - 1  # Exclude 'Par'
    unique_courses = len(st.session_state.df['CourseName'].unique())
    
    col1.metric("Total Rounds", total_rounds)
    col2.metric("Players", unique_players)
    col3.metric("Courses", unique_courses)
    col4.metric("Date Range", f"{st.session_state.df['StartDate'].min()[:10]} to {st.session_state.df['StartDate'].max()[:10]}")
    
    st.info("🎯 Use the sidebar to navigate to analysis pages, or upload a new file below to replace the current data.")

st.markdown("""
## Welcome to UDisc Stats!

This app provides enhanced data visualization for your UDisc scorecards. Since UDisc doesn't offer a public API, 
you'll need to manually export your scorecard data as CSV files from the UDisc mobile app.

### Available Analysis Pages:
- **🎯 Hole Breakdown**: Complete course analysis with player comparisons, heatmaps, and detailed hole statistics
- **👤 Player Statistics**: Comprehensive individual player analytics and trends
""")

# Display upload instructions
display_upload_instructions()

# Display saved uploads section
display_saved_uploads()

# Handle file upload
st.subheader("📤 Upload New File")
handle_file_upload()

# Display data preview if available
if st.session_state.df is not None:
    display_data_preview()
else:
    st.info("👆 Upload a CSV file to begin analyzing your disc golf data!")