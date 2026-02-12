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
            start = time.time()

            encoded = encode_password(password)
            hashed = hash_password(encoded)

            creation_time = time.time() - start

            save_log({
                "user_id": user_id,
                "type": pw_type,
                "event": "created",
                "password_length": len(password),
                "emoji_count": sum(1 for c in password if c in EMOJI_MAP),
                "creation_time": creation_time,
                "hash": hashed
            })

            st.success("Password Saved")

# Login Mode
if mode == "Login Test":
    st.subheader("Step 2 — Login")

    user_id = st.text_input("Participant ID")
    pw_type = st.selectbox("Password Type", ["Text", "Emoji", "Hybrid"])

    password = st.text_input("Enter password", type="password")

    # # adding emoji
    # st.write("Click emojis to add to password:")

    # if "password_input" not in st.session_state:
    #     st.session_state.password_input = ""

    # cols = st.columns(8)
    # for i, emoji in enumerate(EMOJIS):
    #     with cols[i % 8]:
    #         if st.button(emoji):
    #             st.session_state.password_input += emoji

    password = st.text_input(
        "Password", 
        value=st.session_state.password_input,
        type="password"
    )

    if st.button("Login"):
        try:
            logs = pd.read_csv(LOG_FILE)
            record = logs[(logs["user_id"] == user_id) & (logs["type"] == pw_type) & (logs["event"] == "created")].iloc[-1]
        except:
            st.error("No password found")
            st.stop()

        start = time.time()

        encoded = encode_password(password)
        hashed = hash_password(encoded)

        login_time = time.time() - start
        success = (hashed == record["hash"])

        save_log({
            "user_id": user_id,
            "type": pw_type,
            "event": "login",
            "success": success,
            "login_time": login_time,
            "attempt_length": len(password)
        })

        if success:
            st.success("Login Successful")
        else:
            st.error("Login Failed")
