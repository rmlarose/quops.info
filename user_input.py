from datetime import datetime
import random
import string

from captcha.image import ImageCaptcha
import numpy as np
import streamlit as st

import database


def get_user_input(update: bool = False):
    all_data = database.get_dataframe(filter={database.STATUS: database.Status.APPROVED})

    REQUIRED_KEY: str = "*"
    st.markdown(f"({REQUIRED_KEY} = required)")

    with st.container(border=True):
        reference_column, date_column = st.columns([2, 1])
        with reference_column:
            if not update:
                reference = st.text_input(
                    label=database.REFERENCE + REQUIRED_KEY,
                    value="",
                    placeholder="The reference for the quantum computation, typically an arXiv or journal link.",
                )
            else:
                reference = st.selectbox(
                    label=database.REFERENCE + REQUIRED_KEY,
                    options=sorted(all_data[database.REFERENCE]),
                    index=0,
                    placeholder="The reference for the quantum computation, typically an arXiv or journal link."
                )
                record = all_data[all_data[database.REFERENCE] == reference]
                record = record.iloc[0]
        with date_column:
            date = st.date_input(
                label=database.DATE + REQUIRED_KEY,
                value=record[database.DATE] if update else datetime.today(),
                help="The date the experiment was performed or published (typically the date of the reference).",
            )
            date = datetime(date.year, date.month, date.day)

    with st.container(border=True):
        institution_column, computer_column = st.columns([1, 1])
        with institution_column:
            institutions = sorted(all_data[database.INSTITUTION].unique())
            try:
                selected = st.selectbox(
                    database.INSTITUTION + REQUIRED_KEY,
                    options=institutions + ["Other"],
                    index=institutions.index(record[database.INSTITUTION]) if update else None,
                    placeholder="Who owns the quantum computer, e.g. Google, Quantinuum, or QuEra.",
                )
                if selected == "Other":
                    raise TypeError("Type Manually")
                else:
                    institution = selected
            except:
                institution = st.text_input(
                    database.INSTITUTION + REQUIRED_KEY,
                    placeholder="Type new institution",
                )
        
        with computer_column:
            if selected != "Other":
                computers = list(
                    all_data[all_data[database.INSTITUTION] == institution][
                        database.COMPUTER
                    ].unique()
                )
                selected_comp = st.selectbox(
                    database.COMPUTER + REQUIRED_KEY,
                    options=computers + ["Other"],
                    index=computers.index(record[database.COMPUTER]) if update else None,
                    placeholder="The name or other identifying label for the quantum computer",
                )
                try:
                    if selected_comp == "Other":
                        raise TypeError("Type Manually")
                    else:
                        computer = selected_comp
                except:
                    computer = st.text_input(
                        database.COMPUTER + REQUIRED_KEY,
                        placeholder="Type new computer.",
                    )
            else:
                computer = st.text_input(
                    database.COMPUTER + REQUIRED_KEY,
                    placeholder="Type new computer.",
                )

    with st.container(border=True):
        num_qubits = st.number_input(
            database.NUMBER_OF_QUBITS + REQUIRED_KEY,
            value=record[database.NUMBER_OF_QUBITS] if update else None,
            placeholder="Number of qubits used in the quantum computation",
            step=1,
        )

    with st.container(border=True):
        st.text("At least one of the following rows is required" + REQUIRED_KEY)

        num_2q_gates = st.number_input(
            label=database.NUMBER_OF_TWO_QUBIT_GATES,
            value=int(record[database.NUMBER_OF_TWO_QUBIT_GATES]) if update and not np.isnan(record[database.NUMBER_OF_TWO_QUBIT_GATES]) else None,
            placeholder="Number of two-qubit gates used in the quantum computation",
            step=1,
        )
        total_gates = st.number_input(
            database.TOTAL_NUMBER_OF_GATES,
            value=int(record[database.TOTAL_NUMBER_OF_GATES]) if update and not np.isnan(record[database.TOTAL_NUMBER_OF_GATES]) else None,
            placeholder="Total number of gates used in the quantum computation",
            step=1,
        )

        circuit_depth_column, circuit_depth_measure_column = st.columns([1, 1])
        with circuit_depth_column:
            circuit_depth = st.number_input(
                database.CIRCUIT_DEPTH,
                value=int(record[database.CIRCUIT_DEPTH]) if update and not np.isnan(record[database.CIRCUIT_DEPTH]) else None,
                placeholder="The depth of the circuit in the quantum computation.",
                step=1,
            )

        with circuit_depth_measure_column:
            cdm_options = list(all_data[database.CIRCUIT_DEPTH_MEASURE].dropna().unique())
            try:
                selected_cdm = st.selectbox(
                    database.CIRCUIT_DEPTH_MEASURE,
                    options=cdm_options + ["Other"],
                    index=cdm_options.index(record[database.CIRCUIT_DEPTH_MEASURE]) if update else None,
                    placeholder="The measure/metric used for circuit depth, for example two-qubit gate layers, Trotter step, etc.",
                )
                if selected_cdm == "Other":
                    raise TypeError("Type Manually")
                else:
                    circuit_depth_measure = selected_cdm
            except:
                circuit_depth_measure = st.text_input(
                    database.CIRCUIT_DEPTH_MEASURE,
                    placeholder="The measure/metric used for circuit depth, for example two-qubit gate layers, Trotter step, etc.",
                )

    num_1q_gates = st.number_input(
        database.NUMBER_OF_ONE_QUBIT_GATES,
        value=int(record[database.NUMBER_OF_ONE_QUBIT_GATES]) if update and not np.isnan(record[database.NUMBER_OF_ONE_QUBIT_GATES]) else None,
        placeholder="Number of single-qubit gates used in the quantum computation",
        step=1,
    )
    computation_raw = st.text_input(
        label=database.COMPUTATION,
        value=record[database.COMPUTATION] if update else None,
        placeholder="The computation performed, e.g. Trotter. If multiple, use a comma-separated list, e.g. VQE, Phase estimation",
    )
    
    if update:
        comments = st.text_input(
            label="Justification for changes" + REQUIRED_KEY,
            value=None,
            placeholder="Clear description of the changes made with justification. For example: 'Changed the number of two-qubit operations from 512 to 1024. The correct number (1024 two-qubit operations) is stated in the caption of Figure 1 of the reference.'",
        )
    # return reference, date, institution, computer, num_qubits, num_2q_gates, total_gates, circuit_depth, circuit_depth_measure, num_1q_gates, computation_raw

    if not update:
        submit = st.button("Submit")
    
    else:
        col3, col4 = st.columns(2)

        if "update_captcha" not in st.session_state:
            st.session_state.update_captcha = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=4)
            )

        image1 = ImageCaptcha(width=200, height=150)
        data1 = image1.generate(st.session_state.update_captcha)
        col3.image(data1)

        captcha_input1 = col4.text_area("Enter the captcha text", height=30)
        submit = st.button("Verify humanity and submit")

    # if st.session_state.get("submission_success"):
    #     st.success(
    #         "Datapoint submitted successfully and is pending admin approval - thanks for contributing to QuOps.Info!"
    #     )
    #     del st.session_state["submission_success"]

    error_count = 0
    if submit:
        if not reference:
            error_count += 1
            st.error(f"{database.REFERENCE} is required.")
        if not num_qubits:
            error_count += 1
            st.error(f"{database.NUMBER_OF_QUBITS} is required.")
        if not institution:
            error_count += 1
            st.error(f"{database.INSTITUTION} is required.")
        if not computer:
            error_count += 1
            st.error(f"{database.COMPUTER} is required.")
        if not (num_2q_gates or total_gates or (circuit_depth and circuit_depth_measure)):
            error_count += 1
            st.error(
                f"{database.NUMBER_OF_TWO_QUBIT_GATES} OR {database.TOTAL_NUMBER_OF_GATES} OR ({database.CIRCUIT_DEPTH} AND {database.CIRCUIT_DEPTH_MEASURE}) is required."
            )
        if update and comments is None:
            error_count += 1
            st.error(f"Justification for changes is required.")
        
        if update:
            if (
                st.session_state.update_captcha.lower()
                != captcha_input1.strip().lower()
            ):
                error_count += 1  # TODO: Is this necessary?
                st.error("🚨 Invalid Captcha")
                del st.session_state.update_captcha
                st.rerun()

        if error_count == 0:
            computation_list = [
                x.strip() for x in computation_raw.split(",") if x.strip()
            ]

            to_return = [reference, date, institution, computer, num_qubits, num_2q_gates, total_gates, circuit_depth, circuit_depth_measure, num_1q_gates, computation_list]

            if update:
                to_return.append(comments)
            
            return tuple(to_return)

            # datapoint_inserted = database.insert_datapoint(
            #     reference=reference,
            #     date=date,
            #     computation=computation_list,
            #     num_qubits=num_qubits,
            #     num_2q_gates=num_2q_gates,
            #     num_1q_gates=num_1q_gates,
            #     total_gates=total_gates,
            #     circuit_depth=circuit_depth,
            #     circuit_depth_measure=circuit_depth_measure,
            #     institution=institution,
            #     computer=computer,
            #     status=database.Status.PENDING,
            # )

            # if datapoint_inserted:
            #     st.success("Datapoint submitted successfully and pending admin approval - thanks for contributing to QuOps.Info!")

            #     st.session_state.submission_success = True
            #     st.rerun()
