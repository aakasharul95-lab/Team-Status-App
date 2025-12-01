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

try:
    df = conn.read(worksheet="Sheet1", ttl=0)
    # Added 'LastReset' to expected columns
    expected_cols = ['Name', 'Status', 'Reason/Comment', 'Last Updated', 'IsLongTerm', 'LastReset']
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ''
    df = df.fillna('')
except Exception as e:
    st.error("Could not connect to Google Sheet. Check Secrets.")
    st.stop()

TEAM_MEMBERS = df['Name'].tolist()

# --- 🤖 AUTOMATIC RESET LOGIC ---
current_sweden_time = datetime.now(sweden_tz)
today_str = current_sweden_time.strftime('%Y-%m-%d')

# Get the last reset date from the first row (Cell F2)
# We convert to string to match the format
last_reset_recorded = str(df.at[0, 'LastReset'])

# CHECK: Is it after 4 AM? AND Did we already reset today?
if current_sweden_time.hour >= 4 and last_reset_recorded != today_str:
    
    # Perform the Reset
    changes_made = False
    for index, row in df.iterrows():
        # Skip Long-Term / Vacation
        if row['IsLongTerm'] != "Yes":
            if row['Status'] != '❓ Not Updated':
                df.at[index, 'Status'] = '❓ Not Updated'
                df.at[index, 'Reason/Comment'] = ''
                df.at[index, 'Last Updated'] = ''
                changes_made = True
    
    # Mark that we have reset for today
    df.at[0, 'LastReset'] = today_str
    
    # Save to Google Sheet
    conn.update(worksheet="Sheet1", data=df)
    
    # Show a message and reload
    st.toast("🌅 Good Morning! Board automatically reset for the day.")
    st.rerun()

# --- SIDEBAR: UPDATE STATUS ---
st.sidebar.header("📝 Update Your Status")
user_name = st.sidebar.selectbox("Who are you?", TEAM_MEMBERS)

status_main = st.sidebar.radio(
    "Where are you today?", 
    ["🏢 Office", "🏠 WFH", "🤒 Sick/Away", "🛠️ Workshop", "🏖️ Vacation"]
)

comment = st.sidebar.text_input("Reason / Comment", placeholder="e.g. Back on Monday")

# CHECKBOX
is_long_term = st.sidebar.checkbox("🔒 Long-term (Protect from Reset)")

if st.sidebar




