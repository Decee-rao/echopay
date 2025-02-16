import streamlit as st
import sqlite3

# Set up Streamlit page
st.set_page_config(page_title="RFID Access System", page_icon="🔑", layout="centered")
st.title("🔑 RFID Access System")

# Database Path
DATABASE_PATH = "./Database.db"

# 🔍 Authenticate Customer from UserAuth table
def authenticate_customer(rfid, password):
    """Check if RFID and password match in UserAuth table."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT RFID FROM UserAuth WHERE RFID = ? AND Password = ?", (rfid, password))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None  # Return RFID if exists

# 🔍 Authenticate Admin (Fixed credentials: admin/admin)
def authenticate_admin(username, password):
    """Authenticate admin manually (since there's no admin table)."""
    return username == "admin" and password == "admin"

# 🔄 Role Selection
page = st.sidebar.radio("Select Role", ["Customer Login", "Admin Login"])

# 🎟️ Customer Login Section
if page == "Customer Login":
    st.subheader("🎟️ Customer Login")
    rfid = st.text_input("Enter RFID")
    password = st.text_input("Enter Password", type="password")

    if st.button("Login"):
        user_rfid = authenticate_customer(rfid, password)
        if user_rfid:
            st.session_state.authenticated_user = user_rfid  # Store RFID for session
            st.success(f"✅ Welcome, User with RFID {user_rfid}!")
            st.switch_page("pages/Customer_Dashboard.py")
        else:
            st.error("❌ Invalid RFID or Password.")

# 🛠️ Admin Login Section
elif page == "Admin Login":
    st.subheader("🛠️ Admin Login")
    username = st.text_input("Enter Admin Username")
    password = st.text_input("Enter Password", type="password")

    if st.button("Login"):
        if authenticate_admin(username, password):
            st.session_state.authenticated_admin = True
            st.success("✅ Admin Login Successful!")
            st.switch_page("pages/Admin_Dashboard.py")
        else:
            st.error("❌ Invalid Admin Credentials.")
