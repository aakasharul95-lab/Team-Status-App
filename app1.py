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

if st.sidebar.button("Update Status"):
    row_index = df.index[df['Name'] == user_name][0]
    
    df.at[row_index, 'Status'] = status_main
    df.at[row_index, 'Reason/Comment'] = comment
    df.at[row_index, 'Last Updated'] = datetime.now(sweden_tz).strftime("%Y-%m-%d %H:%M")
    df.at[row_index, 'IsLongTerm'] = "Yes" if is_long_term else "No"
    
    conn.update(worksheet="Sheet1", data=df)
    st.sidebar.success("Updated! Refreshing...")
    st.rerun()

# --- SIDEBAR: MANAGER RESET (Backup) ---
st.sidebar.markdown("---")
st.sidebar.subheader("Manager Tools")
if st.sidebar.checkbox("Show Reset Button"):
    pwd = st.sidebar.text_input("Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        if st.sidebar.button("Force Reset Board"):
            for index, row in df.iterrows():
                if row['IsLongTerm'] != "Yes":
                    df.at[index, 'Status'] = '❓ Not Updated'
                    df.at[index, 'Reason/Comment'] = ''
                    df.at[index, 'Last Updated'] = ''
            conn.update(worksheet="Sheet1", data=df)
            st.success("Board Reset Manually.")
            st.rerun()

# --- MAIN DASHBOARD ---
# Title uses the correct variable 'today_str'
st.title(f"SPAE AD&E Availability on {today_str}")

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
    elif 'Vacation' in val_str:
        color = 'background-color: #ffe5d0; color: black'
    return color

# Hide technical columns
display_cols = ['Name', 'Status', 'Reason/Comment', 'Last Updated']
styled_df = df[display_cols].style.applymap(highlight_status, subset=['Status'])

st.dataframe(styled_df, use_container_width=True, height=600, hide_index=True)

if st.button("🔄 Refresh Board"):
    st.rerun()

# --- EASTER EGG: VERSION BUTTON ---
st.markdown("---")
col1, col2 = st.columns([8, 2])

with col2:
    # 1. Initialize the counter if it doesn't exist
    if 'egg_clicks' not in st.session_state:
        st.session_state['egg_clicks'] = 0

    # 2. Define the counting function
    def count_click():
        st.session_state['egg_clicks'] += 1

    # 3. The Button (Note: we use 'on_click' here for better performance)
    st.button("v1.01", on_click=count_click)

    # 4. The Trigger
    if st.session_state['egg_clicks'] >= 5:
        st.error("🚨 Göran is a traitor for leaving SPAE! 🚨")
        # Reset the counter automatically so you can do it again
        st.session_state['egg_clicks'] = 0







