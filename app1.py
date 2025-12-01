import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
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
st.set_page_config(page_title="SPAE AD&E Availability", layout="wide")

# --- INITIALIZE DATA ---
if 'team_data' not in st.session_state:
    default_data = {
        'Name': TEAM_MEMBERS,
        'Status': ['❓ Not Updated'] * len(TEAM_MEMBERS),
        # Location column removed here
        'Reason/Comment': [''] * len(TEAM_MEMBERS),
        'Last Updated': [''] * len(TEAM_MEMBERS)
    }
    st.session_state['team_data'] = pd.DataFrame(default_data)

# --- SIDEBAR: UPDATE STATUS ---
st.sidebar.header("📝 Update Your Status")
user_name = st.sidebar.selectbox("Who are you?", TEAM_MEMBERS)

# Status Options (Added Symbol to Workshop)
status_main = st.sidebar.radio(
    "Where are you today?", 
    ["🏢 Office", "🏠 WFH", "🤒 Sick/Away", "🛠️ Workshop"]
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
            # Reset columns to default
            st.session_state['team_data']['Status'] = '❓ Not Updated'
            st.session_state['team_data']['Reason/Comment'] = ''
            st.session_state['team_data']['Last Updated'] = ''
            st.rerun()

# --- MAIN DASHBOARD ---
# Title updated to include Todays Date dynamically
today_date = datetime.now().strftime('%Y-%m-%d')
st.title(f"SPAE AD&E Availability on {today_date}")

# Display the Dataframe
df_display = st.session_state['team_data']

# Define coloring logic
def highlight_status(val):
    color = ''
    val_str = str(val)
    if 'WFH' in val_str:
        color = 'background-color: #d1e7dd; color: black' # Greenish
    elif 'Sick' in val_str:
        color = 'background-color: #f8d7da; color: black' # Reddish
    elif 'Office' in val_str:
        color = 'background-color: #cff4fc; color: black' # Blueish
    elif 'Workshop' in val_str:
        color = 'background-color: #fff3cd; color: black' # Yellowish for Workshop
    return color

# Apply styling
styled_df = df_display.style.applymap(highlight_status, subset=['Status'])

# Show the table
st.dataframe(
    styled_df, 
    use_container_width=True, 
    height=600,
    hide_index=True
)

# Refresh button
if st.button("🔄 Refresh Board"):
    st.rerun()
