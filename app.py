"""The QuOps.Info website."""

from datetime import datetime
import random
import string

import pandas as pd

import streamlit as st
from streamlit.components.v1 import html

import plotly.express as px

from captcha.image import ImageCaptcha

from admin import show_admin_page
import database
import utils


# Initialize session state for login.  TODO: Is this still needed?
if "logged_in" not in st.session_state:
    st.session_state.logged_in = "login"

# Page setup.
st.set_page_config(
    page_title="QuOps.Info",
    page_icon="./assets/logo.png",
    layout="wide",
)


def show_app():
    st.title("🔬 Quantum Operations (QuOps) Info")

    if "clicked_id" not in st.session_state:
        st.session_state.clicked_id = None

    # Define tabs.
    about_tab, visualization_tab, submit_tab, update_tab, admin_tab = st.tabs(
        [
            "About",
            "Visualization",
            "Submit New Datapoint",
            "Update a Datapoint",
            "Admin Login",
        ]
    )

    def switch(tab):
        return f"""
    var tabGroup = window.parent.document.getElementsByClassName("stTabs")[0]
    var tab = tabGroup.getElementsByTagName("button")
    tab[{tab}].click()
    """

    # last_row = st.container()
    # if last_row.button("Update Datapoint"):
    #     html(f"<script>{switch(3)}</script>", height=0)

    length_captcha = 4
    width = 200
    height = 150

    html(f"<script>{switch(1)} </script>", height=0)

    # The "About" tab.
    with about_tab:
        # Inject button + JS in one iframe
        html(
            f"""
             <style>
             button
             {{
                 
                border: none;
                background-color: white;
                color: blue;
                text-decoration: underline;
                cursor: pointer;
                font: inherit;
                padding: 0;
             }}
             </style>
             <div style="font-family: system-ui, sans-serif; line-height: 1.6; font-size: 1rem;">
                <p>
                    Track the quantum operations (QuOps) used in state-of-the-art quantum computations over time.
                </p>

                <p>
                    On the <button class="goto" style="margin-left: 6px;">visualization page</button>:<br>
                    1. <strong>Hover</strong> over a point to see its data.<br>
                    2. <strong>Single-click</strong> a point to update its data.<br>
                    3. <strong>Double-click</strong> a point to open its reference.
                </p>

                <p>
                    You can also <button class="gotos" style="margin-left: 6px;">submit new datapoints</button>.
                </p>

                <p>
                    All new submissions and updates are reviewed by site administrators.
                </p>
            </div>
                
                <script>
                const be = document.querySelector(".goto");
                be.addEventListener("click", () => {{
                    {switch(1)}
                }});
                const bes = document.querySelector(".gotos");
                bes.addEventListener("click",()=>{{
                      {switch(2)} 
                    
                }});
                </script>
            """,
            height=500,
        )

    # The main visualization/plotting tab.
    with visualization_tab:
        all_data: pd.DataFrame = database.get_dataframe(
            filter={database.STATUS: database.Status.APPROVED}
        )

        # Create two columns: Left column for filtering/selecting criteria in the plot, right column for the plot itself.
        selection_column, plot_column, url_column = st.columns([2, 5, 1])

        # Filter controls in the first column
        with selection_column:
            # Institution filter.
            institutions_unique = sorted(all_data[database.INSTITUTION].unique())
            institutions_selected = st.multiselect(
                database.INSTITUTION, institutions_unique, default=institutions_unique
            )

            # Computer filter (based on selected institutions).
            filtered_computer_options = sorted(
                all_data[all_data[database.INSTITUTION].isin(institutions_selected)][
                    database.COMPUTER
                ]
                .dropna()
                .unique()
            )
            computers_selected = st.multiselect(
                database.COMPUTER,
                filtered_computer_options,
                default=filtered_computer_options,
            )

            # Year filter.
            years = [d.year for d in all_data[database.DATE]]
            all_data["Year"] = years  # For convenience later.
            years_unique = sorted(set(years))
            selected_years = st.multiselect(
                "Year", years_unique, default=years_unique
            )  # TODO: Explore options other than multiselect. Maybe a start, stop, [step]?

            # TODO: Add horizontal axis selection. (Qubits / date).
            x_options = [
                database.NUMBER_OF_QUBITS,
                database.DATE,
            ]
            x_axis_selection = st.selectbox("Horizontal axis", x_options, index=0)

            # Y-axis selection.
            y_options = [
                database.NUMBER_OF_TWO_QUBIT_GATES,
                database.NUMBER_OF_QUBITS,
                database.NUMBER_OF_ONE_QUBIT_GATES,
                database.TOTAL_NUMBER_OF_GATES,
                database.CIRCUIT_DEPTH,
            ]
            y_axis_selection = st.selectbox("Vertical axis", y_options, index=0)

            # Marker size selection.
            b_options = [
                "Date (more recent = larger)",
                "Equal size",
                database.NUMBER_OF_QUBITS,
                database.NUMBER_OF_TWO_QUBIT_GATES,
                database.NUMBER_OF_ONE_QUBIT_GATES,
                database.TOTAL_NUMBER_OF_GATES,
                database.CIRCUIT_DEPTH,
            ]
            b_axis = st.selectbox("Marker size", b_options, index=0)

            if b_axis == b_options[0]:
                dates = [d for d in all_data.Date]
                date_min = min(dates)
                date_max = max(dates)
                all_data["bubble_size"] = dates
                all_data["bubble_size"] = all_data["bubble_size"].apply(
                    lambda x: (
                        (x - date_min).days / (date_max - date_min).days
                        if pd.notnull(x)
                        else None
                    )
                )

                # Scale to a desired range (e.g., 10–60)
                all_data["bubble_size"] = (
                    all_data["bubble_size"] * 50 + 10
                )  # range from 10 to 60. TODO: Make these parameters.
                b_axis = "bubble_size"

            col5, col6 = st.columns(2)

            with col5:
                x_axis_scale = st.selectbox(
                    "Horizontal axis scale", ["Linear", "Log"], index=0
                )
            with col6:
                y_axis_scale = st.selectbox(
                    "Vertical axis scale", ["Linear", "Log"], index=1
                )

        # Filter DataFrame for plotting.
        data_to_plot = all_data[
            (all_data["Institution"].isin(institutions_selected))
            & (all_data["Computer"].isin(computers_selected))
            & (all_data["Year"].isin(selected_years))
        ]
        graph_df = data_to_plot.copy()

        if b_axis != "Equal size":
            data_to_plot = data_to_plot.dropna(subset=[b_axis])
            graph_df = data_to_plot.copy()
            bubble_index = graph_df.columns.get_loc(b_axis)
            min_value = graph_df.iloc[:, bubble_index].min()
            max_value = graph_df.iloc[:, bubble_index].max()
            min_value = 0 if pd.isna(min_value) else min_value
            max_value = 0 if pd.isna(max_value) else max_value

            bubble_index = int(bubble_index)
            min_value = float(min_value) if min_value is not None else 0
            max_value = float(max_value) if max_value is not None else 0
            b_size = [50, 120]
        else:
            graph_df = data_to_plot.copy()
            bubble_index = graph_df.columns.get_loc("Date")
            min_value = 50
            max_value = 50
            b_size = [50, 50]

        with plot_column:
            graph_df["Date"] = graph_df["Date"].astype(str)
            graph_df["_id"] = [str(id) for id in graph_df["_id"]]
            graph_df = graph_df.fillna("")

            graph_df["Quantum computer"] = (
                graph_df["Institution"] + " " + graph_df["Computer"]
            )
            computers = list(graph_df["Quantum computer"].unique())
            colors = {
                "IBM": "#006699",
                "Google": "#DB4437",
                "Quantinuum": "#30a08e",
            }  # TODO: Use custom colors for plotting based on institution colors.

            fig = px.scatter(
                data_frame=graph_df,
                x=x_axis_selection,
                y=y_axis_selection,
                log_x=x_axis_scale == "Log",
                log_y=y_axis_scale == "Log",
                size="bubble_size",  # TODO: Set to be selected marker size.
                color="Quantum computer",
                hover_data={
                    database.REFERENCE: True,
                    database.INSTITUTION: True,
                    database.COMPUTER: True,
                    database.DATE: True,
                    database.COMPUTATION: True,
                    "bubble_size": False,
                    "Quantum computer": False,
                },
                custom_data=database.REFERENCE,
            )

            def handle_selection():
                event = (
                    st.session_state.click
                )  # This is defined via key="click" in st.plotly_chart below.
                if event and event.selection.points:
                    selected_point = event.selection.points[0]
                    url = selected_point["customdata"][
                        0
                    ]  # TODO: Will index 0 always be the URL?
                    with url_column:
                        st.link_button(
                            f"Open reference: {url}",
                            url,
                            use_container_width=True,
                            type="primary",
                            icon="🔎",
                        )
                        # st.link_button()  # TODO: Add "update this point" option. See https://discuss.streamlit.io/t/switch-tabs-programitically/37887/8.
                    # st.write(f"Selected point: {selected_point}")
                # else:
                #     st.write("No point selected.")

            st.plotly_chart(
                fig, on_select=handle_selection, selection_mode="points", key="click"
            )

    # The tab for submitting a new datapoint.
    with submit_tab:
        institutions = list(all_data["Institution"].unique())

        # st.header("Submit Quantum Datapoint")

        # CAPTCHA Verification First
        if "controllo" not in st.session_state:
            st.session_state["controllo"] = False

        if st.session_state["controllo"] == False:
            st.markdown("Confirm humanity")

            selection_column, plot_column = st.columns([1, 1])

            if "Captcha" not in st.session_state:
                st.session_state["Captcha"] = "".join(
                    random.choices(
                        string.ascii_uppercase + string.digits, k=length_captcha
                    )
                )

            image = ImageCaptcha(width=width, height=height)
            data = image.generate(st.session_state["Captcha"])
            selection_column.image(data)

            captcha_input = plot_column.text_area("Enter captcha text", height=30)

            if st.button("Verify"):
                if st.session_state["Captcha"].lower() == captcha_input.strip().lower():
                    del st.session_state["Captcha"]
                    st.session_state["controllo"] = True
                    st.rerun()
                else:
                    st.error("🚨 Invalid Captcha")
                    del st.session_state["Captcha"]
                    st.rerun()

            # st.stop()  # Stop here until CAPTCHA is verified

        # Only show the form if CAPTCHA passed

        elif st.session_state["controllo"] == True:
            st.markdown(
                """
            <style>
                /* Hide the default Streamlit label */
                label[for="reference_input"] {
                    display: none;
                }
                /* Make the custom label green */
                .green-label {
                    color: green;
                    font-weight:bold;

                }
                .black-label{
                    color:black;
                    
                }
            </style>
        """,
                unsafe_allow_html=True,
            )

            st.markdown("Highlighted fields are required.")

            st.markdown(
                '<div class="green-label">Reference</div>', unsafe_allow_html=True
            )
            reference = st.text_input(
                label="",
                key="reference_input",
                help="The reference for the quantum computation, typically an arXiv or journal link",
            )

            st.markdown(
                '<div class="black-label">Experiment Date</div>', unsafe_allow_html=True
            )
            date = st.date_input(
                "",
                value=datetime.today(),
                help="The date the experiment was performed or published (typically the date of the reference)",
            )
            date = datetime(
                date.year, date.month, date.day
            )  # Convert from datetime.date to datetime.datetime.

            st.markdown(
                '<div class="black-label">Computation (comma-separated list)</div>',
                unsafe_allow_html=True,
            )
            computation_raw = st.text_area(
                "",
                help="The algorithm used/computation performed, for example Trotter, VQE, Phase estimation",
            )

            # st.markdown('<div class="black-label">Error Mitigation (comma-separated list)</div>', unsafe_allow_html=True)
            # error_mitigation_raw = st.text_area("", help="e.g. ZNE, Clifford Data Regression")

            st.markdown(
                '<div class="green-label">Number of Qubits</div>',
                unsafe_allow_html=True,
            )
            num_qubits_raw = st.text_input(
                "", help="Number of qubits used in the quantum computation"
            )
            num_qubits = (
                int(num_qubits_raw) if num_qubits_raw.strip().isdigit() else None
            )

            st.markdown(
                '<div class="black-label">Number of Two-Qubit Operations</div>',
                unsafe_allow_html=True,
            )
            num_2q_gates_raw = st.text_input(
                "",
                help="Number of two-qubit operations used in the quantum computation",
            )
            num_2q_gates = (
                int(num_2q_gates_raw) if num_2q_gates_raw.strip().isdigit() else None
            )

            st.markdown(
                '<div class="black-label">Number of Single-Qubit Operations</div>',
                unsafe_allow_html=True,
            )
            num_1q_gates_raw = st.text_input(
                "",
                help="Number of siingle-qubit operations used in the quantum computation",
            )
            num_1q_gates = (
                int(num_1q_gates_raw) if num_1q_gates_raw.strip().isdigit() else None
            )

            st.markdown(
                '<div class="black-label">Total Number of Operations</div>',
                unsafe_allow_html=True,
            )
            total_gates_raw = st.text_input(
                "",
                help="Total number of operations used in the quantum computation, e.g. single-qubit operations + two-qubit operations",
            )
            total_gates = (
                int(total_gates_raw) if total_gates_raw.strip().isdigit() else None
            )

            st.markdown(
                '<div class="black-label">Circuit Depth</div>', unsafe_allow_html=True
            )
            circuit_depth_raw = st.text_input(
                "",
                help="The depth of the circuit in the quantum computation (see Circuit Depth Measure).",
            )
            circuit_depth = (
                int(circuit_depth_raw) if circuit_depth_raw.strip().isdigit() else None
            )

            st.markdown(
                '<div class="black-label">Circuit Depth Measure</div>',
                unsafe_allow_html=True,
            )
            cdm_options = list(all_data["Circuit depth measure"].unique())
            try:
                selected_cdm = st.selectbox(
                    "",
                    options=cdm_options + ["Other"],
                    index=0,
                    help="The measure/metric used for circuit depth, for example two-qubit gate layers, Trotter step, etc. Number of two-qubit operations and/or total number of operations is preferred to this metric, and this should be used only when these are unknown.",
                )
                if selected_cdm == "Other":
                    raise TypeError("Type Manually")
                else:
                    circuit_depth_measure = selected_cdm
            except:
                circuit_depth_measure = st.text_input(
                    "Enter Circuit depth measure manually:",
                    help="The measure/metric used for circuit depth, for example two-qubit gate layers, Trotter step, etc. Number of two-qubit operations and/or total number of operations is preferred to this metric, and this should be used only when these are unknown.",
                )

            st.markdown(
                '<div class="green-label">Institution</div>', unsafe_allow_html=True
            )
            try:
                selected = st.selectbox(
                    "",
                    options=institutions + ["Other"],
                    index=0,
                    help="Who owns the quantum computer, e.g. Google, Quantinuum, QuEra",
                )
                if selected == "Other":
                    raise TypeError("Type Manually")
                else:
                    institution = selected
            except:
                institution = st.text_input(
                    "Enter Institution manually:",
                    help="Who owns the quantum computer, e.g. Google, Quantinuum, QuEra",
                )

            st.markdown(
                '<div class="green-label">Computer</div>', unsafe_allow_html=True
            )
            if selected != "Other":
                computers = list(
                    all_data[all_data["Institution"] == institution][
                        "Computer"
                    ].unique()
                )
                selected_comp = st.selectbox(
                    "",
                    options=computers + ["Other"],
                    index=0,
                    help="The name or other identifying label for the quantum computer",
                )
                try:
                    if selected_comp == "Other":
                        raise TypeError("Type Manually")
                    else:
                        computer = selected_comp
                except:
                    computer = st.text_input(
                        "Enter Computer manually:",
                        help="The name or other identifying label for the quantum computer",
                    )
            else:

                computer = st.text_input(
                    "Enter Computer manually:",
                    help="The name or other identifying label for the quantum computer",
                )

            submit = st.button("Submit")

            if st.session_state.get("submission_success"):
                st.success(
                    "Datapoint submitted successfully and is now pending admin approval - thank you!"
                )
                del st.session_state["submission_success"]

            error_count_new = 0
            if submit:
                if not reference:
                    error_count_new += 1
                    st.error(
                        "Please fill out Reference(url or citation) as it is a required field. "
                    )
                if not num_qubits:
                    error_count_new += 1
                    st.error(
                        "Please fill out Number of Qubits as it is a required field. "
                    )
                if not institution:
                    error_count_new += 1
                    st.error("Please fill out Institution as it is a required field. ")
                if not computer:
                    error_count_new += 1
                    st.error("Please fill out Computer as it is a required field. ")
                if not (num_2q_gates or total_gates):
                    error_count_new += 1
                    st.error(
                        "Please fill either Number of two-Qubit operations or Total Number of Operations"
                    )

                if error_count_new == 0:
                    computation_list = [
                        x.strip() for x in computation_raw.split(",") if x.strip()
                    ]
                    datapoint_inserted = database.insert_datapoint(
                        reference=reference,
                        date=date,
                        computation=computation_list,
                        num_qubits=num_qubits,
                        num_2q_gates=num_2q_gates,
                        num_1q_gates=num_1q_gates,
                        total_gates=total_gates,
                        circuit_depth=circuit_depth,
                        circuit_depth_measure=circuit_depth_measure,
                        institution=institution,
                        computer=computer,
                        status=database.Status.PENDING,
                    )

                    if datapoint_inserted:
                        st.success("Datapoint submitted successfully!")
                        # st.session_state['controllo'] = False

                        st.session_state.submission_success = True
                        st.rerun()

    # The tab for updating a datapoint.
    with update_tab:
        # if st.session_state.clicked_id is None:
        #     # st.subheader("Please provide the necessary details…")
        #     update_id = all_data.iloc[0]["_id"]
        # else:
        #     # st.subheader("Please provide the necessary details…")
        #     update_id = st.session_state.clicked_id
        #     st.session_state.visited = 1

        # record = all_data[all_data["_id"] == update_id]

        # if not record.empty:

        all_data = database.get_dataframe()
        reference_to_update = st.selectbox(  # TODO: Note: Can select based off data ID here, which is guarunteed to always be unique.
            database.REFERENCE,
            options=all_data[database.REFERENCE],
            help="The reference for the quantum computation, typically an arXiv or journal link. Note: The reference uniquely identifies the datapoint. To update the reference url itself (e.g., for a journal link), make a note with the new url in 'Justification for changes' at the end.",
        )
        record = all_data[all_data[database.REFERENCE] == reference_to_update]
        record = record.iloc[0]

        new_date = st.date_input("Date", value=record["Date"])
        new_date = datetime(year=new_date.year, month=new_date.month, day=new_date.day)
        new_qubits = st.number_input(
            "Number of Qubits",
            value=int(record["Number of qubits"]),
            help="Number of qubits used in the quantum computation",
        )

        try:
            num_2q_gates_raw = st.text_input(
                "Number of Two-Qubit Gates",
                value=record["Number of two-qubit gates"],
                help="Number of two-qubit operations used in the quantum computation",
            )
            new_num_2q_gates = (
                float(num_2q_gates_raw)
                if num_2q_gates_raw and not utils.is_nan_or_nan_string(num_2q_gates_raw)
                else None
            )
        except:
            st.error("Invalid input. Please input a valid number")

        try:
            num_1q_gates_raw = st.text_input(
                database.NUMBER_OF_ONE_QUBIT_GATES,
                value=record[database.NUMBER_OF_ONE_QUBIT_GATES],
                help="Number of single-qubit operations used in the quantum computation",
            )
            new_num_1q_gates = (
                int(num_1q_gates_raw)
                if num_1q_gates_raw and not utils.is_nan_or_nan_string(num_1q_gates_raw)
                else None
            )
        except:
            st.error("Invalid input. Please input a valid number")

        try:
            total_gates_raw = st.text_input(
                "Total number of gates",
                value=record["Total number of gates"],
                help="Total number of operations used in the quantum computation, e.g. single-qubit operations + two-qubit operations",
            )
            new_total_gates = (
                int(total_gates_raw)
                if total_gates_raw and not utils.is_nan_or_nan_string(total_gates_raw)
                else None
            )
        except:
            st.error("Invalid input. Please input a valid number")

        try:
            circuit_depth_raw = st.text_input(
                "Circuit depth",
                value=record["Circuit depth"],
                help="The depth of the circuit in the quantum computation (see Circuit Depth Measure).",
            )
            new_circuit_depth = (
                int(circuit_depth_raw)
                if circuit_depth_raw
                and not utils.is_nan_or_nan_string(circuit_depth_raw)
                else None
            )
        except:
            st.error("Invalid input. Please input a valid number")

        new_circuit_depth_measure = st.text_input(
            "Circuit depth measure",
            value=record["Circuit depth measure"],
            help="The measure/metric used for circuit depth, for example two-qubit gate layers, Trotter step, etc. Number of two-qubit operations and/or total number of operations is preferred to this metric, and this should be used only when these are unknown. ",
        )
        new_institution = st.text_input(
            "Institution",
            value=record["Institution"],
            help="Who owns the quantum computer, e.g. Google, Quantinuum, QuEra",
        )
        new_computation = st.text_input(
            "Computation", value=record["Computation"], help="e.g. QFT, Measurement"
        )
        new_computer = st.text_input(
            "Computer",
            value=record["Computer"],
            help="The name or other identifying label for the quantum computer",
        )
        # new_mitigation = st.text_input("Error Mitigations", value=record['Error mitigations'], help="e.g. ZNE, Clifford Data Regression")
        comments = st.text_input(
            "Justification for changes",
            value=record.get("feedback"),
            help="Clear description of the changes made with justification. For example: 'Changed the number of two-qubit operations from 512 to 1024. The correct number (1024 two-qubit operations) is stated in the caption of Figure 1 of the reference.'",
        )

        computation_list = [x.strip() for x in new_computation.split(",") if x.strip()]
        # error_mitigation_list = [x.strip() for x in new_mitigation.split(",") if x.strip()]

        # --- CAPTCHA ---
        col3, col4 = st.columns(2)

        if "update_captcha" not in st.session_state:
            st.session_state.update_captcha = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=length_captcha)
            )

        image1 = ImageCaptcha(width=width, height=height)
        data1 = image1.generate(st.session_state.update_captcha)
        col3.image(data1)

        captcha_input1 = col4.text_area("Enter the captcha text", height=30)

        error_count = 0

        if st.button("Verify humanity and submit"):
            if (
                st.session_state.update_captcha.lower()
                == captcha_input1.strip().lower()
            ):
                if not reference_to_update:
                    error_count += 1
                    st.error(
                        "Please fill out Reference(url or citation) as it is a required field. "
                    )
                if not new_qubits:
                    error_count += 1
                    st.error(
                        "Please fill out Number of Qubits as it is a required field. "
                    )
                if not (new_num_2q_gates or new_total_gates):
                    error_count += 1
                    st.error(
                        "Please fill either Number of two-Qubit operations or Total Number of Operations"
                    )
                if not new_institution:
                    error_count += 1
                    st.error("Please fill out Institution as it is a required field. ")
                if not new_computer:
                    error_count += 1
                    st.error("Please fill out Computer as it is a required field. ")
                if not comments:
                    error_count += 1
                    st.error(
                        "Please fill out Justification for changes as it is a required field. "
                    )

                # if reference and num_qubits and (num_2q_gates or total_gates):
                if error_count == 0:
                    collection = database.get_collection()
                    # TODO: Should this be insserting or updating? I beleive this is updating, so use find_one_and_update.
                    collection.insert_one(
                        {
                            database.REFERENCE: reference_to_update,
                            database.DATE: new_date,
                            database.COMPUTATION: computation_list,
                            database.NUMBER_OF_QUBITS: new_qubits,
                            database.NUMBER_OF_TWO_QUBIT_GATES: new_num_2q_gates,
                            database.NUMBER_OF_ONE_QUBIT_GATES: new_num_1q_gates,
                            database.TOTAL_NUMBER_OF_GATES: new_total_gates,
                            database.CIRCUIT_DEPTH: new_circuit_depth,
                            database.CIRCUIT_DEPTH_MEASURE: new_circuit_depth_measure,
                            database.INSTITUTION: new_institution,
                            database.COMPUTER: new_computer,
                            database.STATUS: database.Status.UPDATE_REQUESTED,
                            database.COMMENTS: comments,
                        }
                    )
                    st.success(
                        f"Update request successfully submitted for reference {record['Reference']}"
                    )
                    del st.session_state.update_captcha  # Reset captcha after success
            else:
                st.error("🚨 Invalid Captcha")
                del st.session_state.update_captcha
                st.rerun()

    with admin_tab:

        st.subheader("Admin Login")

        admin_user = st.text_input("Username", key="admin_user")
        admin_pass = st.text_input("Password", type="password", key="admin_pass")
        if st.button("Login as Admin"):
            if database.is_valid_admin(admin_user, admin_pass):
                st.success("✅ Admin login successful!")
                st.markdown("Welcome to the admin dashboard.")
                st.session_state.logged_in = "admin"
                # login_button = st.form_submit_button('Go to App')
                st.rerun()
            # Add your admin dashboard code here
            else:
                st.error("❌ Invalid credentials.")


# Main logic
# if st.session_state.logged_in == 'refresh':
#     #show_user_app()
#     show_login_form()
if st.session_state.logged_in == "app":
    # show_user_app()
    show_app()
elif st.session_state.logged_in == "admin":
    show_admin_page()
else:
    show_app()
