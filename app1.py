import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import time
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
ADMIN_PASSWORD = "admin" 
sweden_tz = pytz.timezone('Europe/Stockholm')

st.set_page_config(page_title="Team Availability Board", layout="wide")

# --- CONNECT TO GOOGLE SHEET (WITH RETRY) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data_with_retry():
    max_retries = 3
    for i in range(max_retries):
        try:
            df = conn.read(worksheet="Sheet1", ttl=0)
            return df
        except Exception as e:
            if i < max_retries - 1:
                time.sleep(1)
            else:
                st.error("Google Sheets is busy. Please refresh the page.")
                st.stop()

df = load_data_with_retry()

# --- CLEAN DATA & REMOVE EMPTY ROWS ---
try:
    expected_cols = ['Name', 'Status', 'Reason/Comment', 'Last Updated', 'IsLongTerm', 'LastReset', 'Team']
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ''
    
    # Fill empty cells to avoid errors
    df = df.fillna('')
    
    # FIX 1: Filter out rows where Name is empty (Removes the blank lines)
    df = df[df['Name'].str.strip() != '']

except Exception as e:
    st.error("Data structure error. Check Google Sheet columns.")
    st.stop()

# --- 🤖 AUTOMATIC RESET LOGIC ---
current_sweden_time = datetime.now(sweden_tz)
today_str = current_sweden_time.strftime('%Y-%m-%d')

# Handle case where sheet is empty or LastReset column is missing data
if not df.empty:
    last_reset_recorded = str(df.at[df.index[0], 'LastReset'])
else:
    last_reset_recorded = ""

if current_sweden_time.hour >= 4 and last_reset_recorded != today_str and not df.empty:
    for index, row in df.iterrows():
        if row['IsLongTerm'] != "Yes":
            if row['Status'] != '❓ Not Updated':
                df.at[index, 'Status'] = '❓ Not Updated'
                df.at[index, 'Reason/Comment'] = ''
                df.at[index, 'Last Updated'] = ''
    
    # Update the reset date in the first row
    if not df.empty:
        df.at[df.index[0], 'LastReset'] = today_str
        
    conn.update(worksheet="Sheet1", data=df)
    st.toast("🌅 Good Morning! Board automatically reset.")
    st.rerun()

# --- SIDEBAR: TEAM SELECTION ---
st.sidebar.header("👥 Select Team")

all_teams = [t for t in df['Team'].unique() if t != '']
if not all_teams:
    all_teams = ["No Teams Found"]

selected_team = st.sidebar.selectbox("View Board For:", all_teams)

# Filter data for the selected team
team_df = df[df['Team'] == selected_team]
team_members = team_df['Name'].tolist()

# --- SIDEBAR: UPDATE STATUS ---
st.sidebar.markdown("---")
st.sidebar.header("📝 Update Your Status")

# If team is empty, show a warning instead of crashing
if not team_members:
    st.sidebar.warning("No members found in this team.")
else:
    user_name = st.sidebar.selectbox("Who are you?", team_members)

    status_main = st.sidebar.radio(
        "Where are you today?", 
        ["🏢 Office", "🏠 WFH", "🤒 Sick/Away", "🛠️ Workshop", "🏖️ Vacation"]
    )

    comment = st.sidebar.text_input("Reason / Comment", placeholder="e.g. Back on Monday")
    is_long_term = st.sidebar.checkbox("🔒 Long-term (Protect from Reset)")

    if st.sidebar.button("Update Status"):
        # Find row in main dataframe
        row_index = df.index[df['Name'] == user_name][0]
        
        df.at[row_index, 'Status'] = status_main
        df.at[row_index, 'Reason/Comment'] = comment
        df.at[row_index, 'Last Updated'] = datetime.now(sweden_tz).strftime("%Y-%m-%d %H:%M")
        df.at[row_index, 'IsLongTerm'] = "Yes" if is_long_term else "No"
        
        if df.at[row_index, 'Team'] == '':
            df.at[row_index, 'Team'] = selected_team

        conn.update(worksheet="Sheet1", data=df)
        st.sidebar.success("Updated! Refreshing...")
        st.rerun()

# --- SIDEBAR: MANAGER RESET ---
st.sidebar.markdown("---")
st.sidebar.subheader("Manager Tools")
if st.sidebar.checkbox("Show Reset Button"):
    pwd = st.sidebar.text_input("Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        if st.sidebar.button(f"Reset {selected_team} Board"):
            for index, row in df.iterrows():
                # Only reset members of the selected team who are NOT long-term
                if row['Team'] == selected_team and row['IsLongTerm'] != "Yes":
                    df.at[index, 'Status'] = '❓ Not Updated'
                    df.at[index, 'Reason/Comment'] = ''
                    df.at[index, 'Last Updated'] = ''
            conn.update(worksheet="Sheet1", data=df)
            st.success(f"Reset complete for {selected_team}!")
            st.rerun()

# --- MAIN DASHBOARD ---
# FIX 2: Added the date back to the main title
st.title(f"{selected_team} Availability on {today_str}")

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

# Show the table
if not team_df.empty:
    display_cols = ['Name', 'Status', 'Reason/Comment', 'Last Updated']
    styled_df = team_df[display_cols].style.applymap(highlight_status, subset=['Status'])
    st.dataframe(styled_df, use_container_width=True, height=600, hide_index=True)
else:
    st.info("No members in this team yet.")

if st.button("🔄 Refresh Board"):
    st.rerun()

# --- EASTER EGG: VERSION BUTTON ---
st.markdown("---")
col1, col2 = st.columns([8, 2])

with col2:
    if 'egg_clicks' not in st.session_state:
        st.session_state['egg_clicks'] = 0

    def count_click():
        st.session_state['egg_clicks'] += 1

    st.button("v1.01", on_click=count_click)

    if st.session_state['egg_clicks'] >= 5:
        st.error("🚨 Göran is a traitor for leaving SPAE! 🚨")
        st.session_state['egg_clicks'] = 0








