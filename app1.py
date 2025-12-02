import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import time
from streamlit_gsheets import GSheetsConnection
import numpy as np

# --- CONFIGURATION ---
ADMIN_PASSWORD = "admin" 
sweden_tz = pytz.timezone('Europe/Stockholm')

st.set_page_config(page_title="Team Availability Board", layout="wide")

# --- CONNECT TO GOOGLE SHEET ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data_with_retry():
    max_retries = 3
    for i in range(max_retries):
        try:
            # FIX 2: We use ttl=0 here so updates are instant when we force a reload
            df = conn.read(worksheet="Sheet1", ttl=0)
            return df
        except Exception as e:
            if i < max_retries - 1:
                time.sleep(1)
            else:
                st.error("Google Sheets is busy. Please wait a moment and refresh.")
                st.stop()

df = load_data_with_retry()

# --- DATA CLEANING ---
try:
    expected_cols = ['Name', 'Status', 'Reason/Comment', 'Last Updated', 'IsLongTerm', 'LastReset', 'Team']
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ''
    
    df = df.fillna('')
    df['Name'] = df['Name'].astype(str).str.strip()
    df['Name'] = df['Name'].replace(['', 'nan', 'None'], np.nan)
    df = df.dropna(subset=['Name'])

except Exception as e:
    st.error(f"Data structure error: {e}")
    st.stop()

# --- 🤖 AUTOMATIC RESET LOGIC ---
current_sweden_time = datetime.now(sweden_tz)
today_str = current_sweden_time.strftime('%Y-%m-%d')

if not df.empty:
    first_index = df.index[0]
    last_reset_recorded = str(df.at[first_index, 'LastReset'])
else:
    last_reset_recorded = ""

is_past_cutoff = (current_sweden_time.hour > 16) or (current_sweden_time.hour == 16 and current_sweden_time.minute >= 30)

if is_past_cutoff and last_reset_recorded != today_str and not df.empty:
    for index, row in df.iterrows():
        if row['IsLongTerm'] != "Yes":
            if row['Status'] != '❓ Not Updated':
                df.at[index, 'Status'] = '❓ Not Updated'
                df.at[index, 'Reason/Comment'] = ''
                df.at[index, 'Last Updated'] = ''
    
    if not df.empty:
        df.at[df.index[0], 'LastReset'] = today_str
        
    conn.update(worksheet="Sheet1", data=df)
    st.cache_data.clear() # Clear cache to ensure fresh data
    st.toast("🧹 End of Day: Board automatically reset (16:30+)")
    st.rerun()

# --- SIDEBAR: TEAM SELECTION ---
st.sidebar.header("👥 Select Team")

all_teams = [t for t in df['Team'].unique() if str(t).strip() != '' and str(t) != 'nan']
if not all_teams:
    all_teams = ["No Teams Found"]

# Helper function to prevent reset on selection change
if 'selected_team_idx' not in st.session_state:
    st.session_state.selected_team_idx = 0

def update_team_idx():
    st.session_state.selected_team_idx = all_teams.index(st.session_state.team_select)

selected_team = st.sidebar.selectbox(
    "View Board For:", 
    all_teams, 
    key='team_select',
    on_change=update_team_idx
)

team_df = df[df['Team'] == selected_team]
team_members = team_df['Name'].tolist()

# --- SIDEBAR: UPDATE STATUS ---
st.sidebar.markdown("---")
st.sidebar.header("📝 Update Your Status")

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
        row_index = df.index[df['Name'] == user_name][0]
        
        df.at[row_index, 'Status'] = status_main
        df.at[row_index, 'Reason/Comment'] = comment
        df.at[row_index, 'Last Updated'] = datetime.now(sweden_tz).strftime("%Y-%m-%d %H:%M")
        df.at[row_index, 'IsLongTerm'] = "Yes" if is_long_term else "No"
        
        if df.at[row_index, 'Team'] == '':
            df.at[row_index, 'Team'] = selected_team

        # FIX 2: Clear cache immediately before rerun
        conn.update(worksheet="Sheet1", data=df)
        st.cache_data.clear() 
        st.sidebar.success("Updated!")
        time.sleep(0.5) # Slight pause to let Google process
        st.rerun()

# --- SIDEBAR: MANAGER RESET ---
st.sidebar.markdown("---")
st.sidebar.subheader("Manager Tools")
if st.sidebar.checkbox("Show Reset Button"):
    pwd = st.sidebar.text_input("Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        if st.sidebar.button(f"Reset {selected_team} Board"):
            for index, row in df.iterrows():
                if row['Team'] == selected_team and row['IsLongTerm'] != "Yes":
                    df.at[index, 'Status'] = '❓ Not Updated'
                    df.at[index, 'Reason/Comment'] = ''
                    df.at[index, 'Last Updated'] = ''
            conn.update(worksheet="Sheet1", data=df)
            st.cache_data.clear()
            st.success(f"Reset complete for {selected_team}!")
            time.sleep(0.5)
            st.rerun()

# --- MAIN DASHBOARD ---
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

if not team_df.empty:
    display_cols = ['Name', 'Status', 'Reason/Comment', 'Last Updated']
    styled_df = team_df[display_cols].style.applymap(highlight_status, subset=['Status'])
    
    val_height = (len(team_df) + 1) * 35 + 3
    st.dataframe(
        styled_df, 
        use_container_width=True, 
        hide_index=True,
        height=val_height
    )
else:
    st.info("No members in this team yet.")

if st.button("🔄 Refresh Board"):
    st.rerun()

# --- EASTER EGG (FIXED JUMPING) ---
# FIX 1: Using an empty container at the bottom keeps layout stable
bottom_container = st.container()
with bottom_container:
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










