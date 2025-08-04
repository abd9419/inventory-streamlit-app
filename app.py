import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
import seaborn as sns
from PIL import Image
import os
from datetime import datetime, timedelta
import io
import base64
import uuid
import hashlib
import random
import plotly.express as px
import plotly.graph_objects as go
import warnings

warnings.filterwarnings("ignore")

# Set Streamlit page config
st.set_page_config(
    page_title="\u0646\u0638\u0627\u0645 \u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0645\u062e\u0627\u0632\u0646",
    page_icon="\ud83d\udce6",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Connect to SQLite DB
conn = sqlite3.connect('inventory.db', check_same_thread=False)
c = conn.cursor()

# Example: Create users table if not exists
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        permissions TEXT,
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Insert default admin user if needed
c.execute('SELECT COUNT(*) FROM users WHERE username = "admin"')
if c.fetchone()[0] == 0:
    admin_password = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute('''
        INSERT INTO users (username, password, role, permissions, active)
        VALUES (?, ?, ?, ?, ?)
    ''', ('admin', admin_password, 'admin', 'view,add,edit,delete', 1))
conn.commit()

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(username, password):
    hashed_password = hash_password(password)
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    return result and result[0] == hashed_password

def show_login():
    st.title("\u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u062f\u062e\u0648\u0644")
    username = st.text_input("\u0627\u0633\u0645 \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645")
    password = st.text_input("\u0643\u0644\u0645\u0629 \u0627\u0644\u0645\u0631\u0648\u0631", type="password")
    if st.button("\u062f\u062e\u0648\u0644"):
        if verify_password(username, password):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.success("\u062a\u0645 \u0627\u0644\u062f\u062e\u0648\u0644 \u0628\u0646\u062c\u0627\u062d")
            st.rerun()
        else:
            st.error("\u062e\u0637\u0623 \u0641\u064a \u0627\u0633\u0645 \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645 \u0623\u0648 \u0643\u0644\u0645\u0629 \u0627\u0644\u0645\u0631\u0648\u0631")

def main_app():
    st.sidebar.title("\u0627\u0644\u0642\u0627\u0626\u0645\u0629 \u0627\u0644\u0631\u0626\u064a\u0633\u064a\u0629")
    menu = st.sidebar.radio("\u0627\u062e\u062a\u0631 \u0627\u0644\u0648\u0638\u064a\u0641\u0629", [
        "\u0627\u0644\u0631\u0626\u064a\u0633\u064a\u0629",
        "\u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a"
    ])
    if menu == "\u0627\u0644\u0631\u0626\u064a\u0633\u064a\u0629":
        st.header("\u0645\u0631\u062d\u0628\u0627 \u0628\u0643 \u0641\u064a \u0646\u0638\u0627\u0645 \u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0645\u062e\u0627\u0632\u0646")
    elif menu == "\u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a":
        st.header("\u0642\u0633\u0645 \u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a")

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    show_login()
else:
    main_app()
