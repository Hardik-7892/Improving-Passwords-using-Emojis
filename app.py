import streamlit as st
import hashlib
import time
import pandas as pd

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Authorize
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)
sheet = client.open("streamlit_logs").sheet1

EMOJIS = ["😀","😂","🔥","❤️","😎","👍","🎉","😢","🚀","🥶","🤖","👀","💀","🌙","⭐","🍕"]

# Encode password (text + emoji safe)
def encode_password(pw):
    encoded = ""
    for char in pw:
        encoded += format(ord(char), "02x")
    return encoded

# Hash password
def hash_password(encoded_pw):
    return hashlib.sha256(encoded_pw.encode()).hexdigest()

# Save logs
def save_log(data):
    headers = sheet.row_values(1)

    # Build row aligned with headers
    row = []
    for col in headers:
        row.append(data.get(col, ""))  # Fill missing fields with empty string

    sheet.append_row(row)

# App UI
st.title("Emoji + Text Password Study Prototype")

# --- Category selection (A/B/C) ---

if "category" not in st.session_state:
    st.session_state.category = None

category = st.selectbox(
    "Select your category",
    [
        "A - Text + Emoji",
        "B - Text + Hybrid",
        "C - Text + Emoji + Hybrid",
    ],
    index=0 if st.session_state.category is None else
           ["A - Text + Emoji", "B - Text + Hybrid", "C - Text + Emoji + Hybrid"].index(st.session_state.category),
)

st.session_state.category = category

cat_code = category.split(" ")[0]  # "A", "B", or "C"

st.info(f"You are in Category {cat_code}")

if cat_code == "A":
    allowed_pw_types = ["Text", "Emoji"]           # Text + Emoji only
elif cat_code == "B":
    allowed_pw_types = ["Text", "Hybrid"]          # Text + Hybrid only
else:  # "C"
    allowed_pw_types = ["Text", "Emoji", "Hybrid"] # All three

mode = st.radio("Select Mode", ["Create Password", "Login Test"])

# Initialize session state variables
if "creation_start_time" not in st.session_state:
    st.session_state.creation_start_time = None
if "login_start_time" not in st.session_state:
    st.session_state.login_start_time = None
if "password_input" not in st.session_state:
    st.session_state.password_input = ""
if "last_pw_type" not in st.session_state:
    st.session_state.last_pw_type = ""
if "reset_password" not in st.session_state:
    st.session_state.reset_password = False

if cat_code == "A":
    st.write("In this condition, you will create Text and Emoji passwords.")
elif cat_code == "B":
    st.write("In this condition, you will create Text and Hybrid passwords.")
else:
    st.write("In this condition, you will create Text, Emoji, and Hybrid passwords.")

if mode == "Create Password":
    st.subheader("Step 1 — Create Password")

    user_id = st.text_input("Participant ID")
    pw_type = st.selectbox("Password Type", allowed_pw_types, key="pw_type_" + mode)
    if st.session_state.creation_start_time is None:
        st.session_state.creation_start_time = time.time()

    # Reset flag
    if "reset_password" not in st.session_state:
        st.session_state.reset_password = False

    # Handle reset BEFORE widget renders
    if st.session_state.reset_password:
        st.session_state.password_input = ""
        st.session_state.reset_password = False

    # Initialize session state
    if "password_input" not in st.session_state:
        st.session_state.password_input = ""

    if "last_pw_type" not in st.session_state:
        st.session_state.last_pw_type = pw_type

    # Clear password if user switches mode
    if pw_type != st.session_state.last_pw_type:
        st.session_state.password_input = ""
        st.session_state.last_pw_type = pw_type
        st.rerun()
        start = time.time()

    # Emoji picker only for Emoji / Hybrid
    if pw_type in ["Emoji", "Hybrid"]:
        st.write("Click emojis to add to password:")

        cols = st.columns(8)
        for i, emoji in enumerate(EMOJIS):
            with cols[i % 8]:
                if st.button(emoji, key=f"emoji_{emoji}"):
                    st.session_state.password_input += emoji
                    st.rerun()
    
    # PASSWORD INPUT LOGIC BASED ON TYPE
    # Emoji-only mode -> read-only input
    if pw_type == "Emoji":
        st.text_input(
            "Password (Emoji only — typing disabled)",
            key="password_input",
            type="password",
            disabled=True
        )

    # Text / Hybrid mode -> typing allowed
    else:
        st.text_input(
            "Password (Type text or click emojis)",
            key="password_input",
            type="password"
        )

    # Clear button
    if st.button("Clear Password"):
        # st.session_state.password_input = ""
        st.session_state.reset_password = True
        st.rerun()

    # Save password
    if st.button("Save Password"):
        password = st.session_state.password_input

        if not user_id or not password:
            st.warning("Fill all fields")
        else:
            

            encoded = encode_password(password)
            hashed = hash_password(encoded)

            creation_time = time.time() - st.session_state.creation_start_time

            save_log({
                "user_id": user_id,
                "type": pw_type,
                "category": st.session_state.get("category", ""),
                "event": "created",
                "password_length": len(password),
                # "emoji_count": sum(1 for c in password if c in EMOJI_MAP),
                "emoji_count": sum(1 for c in password if c in EMOJIS),
                "creation_time": creation_time,
                "hash": hashed
            })
            st.session_state.creation_start_time = None
            st.success("Password Saved")

# Login Mode
if mode == "Login Test":
    st.subheader("Step 2 — Login")

    user_id = st.text_input("Participant ID")
    pw_type = st.selectbox("Password Type", allowed_pw_types, key="pw_type_" + mode)
    
    if st.session_state.login_start_time is None:
        st.session_state.login_start_time = time.time()

    if "reset_password" not in st.session_state:
        st.session_state.reset_password = False

    # Handle reset BEFORE widget renders
    if st.session_state.reset_password:
        st.session_state.password_input = ""
        st.session_state.reset_password = False

    # Initialize session state
    if "password_input" not in st.session_state:
        st.session_state.password_input = ""

    if "last_pw_type" not in st.session_state:
        st.session_state.last_pw_type = pw_type

    if pw_type != st.session_state.last_pw_type:
        st.session_state.password_input = ""
        st.session_state.last_pw_type = pw_type
        st.rerun()

    # Emoji picker only for Emoji / Hybrid
    if pw_type in ["Emoji", "Hybrid"]:
        st.write("Click emojis to add to password:")

        cols = st.columns(8)
        for i, emoji in enumerate(EMOJIS):
            with cols[i % 8]:
                if st.button(emoji, key=f"emoji_{emoji}"):
                    st.session_state.password_input += emoji
                    st.rerun()

    # PASSWORD INPUT LOGIC BASED ON TYPE
    # Emoji-only mode -> read-only input
    if pw_type == "Emoji":
        st.text_input(
            "Password (Emoji only — typing disabled)",
            key="password_input",
            type="password",
            disabled=True
        )

    # Text / Hybrid mode -> typing allowed
    else:
        st.text_input(
            "Password (Type text or click emojis)",
            key="password_input",
            type="password"
        )
    
    if st.button("Clear Password"):
        st.session_state.reset_password = True
        st.rerun()

    if st.button("Login"):
        password = st.session_state.password_input
        if not user_id or not password:
            st.warning("Fill all fields")
            st.stop()

        try:
            records = sheet.get_all_records()
            logs = pd.DataFrame(records)
            # logs = pd.read_csv(LOG_FILE)
            filtered = logs[
                (logs["user_id"].astype(str) == str(user_id)) &
                (logs["type"] == pw_type) &
                (logs["event"] == "created")
            ]
            record = filtered.iloc[-1] if not filtered.empty else None
        except:
            st.error("No password found")
            st.stop()

        encoded = encode_password(password)
        hashed = hash_password(encoded)

        login_time = time.time() - st.session_state.login_start_time

        success = (hashed == record["hash"])

        save_log({
            "user_id": user_id,
            "type": pw_type,
            "category": st.session_state.get("category", ""),
            "event": "login",
            "success": success,
            "login_time": login_time,
            "attempt_length": len(password)
        })
        st.session_state.login_start_time = None

        if success:
            st.success("Login Successful")
        else:
            st.error("Login Failed")

st.divider()
st.subheader("Researcher Controls")

if st.button("Download Logs"):
    try:
        records = sheet.get_all_records()
        logs = pd.DataFrame(records)
        # logs = pd.read_csv(LOG_FILE)
        csv = logs.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Click to Download logs.csv",
            data=csv,
            file_name="logs.csv",
            mime="text/csv"
        )
    except FileNotFoundError:
        st.warning("No logs found yet.")

