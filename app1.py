import streamlit as st
import pandas as pd
from datetime import datetime
import pytz # New library for timezones

# --- CONFIGURATION ---
ADMIN_PASSWORD = "admin" 

# SET TIMEZONE TO SWEDEN
sweden_tz = pytz.timezone('Europe/Stockholm')

TEAM_MEMBERS = [
    "Niclas Axelsson (Manager)",
    "Anna Penalosa",
    "Jukka Kvarnström",
    "Aakash Arul",
    "Tony Nilsson",
    "Niklas Brikell",
    "Ting Ma",
    "Niclas Larsson",
    "Kjell-Ove Johannesson",
    "Kenny Leandersson",
    "Tobias Persson",
    "Angelo Dárro",
    "Viktor Borgström",
    "Jozsef Kovacs",
    "Kemal Veispahic",
    "Lennart Olausson"
]

st.set_page_config(page_title="SPAE AD&E Availability", layout="wide")

# --- INITIALIZE DATA ---
if 'team_data' not in st.session_state:
    default_data = {
        'Name': TEAM_MEMBERS,
        'Status': ['❓ Not Updated'] * len(TEAM_MEMBERS),
        'Reason/Comment': [''] * len(TEAM_MEMBERS),
        'Last Updated': [''] * len(TEAM_MEMBERS)
    }
    st.session_state['team_data'] = pd.DataFrame(default_data)

# --- SIDEBAR: UPDATE STATUS ---
st.sidebar.header("📝 Update Your Status")
user_name = st.sidebar.selectbox("Who are you?", TEAM_MEMBERS)

status_main = st.sidebar.radio(
    "Where are you today?", 
    ["🏢 Office", "🏠 WFH", "🤒 Sick/Away", "🛠️ Workshop"]
)

comment = st.sidebar.text_input("Reason / Comment (Optional)", placeholder="e.g. Waiting for delivery")

if st.sidebar.button("Update Status"):
    df = st.session_state['team_data']
    index = df.index[df['Name'] == user_name][0]
    
    df.at[index, 'Status'] = status_main
    df.at[index, 'Reason/Comment'] = comment
    # FIX: Use Sweden time for the timestamp
    df.at[index, 'Last Updated'] = datetime.now(sweden_tz).strftime("%H:%M")
    
    st.session_state['team_data'] = df
    st.sidebar.success("Updated!")

# --- SIDEBAR: MANAGER RESET ---
st.sidebar.markdown("---")
st.sidebar.subheader("Manager Tools")
if st.sidebar.checkbox("Show Reset Button"):
    pwd = st.sidebar.text_input("Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        if st.sidebar.button("🗑️ Reset Board for New Day"):
            st.session_state['team_data']['Status'] = '❓ Not Updated'
            st.session_state['team_data']['Reason/Comment'] = ''
            st.session_state['team_data']['Last Updated'] = ''
            st.rerun()

# --- MAIN DASHBOARD ---
# FIX: Use Sweden time for the Date Title
today_date = datetime.now(sweden_tz).strftime('%Y-%m-%d')
st.title(f"SPAE AD&E Availability on {today_date}")

df_display = st.session_state['team_data']

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

styled_df = df_display.style.applymap(highlight_status, subset=['Status'])

st.dataframe(styled_df, use_container_width=True, height=600, hide_index=True)

if st.button("🔄 Refresh Board"):
    st.rerun()
