# seed_db.py
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit as st

# Define your initial curriculum
data = [
    # AI Catch-up
    {"topic": "RAG (Retrieval Augmented Generation)", "category": "AI", "difficulty": "5-min", "status": "New", "content_cache": ""},
    {"topic": "Vector Databases vs Traditional DBs", "category": "AI", "difficulty": "15-min", "status": "New", "content_cache": ""},
    {"topic": "LLM Agents & Tool Calling", "category": "AI", "difficulty": "15-min", "status": "New", "content_cache": ""},
    
    # Payments / Staff Eng
    {"topic": "Idempotency Keys in Distributed Systems", "category": "Payments", "difficulty": "5-min", "status": "New", "content_cache": ""},
    {"topic": "Distributed Transactions (Saga Pattern)", "category": "System Design", "difficulty": "Deep Dive", "status": "New", "content_cache": ""},
    {"topic": "Double Entry Ledger at Scale", "category": "Payments", "difficulty": "Deep Dive", "status": "New", "content_cache": ""},
    {"topic": "Staff Eng: Influence without Authority", "category": "Leadership", "difficulty": "5-min", "status": "New", "content_cache": ""},
]

df = pd.DataFrame(data)

# Connect and write
conn = st.connection("gsheets", type=GSheetsConnection)
conn.update(worksheet="Curriculum", data=df)
print("Database seeded successfully!")