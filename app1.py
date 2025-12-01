import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "st-gsheets-connection"])
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
ADMIN_PASSWORD = "admin" 
sweden_tz = pytz.timezone('Europe/Stockholm')

st.set_page_config(page_title="SPAE AD&E Availability", layout="wide")

# --- CONNECT TO GOOGLE SHEET ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Read the data directly from the Google Sheet
# ttl=0 means "don't cache", fetch fresh data every time we reload
try:
    df = conn.read(worksheet="Sheet1", ttl=0)
    # Ensure columns exist to prevent errors if sheet is empty
    expected_cols = ['Name', 'Status', 'Reason/Comment', 'Last Updated']
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ''
    # Fill NaN values with empty strings for clean display
    df = df.fillna('')
except Exception as e:
    st.error("Could not connect to Google Sheet. Check Secrets.")
    st.stop()

# List of team members comes directly from the Sheet now
TEAM_MEMBERS = df['Name'].tolist()

# --- SIDEBAR: UPDATE STATUS ---
st.sidebar.header("📝 Update Your Status")
user_name = st.sidebar.selectbox("Who are you?", TEAM_MEMBERS)

status_main = st.sidebar.radio(
    "Where are you today?", 
    ["🏢 Office", "🏠 WFH", "🤒 Sick/Away", "🛠️ Workshop"]
)

comment = st.sidebar.text_input("Reason / Comment (Optional)", placeholder="e.g. Waiting for delivery")

if st.sidebar.button("Update Status"):
    # 1. Find the row index for the selected user
    # We look inside the dataframe we just pulled from Google
    row_index = df.index[df['Name'] == user_name][0]
    
    # 2. Update the data in memory
    df.at[row_index, 'Status'] = status_main
    df.at[row_index, 'Reason/Comment'] = comment
    df.at[row_index, 'Last Updated'] = datetime.now(sweden_tz).strftime("%H:%M")
    
    # 3. Push the update back to Google Sheets
    conn.update(worksheet="Sheet1", data=df)
    st.sidebar.success("Updated! Refreshing...")
    st.rerun()

# --- SIDEBAR: MANAGER RESET ---
st.sidebar.markdown("---")
st.sidebar.subheader("Manager Tools")
if st.sidebar.checkbox("Show Reset Button"):
    pwd = st.sidebar.text_input("Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        if st.sidebar.button("🗑️ Reset Board for New Day"):
            # Reset columns in the dataframe
            df['Status'] = '❓ Not Updated'
            df['Reason/Comment'] = ''
            df['Last Updated'] = ''
            
            # Push clean data to Google Sheets
            conn.update(worksheet="Sheet1", data=df)
            st.rerun()

# --- MAIN DASHBOARD ---
today_date = datetime.now(sweden_tz).strftime('%Y-%m-%d')
st.title(f"SPAE AD&E Availability on {today_date}")

# Styling
def highlight_status(val):
    color = ''
    val_str = str(val)
    if 'WFH' in val_str:
        color = 'background-color: #d1e7dd; color: black'
    elif 'Sick' in val_str:
        color = 'background-color: #f8d7da; color: black'
    elif 'Office' in val_str:
        color = 'background-color: #cff4fc; color: black'
    elif 'Workshop' in val_str:
        color = 'background-color: #fff3cd; color: black'
    return color

# Display the table from the dataframe
styled_df = df.style.applymap(highlight_status, subset=['Status'])

st.dataframe(styled_df, use_container_width=True, height=600, hide_index=True)

if st.button("🔄 Refresh Board"):
    st.rerun()


