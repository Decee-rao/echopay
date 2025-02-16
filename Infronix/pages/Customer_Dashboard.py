import streamlit as st
import sqlite3

# Database Path
DATABASE_PATH = "./Database.db"

# 🔒 Check Customer Authentication
if "authenticated_user" not in st.session_state:
    st.error("❌ Access Denied. Please log in as a Customer.")
    st.stop()

rfid = st.session_state.authenticated_user

st.title("🎟️ Customer Dashboard")

# 🔓 Logout Button
if st.button("Logout"):
    del st.session_state.authenticated_user
    st.switch_page("app.py")

# 📡 Fetch UID & ESP_ID from `rfid_data`
def get_rfid_details(rfid):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT UID, ESP_ID, Timestamp FROM rfid_data WHERE UID = ?", (rfid,))
    rfid_data = cursor.fetchone()
    conn.close()
    return rfid_data

rfid_data = get_rfid_details(rfid)

if rfid_data:
    uid, esp_id, timestamp = rfid_data

    # 📡 Fetch Customer Balance from `RFIDTable`
    def get_balance(uid):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT Balance FROM RFIDTable WHERE RFID = ?", (uid,))
        balance = cursor.fetchone()
        conn.close()
        return balance[0] if balance else 0

    balance = get_balance(uid)

    st.success("✅ Login Successful!")

    # Display RFID Details
    st.markdown(f"""
        <div style="text-align: center; padding: 20px; background-color: black; color: white; border-radius: 10px;">
            <h3>🎟️ UID: {uid}</h3>
            <p><b>🔄 Linked ESP ID:</b> {esp_id} </p>
            <p><b>🕒 Timestamp:</b> {timestamp} </p>
            <p><b>💰 Balance:</b> {balance} </p>
        </div>
    """, unsafe_allow_html=True)

    # 📜 Fetch Transaction History from `ESPNumber`
    def get_transactions(uid):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT ESPID, TransactionAmt FROM ESPNumber WHERE RFID = ?", (uid,))
        transactions = cursor.fetchall()
        conn.close()
        return transactions

    transactions = get_transactions(uid)
    
    st.subheader("📜 Transaction History")
    if transactions:
        for esp_id, amount in transactions:
            st.write(f"🔹 **ESP ID:** {esp_id} | **Amount:** {amount}")
    else:
        st.warning("No transactions found.")

else:
    st.error("RFID details not found.")
