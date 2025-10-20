"""The QuOps.Info website."""

from datetime import timedelta
import random
import string

import pandas as pd

import streamlit as st
from streamlit.components.v1 import html

import plotly.express as px

from captcha.image import ImageCaptcha

from admin import show_admin_page
import database
import user_input


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
            "Submit datapoint",
            "Update datapoint",
            "Admin login",
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
                    On the<button class="goto" style="margin-left: 6px;">visualization page</button>, hover over a point to see its data and click a point to open its reference.
                </p>

                <p>
                    Please consider<button class="gotos" style="margin-left: 6px;">submitting a datapoint</button> and/or updating a datapoint!
                </p>

                <p>
                    All new submissions and updates are reviewed by site administrators.
                </p>

                <p>
                    For background information, we recommend <a target="_blank" rel="noopener noreferrer" href="https://arxiv.org/abs/1801.00862">Quantum computing in the NISQ era and beyond</a> and <a target="_blank" rel="noopener noreferrer" href="https://arxiv.org/abs/2502.17368">Beyond NISQ: The Megaquop Machine</a>.
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

        # Selection/filters on the left, plot on the right.
        selection_column, plot_column = st.columns([2, 5])

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

            # Dates filter.
            min_date = min(all_data[database.DATE]).to_pydatetime()
            max_date = max(all_data[database.DATE]).to_pydatetime()
            min_date_selected, max_date_selected = st.slider(
                "Dates",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),
                step=timedelta(days=1),
            )

            col5, col6 = st.columns(2)
            with col5:
                x_options = [
                    database.NUMBER_OF_QUBITS,
                    database.DATE,
                ]
                x_axis_selection = st.selectbox("Horizontal axis", x_options, index=0)

                xscale_options = (
                    ["Linear"]
                    if x_axis_selection == database.DATE
                    else ["Linear", "Log"]
                )
                x_axis_scale = st.selectbox(
                    "Horizontal axis scale", xscale_options, index=0
                )
            with col6:
                # Y-axis selection.
                y_options = [
                    database.NUMBER_OF_TWO_QUBIT_GATES,
                    database.NUMBER_OF_QUBITS,
                    database.NUMBER_OF_ONE_QUBIT_GATES,
                    database.TOTAL_NUMBER_OF_GATES,
                    database.CIRCUIT_DEPTH,
                ]
                y_axis_selection = st.selectbox("Vertical axis", y_options, index=0)
                y_axis_scale = st.selectbox(
                    "Vertical axis scale", ["Linear", "Log"], index=1
                )

            # Marker size selection.
            marker_size_options = [
                "Date (more recent = larger)",
                "Equal size",
                database.NUMBER_OF_QUBITS,
                database.NUMBER_OF_TWO_QUBIT_GATES,
                database.NUMBER_OF_ONE_QUBIT_GATES,
                database.TOTAL_NUMBER_OF_GATES,
                database.CIRCUIT_DEPTH,
            ]
            marker_size_selection = st.selectbox(
                "Marker size", marker_size_options, index=0
            )

            # Columns to show the URL when a point is clicked on the plot.
            # TODO: Not ideal. Explore options for displaying under the plot. Maybe st.container()?
            ref_column1, ref_column2 = st.columns([0.40, 0.60])

        with plot_column:
            # Filter DataFrame for plotting.
            graph_df = all_data[
                (all_data[database.INSTITUTION].isin(institutions_selected))
                & (all_data[database.COMPUTER].isin(computers_selected))
                & (all_data[database.DATE] >= min_date_selected)
                & (all_data[database.DATE] <= max_date_selected)
            ]
            # graph_df = graph_df.fillna("")

            if marker_size_selection == marker_size_options[0]:
                date_min = min(graph_df[database.DATE])
                date_max = max(graph_df[database.DATE])
                graph_df["marker_size"] = graph_df[database.DATE]
                graph_df["marker_size"] = graph_df["marker_size"].apply(
                    lambda x: (
                        (x - date_min).days / (date_max - date_min).days
                        if pd.notnull(x)
                        else None
                    )
                )
                graph_df["marker_size"] = graph_df["marker_size"] * 125 + 10
                marker_size_selection = "marker_size"

            elif marker_size_selection == "Equal size":
                graph_df["marker_size"] = 125
            else:
                graph_df["marker_size"] = graph_df[marker_size_selection]

            graph_df["Quantum computer"] = (
                graph_df["Institution"] + " " + graph_df["Computer"]
            )
            computers = list(graph_df["Quantum computer"].unique())
            colors = {
                "IBM": "#006699",
                "Google": "#DB4437",
                "Quantinuum": "#30a08e",
            }  # TODO: Use custom colors for plotting based on institu tion colors.

            fig = px.scatter(
                data_frame=graph_df,
                x=x_axis_selection,
                y=y_axis_selection,
                log_x=x_axis_scale == "Log",
                log_y=y_axis_scale == "Log",
                size="marker_size",
                color="Quantum computer",
                hover_data={
                    database.REFERENCE: True,
                    database.INSTITUTION: True,
                    database.COMPUTER: True,
                    database.DATE: True,
                    database.COMPUTATION: True,
                    "marker_size": False,
                    "Quantum computer": False,
                },
                custom_data=database.REFERENCE,
                height=625,
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
                    with ref_column1:
                        st.write("URL of selected point:")
                    with ref_column2:
                        st.write(f"{url}")
                        # st.link_button()  # TODO: Add "update this point" option. See https://discuss.streamlit.io/t/switch-tabs-programitically/37887/8.
                    # st.write(f"Selected point: {selected_point}")
                # else:
                #     st.write("No point selected.")

            st.plotly_chart(
                fig, on_select=handle_selection, selection_mode="points", key="click"
            )

    # The tab for submitting a new datapoint.
    with submit_tab:
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

            if st.button("Verify humanity"):
                if st.session_state["Captcha"].lower() == captcha_input.strip().lower():
                    del st.session_state["Captcha"]
                    st.session_state["controllo"] = True
                    st.rerun()
                else:
                    st.error("🚨 Invalid Captcha")
                    del st.session_state["Captcha"]
                    st.rerun()

        # Show the form when the captcha is passed.
        elif st.session_state["controllo"] == True:
            try:
                (
                    reference,
                    date,
                    institution,
                    computer,
                    num_qubits,
                    num_2q_gates,
                    total_gates,
                    circuit_depth,
                    circuit_depth_measure,
                    num_1q_gates,
                    computation_list,
                ) = user_input.get_user_input(update=False)

            # if st.session_state.get("submission_success"):
            #     st.success(
            #         "Datapoint submitted successfully and is pending admin approval - thanks for contributing to QuOps.Info!"
            #     )
            #     del st.session_state["submission_success"]

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
                    st.success(
                        "Datapoint submitted successfully and pending admin approval - thanks for contributing to QuOps.Info!"
                    )

                    st.session_state.submission_success = True
                    # TODO: Sleep for a second here?
                    # TODO: Clear form.
                    st.rerun()
            except TypeError:
                pass

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
        try:
            (
                reference,
                date,
                institution,
                computer,
                num_qubits,
                num_2q_gates,
                total_gates,
                circuit_depth,
                circuit_depth_measure,
                num_1q_gates,
                computation_list,
                comments,
            ) = user_input.get_user_input(update=True)

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
                status=database.Status.UPDATE_REQUESTED,
                comments=comments,
            )
            st.success(
                f"Update request successfully submitted for reference {reference}"
            )
            del st.session_state.update_captcha  # Reset captcha after success
        except TypeError:
            pass

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
