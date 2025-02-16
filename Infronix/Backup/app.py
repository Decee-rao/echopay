import streamlit as st
import sqlite3

# ---------- Authentication Functions ----------
def authenticate_customer(rfid, password, db_path="./Database.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT Password FROM UserAuth WHERE RFID = ?", (rfid,))
    user = cursor.fetchone()
    conn.close()
    return user and user[0] == password

def authenticate_admin(username, password):
    return username == "admin" and password == "admin"  # ✅ Fixed authentication

# ---------- Fetch Data from Database ----------
def get_rfid_details(rfid, db_path="./Database.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT Balance, ESPID FROM RFIDTable WHERE RFID = ?", (rfid,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"Balance": result[0], "ESPID": result[1]}
    return None

def get_transactions(rfid, db_path="./Database.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ESPNumber WHERE RFID = ?", (rfid,))
    transactions = cursor.fetchall()
    conn.close()
    return transactions

# ---------- Customer Dashboard ----------
def customer_dashboard(rfid):
    st.subheader("🎟️ Customer Dashboard")
    user_data = get_rfid_details(rfid)

    if user_data:
        st.success("✅ Login Successful!")
        
        # Centering the card using HTML & CSS
        st.markdown(f"""
            <style>
                .card-container {{
                    display: flex;
                    justify-content: center;
                }}
                .info-card {{
                    border: 2px solid white !important;
                    padding: 20px;
                    border-radius: 15px;
                    background-color: black;
                    color: white;
                    width: 50%;
                    text-align: center;
                    box-shadow: 4px 4px 10px rgba(255, 255, 255, 0.3);
                }}
            </style>
        
            <div class="card-container">
                <div class="info-card">
                    <h3>🎟️ RFID: {rfid}</h3>
                    <p><b>💰 Balance:</b> {user_data['Balance']} </p>
                    <p><b>🔄 Linked ESPID:</b> {user_data['ESPID']} </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Display transactions
        transactions = get_transactions(rfid)
        st.subheader("📜 Transaction History")
        if transactions:
            for t in transactions:
                st.write(f"🔹 **Transaction ID:** {t[0]} | **Amount:** {t[2]}")
        else:
            st.warning("No transactions found.")
    else:
        st.error("RFID details not found.")

# ---------- Admin Dashboard ----------
def admin_dashboard():
    st.subheader("🛠️ Admin Dashboard")

    conn = sqlite3.connect("./Database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT RFID FROM ESPNumber")
    rfids = [row[0] for row in cursor.fetchall()]
    conn.close()

    selected_rfid = st.selectbox("Select RFID to View Transactions", rfids)

    if st.button("View Transactions"):
        transactions = get_transactions(selected_rfid)
        if transactions:
            st.write(f"📜 Transactions for **{selected_rfid}**:")
            for t in transactions:
                st.write(f"🔹 **Transaction ID:** {t[0]} | **Amount:** {t[2]}")
        else:
            st.warning("No transactions found for this RFID.")

# ---------- Main Page ----------
st.set_page_config(page_title="RFID Access System", page_icon="🔑", layout="centered")

st.title("🔑 RFID Access System")

page = st.sidebar.radio("Select Role", ["Customer Login", "Admin Login"])

if page == "Customer Login":
    st.subheader("🎟️ Customer Login")
    rfid = st.text_input("Enter RFID")
    password = st.text_input("Enter Password", type="password")
    
    if st.button("Login"):
        if authenticate_customer(rfid, password):
            customer_dashboard(rfid)
        else:
            st.error("❌ Invalid RFID or Password.")

elif page == "Admin Login":
    st.subheader("🛠️ Admin Login")
    username = st.text_input("Enter Admin Username")
    password = st.text_input("Enter Password", type="password")
    
    if st.button("Login"):
        if authenticate_admin(username, password):  # ✅ Uses fixed "admin" credentials
            admin_dashboard()
        else:
            st.error("❌ Invalid Admin Credentials.")
