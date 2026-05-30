import streamlit as st
import pandas as pd

from triage_utils import(
    create_triage_queue,
    get_urgent_cases,
    get_pathologist_review_cases,
    get_imager_qc_review_cases,
    format_workflow_label,
    format_column_label
)

from qc_detector import assign_qc_flag

INPUT_FILE = "data/raw/cytology_cases.csv"

st.title("Cytology Workflow Dashboard")

cases = pd.read_csv(INPUT_FILE)

triage_queue = create_triage_queue(cases)

triage_queue["qc_flag"] = triage_queue.apply(
    lambda row: assign_qc_flag(
        row["blur_score"],
        row["artifact_risk_score"]
    ),
    axis=1
)

urgent_cases = get_urgent_cases(triage_queue)
pathologist_cases = get_pathologist_review_cases(triage_queue)
imager_qc_review_cases = get_imager_qc_review_cases(triage_queue)

st.subheader("Daily Workflow Metrics")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Cases", len(triage_queue))
col2.metric("Urgent Cases", len(urgent_cases))
col3.metric("Pathologist Review", len(pathologist_cases))
col4.metric("Imager QC Review", len(imager_qc_review_cases))

st.subheader("Workflow Distribution")

workflow_distribution = (
    triage_queue["needs_attention"]
    .apply(format_workflow_label)
    .value_counts()
)

st.bar_chart(workflow_distribution)

st.subheader("Workflow Queue")

workflow_view = st.selectbox(
    "Select Workflow View",
    [
        "All Cases",
        "Immediate Attention",
        "Pathologist Review",
        "Routine",
    ]
)

qc_view = st.selectbox(
    "Select Imager QC View",
    [
        "All Imager QC States",
        "Imager QC Review",
        "Imager QC Pass"
    ]
)

if workflow_view == "Immediate Attention":
    filtered_queue = triage_queue[
        triage_queue["needs_attention"] == "immediate_attention"
    ]

elif workflow_view == "Pathologist Review":
    filtered_queue = triage_queue[
        triage_queue["needs_attention"] == "pathologist_review"
    ]

elif workflow_view == "Routine":
    filtered_queue = triage_queue[
        triage_queue["needs_attention"] == "routine"
    ]

else:
    filtered_queue = triage_queue

if qc_view == "Imager QC Review":
    filtered_queue = filtered_queue[
        filtered_queue["qc_flag"] == "imager_qc_review"
    ]

elif qc_view == "Imager QC Pass":
    filtered_queue = filtered_queue[
        filtered_queue["qc_flag"] == "imager_qc_pass"
    ]

display_queue = filtered_queue.copy()

display_queue["needs_attention"] = (
    display_queue["needs_attention"]
    .apply(format_workflow_label)
)

display_queue["qc_flag"] = (
    display_queue["qc_flag"]
    .apply(format_workflow_label)
)

display_value_columns = [
    "adequacy",
    "scan_status",
    "diagnosis",
]

for column in display_value_columns:
    display_queue[column] = (
        display_queue[column]
        .apply(format_workflow_label)
    )

display_columns = {}

for column in display_queue.columns:
    display_columns[column] = format_column_label(column)

display_queue = display_queue.rename(columns=display_columns)

st.dataframe(display_queue)
