import pandas as pd
import streamlit as st
from pymongo import MongoClient


@st.cache_resource
def get_connection():
    return MongoClient(st.secrets["mongo"]["host"])


@st.cache_resource
def get_admins():
    client = get_connection()
    db = client[st.secrets["mongo"]["adatabase"]]
    return db[st.secrets["mongo"]["acollection"]]


@st.cache_resource
def get_database():
    client = get_connection()
    return client[st.secrets["mongo"]["database"]]


@st.cache_resource
def get_collection():
    database = get_database()
    return database[st.secrets["mongo"]["collection"]]


@st.cache_resource
def get_dataframe():
    collection = get_collection()
    return pd.DataFrame(list(collection.find({})))


def load_data_from_db(conn: "PGConnection")->pd.DataFrame:
    query = "SELECT * FROM quant_data where status = 'APPROVED';"
    df_comp = pd.read_sql_query(query, conn)
    return df_comp
