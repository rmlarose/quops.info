"""Tools for interacting with the database on MongoDB."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import streamlit as st
from pymongo import MongoClient


# Constants: Keys for data.
ID: str = "_id"
REFERENCE: str = "Reference"
DATE: str = "Date"
COMPUTATION: str = "Computation"
NUMBER_OF_QUBITS: str = "Number of qubits"
NUMBER_OF_TWO_QUBIT_GATES: str = "Number of two-qubit gates"
NUMBER_OF_ONE_QUBIT_GATES: str = "Number of single-qubit gates"
TOTAL_NUMBER_OF_GATES: str = "Total number of gates"
CIRCUIT_DEPTH: str = "Circuit depth"
CIRCUIT_DEPTH_MEASURE: str = "Circuit depth measure"
INSTITUTION: str = "Institution"
COMPUTER: str = "Computer"
STATUS: str = "status"
COMMENTS: str = "comments"


@dataclass
class Status:
    """Valid options for the STATUS field of database entries."""

    APPROVED: str = "approved"
    PENDING: str = "pending"
    UPDATE_REQUESTED: str = "UPDATE REQUESTED"


def get_connection():
    return MongoClient(st.secrets["mongo"]["host"])


def get_database():
    client = get_connection()
    return client[st.secrets["mongo"]["database"]]


def get_collection():
    database = get_database()
    return database[st.secrets["mongo"]["collection"]]


def get_dataframe(filter: Dict[Any, Any] | None = None):
    if not filter:
        filter = {}
    collection = get_collection()
    return pd.DataFrame(list(collection.find(filter)))


def insert_datapoint(
    reference: str,
    date: datetime,
    computation: List[str],
    num_qubits: int,
    num_2q_gates: int,
    num_1q_gates: int,
    total_gates: int,
    circuit_depth: int,
    circuit_depth_measure: str,
    institution: str,
    computer: str,
    status: str,
    comments: str = "",
) -> bool:
    try:
        collection = get_collection()
        collection.insert_one(
            {
                REFERENCE: reference,
                DATE: date,
                COMPUTATION: computation,
                NUMBER_OF_QUBITS: num_qubits,
                NUMBER_OF_TWO_QUBIT_GATES: num_2q_gates,
                NUMBER_OF_ONE_QUBIT_GATES: num_1q_gates,
                TOTAL_NUMBER_OF_GATES: total_gates,
                CIRCUIT_DEPTH: circuit_depth,
                CIRCUIT_DEPTH_MEASURE: circuit_depth_measure,
                INSTITUTION: institution,
                COMPUTER: computer,
                STATUS: status,
                COMMENTS: comments,
            }
        )

        return True
    except Exception as e:
        st.error(f"Unable to retrieve collection and/or insert datapoint. Error: {e}")
        return False


def get_admins():
    client = get_connection()
    db = client[st.secrets["mongo"]["adatabase"]]
    return db[st.secrets["mongo"]["acollection"]]


def is_valid_admin(username, password) -> bool:
    try:
        ad = get_admins()
        user = ad.find_one({username: password})
        return user is not None
    except Exception as e:
        st.error(f"Database error: {e}")
        return False
