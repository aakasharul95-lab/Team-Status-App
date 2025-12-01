import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
# Password to clear the board at the end of the day
ADMIN_PASSWORD = "admin" 

# The list of people from your screenshot
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

# --- PAGE SETUP ---
st.set_page_config(page_title="Team Status Board", layout="wide")

# --- INITIALIZE DATA ---
# This creates a blank table if one doesn't exist yet
if 'team_data' not in st.session_state:
    # Create a default dataframe
    default_data = {
        'Name': TEAM_MEMBERS,
        'Status': ['❓ Not Updated'] * len(TEAM_MEMBERS),
        'Location': ['Unknown'] * len(TEAM_MEMBERS),
        'Reason/Comment': [''] * len(TEAM_MEMBERS),
        'Last Updated': [''] * len(TEAM_MEMBERS)
    }
    st.session_state['team_data'] = pd.DataFrame(default_data)

# --- SIDEBAR: UPDATE STATUS ---
st.sidebar.header("📝 Update Your Status")
user_name = st.sidebar.selectbox("Who are you?", TEAM_MEMBERS)

# Status Options
status_main = st.sidebar.radio(
    "Where are you today?", 
    ["🏢 Office", "🏠 WFH", "🤒 Sick/Away", "Workshop"]
)

# Optional Comment
comment = st.sidebar.text_input("Reason / Comment (Optional)", placeholder="e.g. Waiting for delivery / Mild fever")

if st.sidebar.button("Update Status"):
    # 1. Get the current table
    df = st.session_state['team_data']
    
    # 2. Find the row for the selected user
    index = df.index[df['Name'] == user_name][0]
    
    # 3. Update the values
    df.at[index, 'Status'] = status_main
    df.at[index, 'Reason/Comment'] = comment
    df.at[index, 'Last Updated'] = datetime.now().strftime("%H:%M")
    
    # 4. Save back to session state
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
st.title("📍 Team Availability Board")
st.markdown(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

# Display the Dataframe with styling
df_display = st.session_state['team_data']

# Define a function to color the rows based on status
def highlight_status(val):
    color = ''
    if 'WFH' in str(val):
        color = 'background-color: #d1e7dd; color: black' # Greenish
    elif 'Sick' in str(val):
        color = 'background-color: #f8d7da; color: black' # Reddish
    elif 'Office' in str(val):
        color = 'background-color: #cff4fc; color: black' # Blueish
    return color

# Apply the styling
styled_df = df_display.style.applymap(highlight_status, subset=['Status'])

# Show the table
st.dataframe(
    styled_df, 
    use_container_width=True, 
    height=600,
    hide_index=True
)

# Add a refresh button just in case
if st.button("🔄 Refresh Board"):
    st.rerun()