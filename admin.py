"""The Admin page of QuOps.Info."""

import datetime

import numpy as np
import pandas as pd
import streamlit as st

from database import get_collection, get_dataframe


def is_nan_or_nan_string(val):
    # Check for actual NaN
    if isinstance(val, float) and np.isnan(val):
        return True
    if isinstance(val, np.float64) and np.isnan(val):
        return True
    # Check for string 'nan', 'NaN', etc.
    if isinstance(val, str) and val.strip().lower() == 'nan':
        return True
    return False


def show_admin_page():
    # --- Initialize page state ---
    if "admin_page" not in st.session_state:
        st.session_state.admin_page = "Data Table"

    # --- Sidebar vertical tabs ---
    st.sidebar.title("🔧 Admin Panel")

    if st.sidebar.button("📊 Manage Requests"):
        st.session_state.admin_page = "Data Table"

    if st.sidebar.button("📊 View Data Tables"):
        st.session_state.admin_page = "Database"

    if st.sidebar.button("📊 Logout"):
        st.session_state.logged_in = "app"
        st.rerun()
        
    if st.session_state.admin_page == "Database":
        df_all = get_dataframe()
        st.dataframe(df_all)
        df_ids = df_all["_id"].unique()
        id_selected = st.selectbox("Select the id",df_ids)
        operation = st.selectbox("Select the operation to be performed", ['Delete', 'Update'])

        # Initialize session state variables
        if "delete_requested" not in st.session_state:
            st.session_state.delete_requested = False
        if "delete_confirmed" not in st.session_state:
            st.session_state.delete_confirmed = False

        if operation == "Delete":
            # Step 1: User clicks "Delete Record"
            if st.button("Delete Record"):
                st.session_state.delete_requested = True

            # Step 2: Show confirmation buttons
            if st.session_state.delete_requested and not st.session_state.delete_confirmed:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Confirm Deletion"):
                        st.session_state.delete_confirmed = True
                with col2:
                    if st.button("❌ Cancel"):
                        st.session_state.delete_requested = False
                        st.session_state.delete_confirmed = False
                        st.warning("Deletion cancelled.")
                        st.rerun()

            # Step 3: Actually delete the record
            if st.session_state.delete_confirmed:
                collection = get_collection()
                collection.find_one_and_delete({"_id": id_selected})  # TODO: Almost certain bug, need to update `id_selected` for MongoDB. Old code is below:

                """
                client = get_connection()
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("DELETE FROM quant_data WHERE id = %s", (int(id_selected),))
                conn.commit()
                cur.close()
                conn.close()
                """
                st.success(f"✅ Successfully deleted the record with _id {id_selected}.")

                if st.button("🔄 Click to refresh and see updates"):
                    st.session_state.delete_requested = False
                    st.session_state.delete_confirmed = False
                    st.rerun()

        """Update an data entry."""
        if operation == "Update":
            record = df_all[df_all["_id"] == id_selected]
            if not record.empty:
                record = record.iloc[0]

                ref = st.text_input("Reference", value=record['Reference'])
                new_date = st.date_input("Date", value=record['Date'])

                if isinstance(new_date, datetime.date):
                    new_date = datetime.datetime(new_date.year, new_date.month, new_date.day)

                new_qubits = st.number_input("Number of qubits", value=int(record['Number of qubits']))

                try:
                    num_2q_gates_raw = st.text_input("Number of two-qubit gates", value=record['Number of two-qubit gates'])
                    new_num_2q_gates = int(num_2q_gates_raw) if num_2q_gates_raw and not is_nan_or_nan_string(num_2q_gates_raw) else None
                except:
                    st.error("Invalid input. Please input a valid number")
                    

                try:
                    num_1q_gates_raw = st.text_input("Number of single-qubit gates", value=record['Number of single-qubit gates'])
                    new_num_1q_gates = int(num_1q_gates_raw) if num_1q_gates_raw and not is_nan_or_nan_string(num_1q_gates_raw) else None
                except:
                    st.error("Invalid input. Please input a valid number")
                    

                try:
                    total_gates_raw = st.text_input("Total number of gates", value=record['Total number of gates'])
                    new_total_gates = int(total_gates_raw) if total_gates_raw and not is_nan_or_nan_string(total_gates_raw) else None
                except:
                    st.error("Invalid input. Please input a valid number")
                    
                try:
                    circuit_depth_raw = st.text_input("Circuit depth", value=record['Circuit depth'])
                    new_circuit_depth = int(circuit_depth_raw) if circuit_depth_raw and not is_nan_or_nan_string(circuit_depth_raw) else None
                except:
                    st.error("Invalid input. Please input a valid number")
                    
                new_circuit_depth_measure = st.text_input("Circuit depth measure", value=record['Circuit depth measure'])
                new_institution = st.text_input("Institution", value=record['Institution'])
                new_computation = st.text_input("Computation", value=record['Computation'])
                new_computer = st.text_input("Computer", value=record['Computer'])
                new_comments = st.text_input("Comments", value=record['comments'])

                computation_list = [x.strip() for x in new_computation.split(",") if x.strip()]

                error_count_a = 0
                if st.button("Save changes"):
                    if not ref:
                        error_count_a+=1
                        st.error("Reference (url or citation) is a required field.")
                    if not new_qubits:
                        error_count_a+=1
                        st.error("Number of qubits is a required field.")
                    if not (new_num_2q_gates or new_total_gates):
                        error_count_a+=1
                        st.error("Number of two-qubit operations OR Total number of operations is required.")
                    if not new_institution:
                        error_count_a+=1
                        st.error("Institution is a required field.")
                    if not new_computer:
                        error_count_a+=1
                        st.error("Computer is a required field. (Select Unknown if the computer is not named or unknown.)")
                    if error_count_a == 0:
                        collection = get_collection()
                        collection.find_one_and_update(
                            {"_id": id_selected},
                            {
                                "$set": {
                                    "Reference": ref,
                                    "Date": new_date,
                                    "Computation": computation_list,
                                    "Number of qubits": new_qubits,
                                    "Number of two-qubit gates": new_num_2q_gates,
                                    "Number of single-qubit gates": new_num_1q_gates,
                                    "Total number of gates": new_total_gates,
                                    "Circuit depth": new_circuit_depth,
                                    "Circuit depth measure": new_circuit_depth_measure,
                                    "Institution": new_institution,
                                    "Computer": new_computer,
                                    "status": "approved",
                                    "comments": new_comments,
                                }
                            }
                        )
                        st.success(f"Update done for ID : {record['_id']}")

                        if st.button("Click to refresh and see updates"):
                            st.rerun()

    # Approve or reject pending submissions.
    if st.session_state.admin_page == "Data Table":
        st.header("📈 Pending Submissions")
        try:
            collection = get_collection()
            data = list(collection.find({"status": "pending"}))  # TODO: Query the database directly like this instead of finding all first.
            df_data = pd.DataFrame(data)

            if not data:
                st.info("✅ No pending submissions.")
            else:
                for _, row in df_data.iterrows():
                    with st.container():
                        st.markdown("---")
                        col1, col2 = st.columns([8, 2])

                        with col1:
                            if row["status"]=="pending":  # TODO: Don't hardcode!!!!!!!
                                st.markdown("New Datapoint")
                                st.table(row)
                            else:
                                st.markdown("Update Datapoint")
                                if "comments" in row.keys():
                                    comments = row["comments"]
                                else:
                                    comments = ""
                                st.markdown(f"**Comments:** <span style='color:green'>{comments}</span>", unsafe_allow_html=True)
                                st.table(row)
                            

                        with col2:
                            c1, c2 = st.columns(2)
                            if c1.button("✅ Approve", key=f"approve_{row['_id']}"):
                                collection = get_collection()

                                if row['status']=='pending':
                                    collection.find_one_and_update(
                                        {"_id": row["_id"]}, {"$set": {"status": "approved"}}
                                    )
                                else:
                                    collection.find_one_and_delete({"_id": row["_id"]})

                                st.success(f"Approved ID {row['_id']}")
                                st.rerun()

                            if c2.button("❌ Reject", key=f"reject_{row['_id']}"):
                                collection = get_collection()
                                collection.find_one_and_delete({"_id": row["_id"]})
                                st.warning(f"Rejected ID {row['_id']}")
                                st.rerun()

        except Exception as e:
            st.error(f"Database error: {e}")
