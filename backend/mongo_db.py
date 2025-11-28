from pymongo import MongoClient
import os
from pathlib import Path
import streamlit as st


def get_mongo_client():
    uri = None
    if hasattr(st, "secrets") and st.secrets.get("MONGO_URI"):
        uri = st.secrets["MONGO_URI"]
    else:
        uri = os.environ.get("MONGO_URI")
    if not uri:
        raise RuntimeError("MONGO_URI not found in Streamlit secrets or environment.")
    return MongoClient(uri)


def get_db(db_name="email_agent"):
    client = get_mongo_client()
    return client[db_name]
