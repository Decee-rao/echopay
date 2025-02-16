import streamlit as st
import sqlite3
import pandas as pd

# Database Path
DATABASE_PATH = "./Database.db"

# 🔒 Check Admin Authentication
if "authenticated_admin" not in st.session_state or not st.session_state.authenticated_admin:
    st.error("❌ Access Denied. Please log in as an Admin.")
    st.stop()

# 🏠 Admin Dashboard Title
st.title("🛠️ Admin Dashboard - RFID Transactions")

# 🔓 Logout button
if st.button("Logout"):
    del st.session_state.authenticated_admin
    st.switch_page("app.py")

# 📡 Fetch RFID List (UIDs) from `rfid_data`
def get_rfid_list():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT UID FROM rfid_data")
    rfids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return rfids

rfid_list = get_rfid_list()

# 🔄 Select RFID Dropdown
selected_rfid = st.selectbox("Select a UID:", rfid_list)

# 🔍 Search UID Manually
search_rfid = st.text_input("Or Search UID:")
if search_rfid and search_rfid in rfid_list:
    selected_rfid = search_rfid

# 📜 Fetch Transactions for the selected UID
def get_transactions(uid):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Fetch rows where UID matches the selected RFID
    cursor.execute("SELECT UID, ESP_ID FROM rfid_data WHERE UID = ?", (uid,))
    transactions = cursor.fetchall()
    
    conn.close()
    return transactions

# 🔘 Fetch Transactions on button click
if st.button("Get Transactions"):
    if selected_rfid:
        transactions = get_transactions(selected_rfid)

        if transactions:
            st.write(f"### Transactions for UID: {selected_rfid}")
            df = pd.DataFrame(transactions, columns=["ESP ID", "RFID"])  # Adjust column names
            st.dataframe(df)  # Display transactions in a table
        else:
            st.info("No transactions found for this UID.")
    else:
        st.warning("Please select or enter a valid UID.")
