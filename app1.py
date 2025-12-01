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
    # Ensure all columns exist
    expected_cols = ['Name', 'Status', 'Reason/Comment', 'Last Updated', 'IsLongTerm']
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ''
    df = df.fillna('')
except Exception as e:
    st.error("Could not connect to Google Sheet. Check Secrets.")
    st.stop()

TEAM_MEMBERS = df['Name'].tolist()

# --- SIDEBAR: UPDATE STATUS ---
st.sidebar.header("📝 Update Your Status")
user_name = st.sidebar.selectbox("Who are you?", TEAM_MEMBERS)

status_main = st.sidebar.radio(
    "Where are you today?", 
    ["🏢 Office", "🏠 WFH", "🤒 Sick/Away", "🛠️ Workshop"]
)

comment = st.sidebar.text_input("Reason / Comment", placeholder="e.g. Vacation until Monday")

# --- THE LONG TERM CHECKBOX ---
# If you check this, the Manager's reset button CANNOT touch your status.
is_long_term = st.sidebar.checkbox("🔒 Long-term (Protect from Daily Reset)")

if st.sidebar.button("Update Status"):
    row_index = df.index[df['Name'] == user_name][0]
    
    # Update the data
    df.at[row_index, 'Status'] = status_main
    df.at[row_index, 'Reason/Comment'] = comment
    df.at[row_index, 'Last Updated'] = datetime.now(sweden_tz).strftime("%Y-%m-%d %H:%M")
    
    # LOGIC: If checked, save "Yes". If unchecked, save "No".
    # Saving "No" is how you 'delete' the long-term status when you get back.
    df.at[row_index, 'IsLongTerm'] = "Yes" if is_long_term else "No"
    
    conn.update(worksheet="Sheet1", data=df)
    st.sidebar.success("Updated! Refreshing...")
    st.rerun()

# --- SIDEBAR: MANAGER RESET ---
st.sidebar.markdown("---")
st.sidebar.subheader("Manager Tools")
if st.sidebar.checkbox("Show Reset Button"):
    pwd = st.sidebar.text_input("Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        if st.sidebar.button("🗑️ Reset Board (Respects Long-term)"):
            
            # --- MANAGER LOGIC ---
            # We loop through every person.
            for index, row in df.iterrows():
                # We ONLY reset them if they did NOT check the Long-term box.
                if row['IsLongTerm'] != "Yes":
                    df.at[index, 'Status'] = '❓ Not Updated'
                    df.at[index, 'Reason/Comment'] = ''
                    df.at[index, 'Last Updated'] = ''
            
            conn.update(worksheet="Sheet1", data=df)
            st.success("Board Reset! (Long-term entries were protected)")
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

# We hide the 'IsLongTerm' column so the table looks clean
display_cols = ['Name', 'Status', 'Reason/Comment', 'Last Updated']
styled_df = df[display_cols].style.applymap(highlight_status, subset=['Status'])

st.dataframe(styled_df, use_container_width=True, height=600, hide_index=True)

if st.button("🔄 Refresh Board"):
    st.rerun()



