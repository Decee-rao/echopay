from fastapi import FastAPI, HTTPException
import sqlite3
from pydantic import BaseModel
from typing import List

# Initialize FastAPI app
app = FastAPI()

DB_PATH = "./Database.db"

# ---------- Database Connection ----------
def get_db():
    """Establish a database connection with dictionary-like row access."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enables access via column names
        return conn
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")

# ---------- Request Models ----------
class UserAuthRequest(BaseModel):
    rfid: str
    password: str

class AdminAuthRequest(BaseModel):
    username: str
    password: str

class TransactionResponse(BaseModel):
    rfid: str
    espid: str
    amount: int  # Integer type based on schema

# ---------- API Endpoints ----------

@app.get("/")
def home():
    return {"message": "Welcome to the RFID API"}

# ✅ Authenticate Customer
@app.post("/authenticate/customer")
def authenticate_customer(request: UserAuthRequest):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT Password FROM UserAuth WHERE RFID = ?", (request.rfid,))
        user = cursor.fetchone()

        if user and user["Password"] == request.password:
            return {"status": "success", "message": "Login successful"}
        raise HTTPException(status_code=401, detail="Invalid RFID or Password")

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        conn.close()

# ✅ Authenticate Admin
@app.post("/authenticate/admin")
def authenticate_admin(request: AdminAuthRequest):
    if request.username == "admin" and request.password == "admin":
        return {"status": "success", "message": "Admin login successful"}
    raise HTTPException(status_code=401, detail="Invalid Admin Credentials")

# ✅ Fetch Balance by UID (assuming UID = RFID)
@app.get("/balance/{uid}")
def get_balance(uid: str):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT Balance FROM RFIDTable WHERE RFID = ?", (uid,))
        result = cursor.fetchone()

        if result:
            return {"uid": uid, "balance": result["Balance"]}
        else:
            raise HTTPException(status_code=404, detail="UID not found")

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        conn.close()

# ✅ Fetch Transactions for RFID (Fixed Column Names)
@app.get("/transactions/{rfid}", response_model=List[TransactionResponse])
def get_transactions(rfid: str):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT RFID, ESPID, TransactionAmt FROM ESPNumber WHERE RFID = ?", (rfid,))
        transactions = cursor.fetchall()

        if transactions:
            return [
                {"rfid": t["RFID"], "espid": t["ESPID"], "amount": t["TransactionAmt"]}
                for t in transactions
            ]
        raise HTTPException(status_code=404, detail="No transactions found")

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        conn.close()

# ✅ Fetch All Unique RFIDs
@app.get("/rfid-list")
def get_rfid_list():
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT DISTINCT RFID FROM RFIDTable")
        rfids = [row["RFID"] for row in cursor.fetchall()]
        return {"rfids": rfids}

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        conn.close()

# ✅ Fetch Transaction Amount by RFID and ESPID
@app.get("/transaction-amount/{rfid}/{espid}")
def get_transaction_amount(rfid: str, espid: str):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT TransactionAmt FROM ESPNumber WHERE RFID = ? AND ESPID = ?", (rfid, espid))
        result = cursor.fetchone()

        if result:
            return {"rfid": rfid, "espid": espid, "transaction_amount": result["TransactionAmt"]}
        else:
            raise HTTPException(status_code=404, detail="No transaction amount found for the given RFID and ESPID")

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        conn.close()
