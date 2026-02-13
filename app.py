import streamlit as st
import hashlib
import time
import pandas as pd

# Emoji mapping table (expandable)
EMOJI_MAP = {
    "😀": "E001", "😂": "E002", "🔥": "E003",
    "❤️": "E004", "😎": "E005", "👍": "E006",
    "🎉": "E007", "😢": "E008", "🚀": "E009"
}

EMOJIS = ["😀","😂","🔥","❤️","😎","👍","🎉","😢","🚀","🥶","🤖","👀","💀","🌙","⭐","🍕"]

LOG_FILE = "logs.csv"

# Encode password (text + emoji safe)
def encode_password(pw):
    encoded = ""
    for char in pw:
        if char in EMOJI_MAP:
            encoded += EMOJI_MAP[char]
        else:
            encoded += format(ord(char), "02x")
    return encoded

# Hash password
def hash_password(encoded_pw):
    return hashlib.sha256(encoded_pw.encode()).hexdigest()

# Save logs
def save_log(data):
    df = pd.DataFrame([data])
    try:
        old = pd.read_csv(LOG_FILE)
        df = pd.concat([old, df])
    except:
        pass
    df.to_csv(LOG_FILE, index=False)

# App UI
st.title("Emoji + Text Password Study Prototype")
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

if mode == "Create Password":
    st.subheader("Step 1 — Create Password")

    user_id = st.text_input("Participant ID")
    pw_type = st.selectbox("Password Type", ["Text", "Emoji", "Hybrid"])
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
    pw_type = st.selectbox("Password Type", ["Text", "Emoji", "Hybrid"])
    
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
            logs = pd.read_csv(LOG_FILE)
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
