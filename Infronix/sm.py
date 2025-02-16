import requests
import threading
import time
import json
import tkinter as tk
from tkinter import messagebox
# from twilio.rest import Client
import sqlite3



client = Client(ACCOUNT_ID, AUTH_TOKEN)

ESP_SERVER_IP = "192.168.185.249"

DB_PATH = "./Database.db"

last_uid = None
last_uid_timestamp = 0
lock = threading.Lock() 

# GUI Components
running = False  # Controls the fetch loop
response_amount = 10  # Default response amount


# ---------- Database Functions ----------

def get_db_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initialize database table if not exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rfid_data (
            UID TEXT PRIMARY KEY,
            ESP_ID TEXT,
            Timestamp REAL
        )
    """)
    conn.commit()
    conn.close()


def add_to_db(uid, espid):
    """Insert new RFID entry into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO rfid_data (UID, ESP_ID, Timestamp) 
        VALUES (?, ?, ?)
    """, (uid, espid, time.time()))

    conn.commit()
    conn.close()


# ---------- ESP Communication ----------

def send_json_to_esp(response_value):
    """Send a response value to the ESP8266 via HTTP GET request."""
    url = f"http://{ESP_SERVER_IP}/1010?response={response_value}"

    try:
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        log_message(f"ESP8266 Response: {response.text}")

    except requests.exceptions.RequestException as e:
        log_message(f"Request failed: {e}")


def get_posts():
    """Fetch UID and ESP ID from ESP8266 and process new data based on timing conditions."""
    global last_uid, last_uid_timestamp
    url = f"http://{ESP_SERVER_IP}/uid"

    try:
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        posts = response.json()

        uid = posts.get('uid')
        espid = posts.get('espid')

        if uid and espid:
            current_time = time.time()

            with lock:
                # If it's a new UID or 30 seconds have passed since last UID, process it
                if uid != last_uid or (current_time - last_uid_timestamp >= 30):
                    last_uid = uid
                    last_uid_timestamp = current_time
                    log_message(f"Processing UID: {uid}, ESP ID: {espid}")

                    # Add to database (NO deletion of old entries)
                    add_to_db(uid, espid)

                    threading.Thread(target=send_json_to_esp, args=(response_amount,)).start()
                else:
                    log_message(f"UID {uid} ignored (same as last and within 30 seconds)")

            update_labels(uid, espid)

    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        log_message(f"Error fetching posts: {e}")


# ---------- GUI & Controls ----------

def fetch_loop():
    """Continuously fetch data if running is True."""
    while running:
        get_posts()
        time.sleep(1)  # Prevent overwhelming the ESP server


def start_fetching():
    """Start fetching data in a separate thread."""
    global running
    if not running:
        running = True
        threading.Thread(target=fetch_loop, daemon=True).start()
        log_message("Started fetching data...")


def stop_fetching():
    """Stop fetching data."""
    global running
    running = False
    log_message("Stopped fetching data.")


def send_manual_response():
    """Send manually entered response value to ESP."""
    global response_amount
    try:
        response_amount = int(response_entry.get())
        send_json_to_esp(response_amount)
        log_message(f"Sent manual response: {response_amount}")
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number")


def log_message(message):
    """Log messages in the GUI."""
    log_text.insert(tk.END, message + "\n")
    log_text.see(tk.END)


def update_labels(uid, espid):
    """Update UID and ESP ID labels in the GUI."""
    uid_label.config(text=f"UID: {uid}")
    espid_label.config(text=f"ESP ID: {espid}")


# ---------- GUI Setup ----------

root = tk.Tk()
root.title("ESP8266 RFID Manager")
root.geometry("500x400")

# Initialize database
init_db()

# UID & ESP ID Labels
uid_label = tk.Label(root, text="UID: -", font=("Arial", 12))
uid_label.pack(pady=5)

espid_label = tk.Label(root, text="ESP ID: -", font=("Arial", 12))
espid_label.pack(pady=5)

# Manual Response Entry
tk.Label(root, text="Set Response Amount:", font=("Arial", 10)).pack()
response_entry = tk.Entry(root)
response_entry.pack(pady=5)
response_entry.insert(0, str(response_amount))  # Default value

send_button = tk.Button(root, text="Send Response", command=send_manual_response)
send_button.pack(pady=5)

# Start/Stop Buttons
start_button = tk.Button(root, text="Start Fetching", command=start_fetching, bg="green", fg="white")
start_button.pack(pady=5)

stop_button = tk.Button(root, text="Stop Fetching", bg="red", fg="white", command=stop_fetching)
stop_button.pack(pady=5)

# Log Display
log_text = tk.Text(root, height=10, width=60)
log_text.pack(pady=5)

# Run the GUI
root.mainloop()
