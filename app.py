"""The QuOps.Info website."""

from datetime import datetime
import random
import string
import time

import numpy as np
import pandas as pd

import streamlit as st
from streamlit_echarts import st_echarts
from streamlit.components.v1 import html

import plotly.io as pio
pio.templates.default = "plotly"
from pyecharts.commons.utils import JsCode

from captcha.image import ImageCaptcha
from urllib.parse import urlparse

from admin import show_admin_page
from database import get_dataframe, get_collection, get_admins


# Initialize session state for Login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = 'login'

# Setting the wide page format
st.set_page_config(layout="wide")


def df_to_json_safe(df: pd.DataFrame):
    """
    Convert a pandas DataFrame into a JSON-safe list-of-lists format.
    Ensures numpy.int64, numpy.float64, NaN, etc. are converted to Python-native types.
    """
    def to_native(val):
        if isinstance(val, (np.generic,)):   # np.int64, np.float64, etc.
            return val.item()
        if pd.isna(val):  # Handle NaN / None
            return None
        return val
    
    return [df.columns.tolist()] + [[to_native(v) for v in row] for row in df.values.tolist()]


def is_hyperlink(s):
    try:
        result = urlparse(s)
        return all([result.scheme in ("http", "https"), result.netloc])
    except ValueError:
        return False


# Check credentials for admin and user
def check_credentials(username, password):
    try:
        ad = get_admins()
        user = ad.find_one({username: password})
        return user is not None
    except Exception as e:
        st.error(f"Database error: {e}")
        return False


def show_app():
        # --- Page Setup ---
    st.title("🔬 Quantum Operations (QuOps) Info")

    if "clicked_id" not in st.session_state:
        st.session_state.clicked_id = None
    
    # --- Tabs for Login Options ---
    about_tab, visualization_tab, submit_tab, update_tab, admin_tab = st.tabs(
        ["About", "Visualization", "Submit New Datapoint", "Update a Datapoint", "Admin Login"]
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

    # define the costant
    length_captcha = 4
    width = 200
    height = 150
    
    html(f"<script>{switch(1)} </script>", height=0)

    # TODO: Why is this defined here and not in database.py???
    # Database insertion function
    def insert_quantum_datapoint(
        reference, date, computation, num_qubits, num_2q_gates, num_1q_gates, total_gates,
        circuit_depth, circuit_depth_measure, institution, computer, status
    ):
        try:
            collection = get_collection()
            collection.insert_one({
                "Reference": reference,
                "Date": date,
                "Computation": computation,
                "Number of qubits": num_qubits,
                "Number of two-qubit gates": num_2q_gates,
                "Number of single-qubit gates": num_1q_gates,
                "Total number of gates": total_gates,
                "Circuit depth": circuit_depth,
                "Circuit depth measure": circuit_depth_measure,
                "Institution": institution,
                "Computer": computer,
                "status": status,
            })
            
            return True
        except Exception as e:
            st.error(f"Unable to retrieve collection and/or submit datapoint. Error: {e}")
            return False

    # The "About" tab.
    with about_tab:
        # Page title

        # Inject button + JS in one iframe
        html(f"""
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
            """, height=500)

    # The main visualization tab with the plot.
    with visualization_tab:
        df: pd.DataFrame = get_dataframe()

        # Create two columns
        selection_column, plot_column = st.columns([1, 2])

        # Filter controls in the first column
        with selection_column:
            # Institution filter
            comp_options = list(df['Institution'].unique())
            selected_comps = st.multiselect("Institution", comp_options, default=comp_options)

            # Computer filter based on Institution
            filtered_computer_options = df[df['Institution'].isin(selected_comps)]['Computer'].dropna().unique()
            selected_computers = st.multiselect("Computer", filtered_computer_options, default=filtered_computer_options)

            # Year filter
            years = [d.year for d in df["Date"]]
            df["Year"] = years
            years_unique = sorted(set(years))
            selected_years = st.multiselect("Year", years_unique, default=years_unique)

            # Y-axis selection
            y_options = [
                'Number of two-qubit gates',
                'Number of single-qubit gates',
                'Total number of gates',
                'Circuit depth'
            ]
            y_axis = st.selectbox("Vertical axis", y_options)

            # B-axis selection
            b_options = [
                'Date (more recent = larger)',
                'Number of qubits',
                'Number of two-qubit gates',
                'Number of single-qubit gates',
                'Total number of gates',
                'Circuit depth',
                'Equal size'
                
            ]
            b_axis = st.selectbox("Marker size", b_options)
         
            if b_axis == 'Date (more recent = larger)':
                dates = [d for d in df.Date]
                date_min = min(dates)
                date_max = max(dates)
                df["bubble_size"] = dates
                df['bubble_size'] = df['bubble_size'].apply(lambda x: (x - date_min).days / (date_max - date_min).days if pd.notnull(x) else None)

                # Scale to a desired range (e.g., 10–60)
                df['bubble_size'] = df['bubble_size'] * 50 + 10  # range from 10 to 60
                b_axis = 'bubble_size'

            col5,col6 = st.columns(2)

            with col5:
                x_axis_scale = st.selectbox("Horizontal axis scale", ["Linear", "Log"], index=0)
            with col6:
                y_axis_scale = st.selectbox("Vertical axis scale", ["Linear", "Log"], index=0)
        
        # Filter DataFrame
        filtered_df = df[
            (df['Institution'].isin(selected_comps)) &
            (df['Computer'].isin(selected_computers)) &
            (df['Year'].isin(selected_years)) 
        ]

        if b_axis != 'Equal size':
            filtered_df = filtered_df.dropna(subset=[b_axis])
            graph_df = filtered_df.copy()
            bubble_index = graph_df.columns.get_loc(b_axis)
            min_value = graph_df.iloc[:, bubble_index].min()
            max_value = graph_df.iloc[:, bubble_index].max()
            min_value = 0 if pd.isna(min_value) else min_value
            max_value = 0 if pd.isna(max_value) else max_value

            bubble_index = int(bubble_index)
            min_value = float(min_value) if min_value is not None else 0
            max_value = float(max_value) if max_value is not None else 0
            b_size = [50,120]
        else:
            graph_df = filtered_df.copy()
            bubble_index = graph_df.columns.get_loc('Date')
            min_value = 50
            max_value = 50
            b_size = [50,50]

        # Assume filtered_df, y_axis, b_axis are already defined
        with plot_column:
            # if x_axis_scale == 'Log':
            #     graph_df['Number of qubits'] = np.log(graph_df['Number of qubits'].replace(0, np.nan).dropna())
            # if y_axis_scale == 'Log':
            #     graph_df[y_axis] = np.log(graph_df[y_axis].replace(0, np.nan).dropna())

            graph_df["Date"] = graph_df["Date"].astype(str)
            graph_df["_id"] = [str(id) for id in graph_df["_id"]]
            graph_df = graph_df.fillna('')
            
            x_index = graph_df.columns.get_loc("Number of qubits")
            y_index = graph_df.columns.get_loc(y_axis)
            
            graph_df["Comp_Inst"] = graph_df["Institution"] + " " + graph_df["Computer"]
            computers = list(graph_df["Comp_Inst"].unique())

            comp_index = graph_df.columns.get_loc("Comp_Inst")

            option = {
                "dataset": [
                    {"source": [graph_df.columns.tolist()] + graph_df.values.tolist()}
                ] + [
                    {"transform": {"type": "filter", "config": {"dimension": comp_index, "eq": i}}}
                    for i in computers
                ],
                "title": {
                    "left": "center"
                },
                "legend": {"data": computers, "bottom": 1},
                "tooltip": {"trigger": "item","confine":True,"appendToBody":True},
                "xAxis": {"type": "log" if x_axis_scale == "Log" else "value", "splitLine": {"lineStyle": {"type": "dashed"}},"min": 1,
                          "name": "Number of qubits",         
                          "nameLocation": "middle",          
                          "nameGap": 30 ,
                           "axisLabel": {
            "formatter": JsCode(
                # one-line JS required
                "function (val) { var e = Math.log10(val); var map = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹','-':'⁻'}; return '10' + e.toString().split('').map(function(c){return map[c]||c}).join(''); }"
            ).js_code if x_axis_scale == "Log" else "{value}"  # this makes labels show as powers of 10
        }
   },
                "yAxis": {"type": "log" if y_axis_scale == "Log" else "value", "splitLine": {"lineStyle": {"type": "dashed"}},"min": 1,
                          "name": y_axis,         
                         "nameLocation": "middle",          
                         "nameGap": 50 ,
                          "axisLabel": {
            "formatter": JsCode(
                # one-line JS required
                "function (val) { var e = Math.log10(val); var map = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹','-':'⁻'}; return '10' + e.toString().split('').map(function(c){return map[c]||c}).join(''); }"
            ).js_code if y_axis_scale == "Log" else "{value}"  # this makes labels show as powers of 10
        }
                    
                       
   },
                "visualMap": {
                    "show": False,
                    "dimension": bubble_index,
                    "min": min_value,
                    "max": max_value,
                    "seriesIndex": list(range(len(computers))),
                    "inRange": {"symbolSize": b_size}
                },
                "series": [
                    {
                        "name": comp,
                        "type": "scatter",
                        "datasetIndex": idx + 1,  # important: dataset index matches filter
                        "encode": {"x": x_index, "y": y_index, "tooltip": [1, 2,4, 5,6,7,8,9,10,11,14]}
                    }
                    for idx, comp in enumerate(computers)
                ]
            }

            last_row = st.container()
            clicked_id = None
            
            
            clicked_id = st_echarts(
                option,
                events={
                    "click": "function(params) { return params.value[0]; }" ,
                    "dblclick": "function(params) { return params.value[1]; }" 

                },
                height="500px",
                key="global",
            )

            

            if clicked_id is not None and isinstance(clicked_id, int):
                st.session_state.clicked_id = clicked_id

            if clicked_id is not None and isinstance(clicked_id, int):
                # Inject CSS to make Streamlit button green
                st.markdown(
                    """
                    <style>
                     div.stButton > button:first-child {
                        background-color: #FF4B4B;
                        color: white;
                        border-radius: 5px;
                      
                    }
                    div.stButton > button:first-child:hover {
                        background-color: #45a049;
                        color: white;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                update_ref = graph_df.loc[graph_df["_id"]==st.session_state.clicked_id,"Reference"].values[0]

                if last_row.button(f"Update data for reference {update_ref}"):
                    ts = int(time.time() * 1000)
                    html(f"<script>{switch(3)} // trigger for id {clicked_id} at {ts}</script>", height=0)
            elif clicked_id is not None and isinstance(clicked_id,str):
                st.components.v1.html(
                    f"""
                    <script>
                        window.open("{clicked_id}", "_blank");
                    </script>
                    """,
                    height=0
                )
    
    # The tab for submitting a new datapoint.
    with submit_tab:
        institutions = list(df["Institution"].unique())

        #st.header("Submit Quantum Datapoint")

        
        # CAPTCHA Verification First
        if 'controllo' not in st.session_state:
            st.session_state['controllo'] = False
      
        if st.session_state['controllo'] == False:
            st.markdown("Confirm humanity")

            selection_column, plot_column = st.columns([1, 1])

            if 'Captcha' not in st.session_state:
                st.session_state['Captcha'] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length_captcha))

            image = ImageCaptcha(width=width, height=height)
            data = image.generate(st.session_state['Captcha'])
            selection_column.image(data)

            captcha_input = plot_column.text_area('Enter captcha text', height=30)

            if st.button("Verify"):
                if st.session_state['Captcha'].lower() == captcha_input.strip().lower():
                    del st.session_state['Captcha']
                    st.session_state['controllo'] = True
                    st.rerun()
                else:
                    st.error("🚨 Invalid Captcha")
                    del st.session_state['Captcha']
                    st.rerun()

            #st.stop()  # Stop here until CAPTCHA is verified

        # Only show the form if CAPTCHA passed
        
        elif st.session_state['controllo'] == True:
            st.markdown("""
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
        """, unsafe_allow_html=True)
            
            st.markdown("Highlighted fields are required.")

            st.markdown('<div class="green-label">Reference</div>', unsafe_allow_html=True)
            reference = st.text_input(label='', key="reference_input", help = "The reference for the quantum computation, typically an arXiv or journal link")

            st.markdown('<div class="black-label">Experiment Date</div>', unsafe_allow_html=True)
            date = st.date_input("", value=datetime.today(), help="The date the experiment was performed or published (typically the date of the reference)")
            date = datetime(date.year, date.month, date.day)  # Convert from datetime.date to datetime.datetime.
            
            st.markdown('<div class="black-label">Computation (comma-separated list)</div>', unsafe_allow_html=True)
            computation_raw = st.text_area("", help="The algorithm used/computation performed, for example Trotter, VQE, Phase estimation")

            # st.markdown('<div class="black-label">Error Mitigation (comma-separated list)</div>', unsafe_allow_html=True)
            # error_mitigation_raw = st.text_area("", help="e.g. ZNE, Clifford Data Regression")

            st.markdown('<div class="green-label">Number of Qubits</div>', unsafe_allow_html=True)
            num_qubits_raw = st.text_input("", help = "Number of qubits used in the quantum computation")
            num_qubits = int(num_qubits_raw) if num_qubits_raw.strip().isdigit() else None

            st.markdown('<div class="black-label">Number of Two-Qubit Operations</div>', unsafe_allow_html=True)
            num_2q_gates_raw = st.text_input("", help = "Number of two-qubit operations used in the quantum computation")
            num_2q_gates = int(num_2q_gates_raw) if num_2q_gates_raw.strip().isdigit() else None

            st.markdown('<div class="black-label">Number of Single-Qubit Operations</div>', unsafe_allow_html=True)
            num_1q_gates_raw = st.text_input("", help = "Number of siingle-qubit operations used in the quantum computation")
            num_1q_gates = int(num_1q_gates_raw) if num_1q_gates_raw.strip().isdigit() else None

            st.markdown('<div class="black-label">Total Number of Operations</div>', unsafe_allow_html=True)
            total_gates_raw = st.text_input("",help = "Total number of operations used in the quantum computation, e.g. single-qubit operations + two-qubit operations")
            total_gates = int(total_gates_raw) if total_gates_raw.strip().isdigit() else None

            st.markdown('<div class="black-label">Circuit Depth</div>', unsafe_allow_html=True)
            circuit_depth_raw = st.text_input("", help = "The depth of the circuit in the quantum computation (see Circuit Depth Measure).")
            circuit_depth = int(circuit_depth_raw) if circuit_depth_raw.strip().isdigit() else None

            st.markdown('<div class="black-label">Circuit Depth Measure</div>', unsafe_allow_html=True)
            cdm_options = list(df["Circuit depth measure"].unique())
            try:  
                selected_cdm = st.selectbox(
                    "",
                    options=cdm_options + ["Other"],
                    index=0,
                    help="The measure/metric used for circuit depth, for example two-qubit gate layers, Trotter step, etc. Number of two-qubit operations and/or total number of operations is preferred to this metric, and this should be used only when these are unknown."
                )
                if selected_cdm == "Other":
                    raise TypeError("Type Manually")
                else:
                    circuit_depth_measure = selected_cdm
            except: 
                circuit_depth_measure = st.text_input(
                    "Enter Circuit depth measure manually:",
                    help="The measure/metric used for circuit depth, for example two-qubit gate layers, Trotter step, etc. Number of two-qubit operations and/or total number of operations is preferred to this metric, and this should be used only when these are unknown."
                )

            st.markdown('<div class="green-label">Institution</div>', unsafe_allow_html=True)
            try:  
                selected = st.selectbox(
                    "",
                    options=institutions + ["Other"],
                    index=0,
                    help="Who owns the quantum computer, e.g. Google, Quantinuum, QuEra"
                )
                if selected == "Other":
                    raise TypeError("Type Manually")
                else:
                    institution = selected
            except: 
                institution = st.text_input(
                    "Enter Institution manually:",
                    help="Who owns the quantum computer, e.g. Google, Quantinuum, QuEra"
                )

            
            
            st.markdown('<div class="green-label">Computer</div>', unsafe_allow_html=True)
            if selected != "Other":
                computers = list(df[df["Institution"]== institution]["Computer"].unique())
                selected_comp = st.selectbox("",options = computers+["Other"],index=0,help ="The name or other identifying label for the quantum computer")
                try:
                    if selected_comp == "Other":
                        raise TypeError("Type Manually")
                    else:
                        computer = selected_comp
                except:
                    computer = st.text_input(
                    "Enter Computer manually:",
                    help="The name or other identifying label for the quantum computer"
                )
            else:
                
                computer = st.text_input(
                    "Enter Computer manually:",
                    help="The name or other identifying label for the quantum computer"
                )

            
            submit = st.button("Submit")
        
            if st.session_state.get("submission_success"):
                st.success("Quantum datapoint submitted successfully!")
                del st.session_state["submission_success"]
            
            error_count_new = 0
            if submit:
                if not reference:
                    error_count_new+=1
                    st.error("Please fill out Reference(url or citation) as it is a required field. ")
                if not num_qubits:
                    error_count_new+=1
                    st.error("Please fill out Number of Qubits as it is a required field. ")
                if not institution:
                    error_count_new+=1
                    st.error("Please fill out Institution as it is a required field. ")
                if not computer:
                    error_count_new+=1
                    st.error("Please fill out Computer as it is a required field. ")
                if not (num_2q_gates or total_gates):
                    error_count_new+=1
                    st.error("Please fill either Number of two-Qubit operations or Total Number of Operations")
                
                if error_count_new==0:
                    computation_list = [x.strip() for x in computation_raw.split(",") if x.strip()]
                    success = insert_quantum_datapoint(
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
                        status="pending"  # TODO: Don't hardcode.
                    )
                
                    if success:
                        st.success("Quantum datapoint submitted successfully!")
                        #st.session_state['controllo'] = False
                        
                        st.session_state.submission_success = True
                        st.rerun()

    # The tab for updating a datapoint.
    with update_tab:

        
        if st.session_state.clicked_id is None:
            st.subheader("Please provide the necessary details…")
            update_id = df.iloc[0]["_id"]
        else:
            st.subheader("Please provide the necessary details…")
            update_id = st.session_state.clicked_id
            st.session_state.visited = 1
        
        
        record = df[df['_id'] == update_id]

        if not record.empty:
        
            record = record.iloc[0]

            new_ref = st.text_input("Reference",value = record["Reference"],help = "The reference for the quantum computation, typically an arXiv or journal link")
            new_date = st.date_input("Date", value=record['Date'])
            new_qubits = st.number_input("Number of Qubits", value=int(record['Number of qubits']), help = "Number of qubits used in the quantum computation")

            try:
                num_2q_gates_raw = st.text_input("Number of Two-Qubit Gates", value=record['Number of two-qubit gates'], help = "Number of two-qubit operations used in the quantum computation")
                new_num_2q_gates = float(num_2q_gates_raw) if num_2q_gates_raw and not is_nan_or_nan_string(num_2q_gates_raw) else None
            except:
                st.error("Invalid input. Please input a valid number")
                

            try:
                num_1q_gates_raw = st.text_input("Number of Single-Qubit Gates", value=record['Number of single-qubit gates'], help = "Number of single-qubit operations used in the quantum computation")
                new_num_1q_gates = float(num_1q_gates_raw) if num_1q_gates_raw and not is_nan_or_nan_string(num_1q_gates_raw) else None
            except:
                st.error("Invalid input. Please input a valid number")
                

            try:
                total_gates_raw = st.text_input("Total number of gates", value=record['Total number of gates'], help = "Total number of operations used in the quantum computation, e.g. single-qubit operations + two-qubit operations")
                new_total_gates = float(total_gates_raw) if total_gates_raw and not is_nan_or_nan_string(total_gates_raw) else None
            except:
                st.error("Invalid input. Please input a valid number")
                
            try:
                circuit_depth_raw = st.text_input("Circuit depth", value=record['Circuit depth'], help = "The depth of the circuit in the quantum computation (see Circuit Depth Measure).")
                new_circuit_depth = float(circuit_depth_raw) if circuit_depth_raw and not is_nan_or_nan_string(circuit_depth_raw) else None
            except:
                st.error("Invalid input. Please input a valid number")
                
            new_circuit_depth_measure = st.text_input("Circuit depth measure", value=record['Circuit depth measure'], help="The measure/metric used for circuit depth, for example two-qubit gate layers, Trotter step, etc. Number of two-qubit operations and/or total number of operations is preferred to this metric, and this should be used only when these are unknown. ")
            new_institution = st.text_input("Institution", value=record['Institution'], help="Who owns the quantum computer, e.g. Google, Quantinuum, QuEra")
            new_computation = st.text_input("Computation", value=record['Computation'], help="e.g. QFT, Measurement")
            new_computer = st.text_input("Computer", value=record['Computer'], help="The name or other identifying label for the quantum computer")
            #new_mitigation = st.text_input("Error Mitigations", value=record['Error mitigations'], help="e.g. ZNE, Clifford Data Regression")
            new_feedback = st.text_input("Justification for changes", value=record.get('feedback'), help="Clear description of the changes made with justification. For example: “Changed the number of two-qubit operations from 512 to 1024. The correct number (1024 two-qubit operations) is stated in the caption of Figure 1 of the reference.")

            computation_list = [x.strip() for x in new_computation.split(",") if x.strip()]
            #error_mitigation_list = [x.strip() for x in new_mitigation.split(",") if x.strip()]

            # --- CAPTCHA ---
            col3, col4 = st.columns(2)

            if "update_captcha" not in st.session_state:
                st.session_state.update_captcha = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length_captcha))

            image1 = ImageCaptcha(width=width, height=height)
            data1 = image1.generate(st.session_state.update_captcha)
            col3.image(data1)

            captcha_input1 = col4.text_area('Enter the captcha text', height=30)

            error_count = 0

            if st.button("Verify humanity and submit"):
                if st.session_state.update_captcha.lower() == captcha_input1.strip().lower():
                    if not new_ref:
                        error_count +=1
                        st.error("Please fill out Reference(url or citation) as it is a required field. ")
                    if not new_qubits:
                        error_count +=1
                        st.error("Please fill out Number of Qubits as it is a required field. ")
                    if not (new_num_2q_gates or new_total_gates):
                        error_count +=1
                        st.error("Please fill either Number of two-Qubit operations or Total Number of Operations")
                    if not new_institution:
                        error_count +=1
                        st.error("Please fill out Institution as it is a required field. ")
                    if not new_computer:
                        error_count +=1
                        st.error("Please fill out Computer as it is a required field. ")
                    if not new_feedback:
                        error_count +=1
                        st.error("Please fill out Justification for changes as it is a required field. ")
                    
                    #if reference and num_qubits and (num_2q_gates or total_gates):
                    if error_count==0:
                        collection = get_collection()
                        # TODO: Should this be insserting or updating? I beleive this is updating, so use find_one_and_update.
                        collection.insert_one({
                            "Reference": new_ref,
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
                            "status": "UPDATE REQUESTED",
                            "feedback": new_feedback,
                        })
                        st.success(f"Update request submitted: {record['Reference']}")
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
            if check_credentials(admin_user, admin_pass):
                st.success("✅ Admin login successful!")
                st.markdown("Welcome to the admin dashboard.")
                st.session_state.logged_in = 'admin'
                #login_button = st.form_submit_button('Go to App')
                st.rerun()
            # Add your admin dashboard code here
            else:
                st.error("❌ Invalid credentials.")


# Main logic
# if st.session_state.logged_in == 'refresh':
#     #show_user_app()
#     show_login_form()
if st.session_state.logged_in == 'app':
    #show_user_app()
    show_app()
elif st.session_state.logged_in == 'admin':
    show_admin_page()
else:
    show_app()
