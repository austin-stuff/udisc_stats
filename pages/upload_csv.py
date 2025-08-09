# pages/1_Upload_CSV.py

import streamlit as st
import pandas as pd
from io import StringIO
from db import (
    initialize_database,
    list_uploads,
    load_upload_df,
    save_upload,
)

def upload_CSV():
    uploaded_file = st.file_uploader("To find your CSV file... Open the UDisc app, go to the 'More' tab, click on 'Scorecards', click the three lines in the top right corner, and then click 'Export to CSV'!", type=["csv"])

    return uploaded_file

st.set_page_config(layout="wide") # Or set globally in Home.py

st.title("Upload Your UDisc CSV File")

# Initialize session state for the DataFrame if it doesn't exist
# These session state variables are GLOBAL across all pages of this single Streamlit app
if 'df' not in st.session_state:
    st.session_state.df = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None
if 'last_saved_upload_id' not in st.session_state:
    st.session_state.last_saved_upload_id = None

# Ensure the on-disk database and folders exist
initialize_database()

# Section to load a previously saved upload
with st.expander("Load previously saved upload", expanded=False):
    saved_uploads = list_uploads()
    if not saved_uploads:
        st.info("No saved uploads yet. Upload a CSV below to save it for future use.")
    else:
        option_labels = [
            f"{rec.id} — {rec.filename} — {rec.num_rows}x{rec.num_cols} — {rec.uploaded_at}"
            for rec in saved_uploads
        ]
        selected_label = st.selectbox(
            "Choose a saved dataset",
            option_labels,
            index=0 if option_labels else None,
        )
        if st.button("Load selected dataset") and selected_label:
            # Map label back to record
            selected_index = option_labels.index(selected_label)
            selected_record = saved_uploads[selected_index]
            try:
                df_loaded = load_upload_df(selected_record.id)
                st.session_state.df = df_loaded
                st.session_state.uploaded_file_name = selected_record.filename
                st.session_state.last_saved_upload_id = selected_record.id
                st.success(
                    f"Loaded saved dataset '{selected_record.filename}' (id {selected_record.id}). "
                    "You can navigate to other sections using the sidebar."
                )
            except Exception as e:
                st.error(f"Failed to load saved dataset: {e}")

if 'df' in st.session_state and st.session_state.df is not None:
    st.info(f"You already have a DataFrame loaded '{st.session_state.uploaded_file_name}'. You can navigate to other sections, or upload a new file to replace it.")

uploaded_file = upload_CSV() # Call the function from functions.py

if uploaded_file is not None:
    # Only process if a new file is uploaded AND it's a new upload or the session state is empty
    if st.session_state.df is None or st.session_state.uploaded_file_name != uploaded_file.name:
        try:
            bytes_data = uploaded_file.getvalue()
            stringio = StringIO(bytes_data.decode('utf-8'))
            df = pd.read_csv(stringio)

            # --- Data Cleaning/Preprocessing (apply once per upload) ---
            df = df.loc[~(df.iloc[:, 3:] == 0).any(axis=1)]

            df['CourseName'] = df['CourseName'].replace(['Indian Riffle Park/Kettering'], 'Indian Riffle Disc Golf Course')
            df['CourseName'] = df['CourseName'].replace(['Belmont Park'], 'Belmont Park Disc Golf Course')
            df['CourseName'] = df['CourseName'].replace(['Karohl Park'], 'Karohl Park Disc Golf Course')

            df['LayoutName'] = df['LayoutName'].replace(['2018 Redesign'], 'Main 18 Hole Layout')
            df['LayoutName'] = df['LayoutName'].replace(['Belmont'], 'Short Tees with Long 16')
            # Add back other layout renames if needed

            # Store the cleaned DataFrame and the uploaded file's name in session state
            st.session_state.df = df
            st.session_state.uploaded_file_name = uploaded_file.name # Store name to detect new upload
            # Persist the upload for future use (deduped by file content)
            try:
                record = save_upload(uploaded_file.name, bytes_data, df)
                st.session_state.last_saved_upload_id = record.id
                st.info(
                    f"Saved dataset to local database as id {record.id} "
                    f"({record.num_rows} rows × {record.num_cols} cols)."
                )
            except Exception as e:
                st.warning(f"Uploaded file processed but could not be saved for later use: {e}")
            st.success(f"CSV file '{uploaded_file.name}' uploaded and processed successfully! "
                       "You can now navigate to other sections using the sidebar.")

        except Exception as e:
            st.error(f"Error processing file: {e}. Please ensure it's a valid UDisc CSV.")
            st.session_state.df = None # Clear potentially corrupted data
            st.session_state.uploaded_file_name = None # Clear file name

    else:
        st.info(f"File '{uploaded_file.name}' is already loaded. You can navigate to other sections.")

    # Display preview of current data (whether newly uploaded or already in session)
    if st.session_state.df is not None:
        st.subheader("Current Data Preview:")
        st.dataframe(st.session_state.df.head())
        # Optional: Add a button to clear the current session's data
        if st.button("Clear Uploaded Data"):
            if 'df' in st.session_state:
                del st.session_state.df
            if 'uploaded_file_name' in st.session_state:
                del st.session_state.uploaded_file_name
            st.info("Data cleared. Please upload a new file.")
            st.rerun() # Force a rerun to update the UI
else:
    st.info("Please upload your UDisc CSV file to begin analysis.")