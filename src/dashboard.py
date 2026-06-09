import streamlit as st
import pandas as pd
from datetime import datetime

from triage_utils import(
    create_triage_queue,
    get_urgent_cases,
    get_pathologist_review_cases,
    get_imager_qc_review_cases,
    format_workflow_label,
    format_column_label,
    create_summary_metrics,
    create_workflow_alerts,
    interpret_workload,
    validate_case_data,
)

from qc_detector import assign_qc_flag

INPUT_FILE = "data/raw/cytology_cases.csv"

st.title("Cytology Workflow Dashboard")

st.caption(
    f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)

uploaded_file = st.sidebar.file_uploader(
    "Upload Cytology Case CSV",
    type=["csv"]
)

if uploaded_file is not None:
    st.sidebar.success("Uploaded CSV Loaded")
    cases = pd.read_csv(uploaded_file)
else:
    st.sidebar.info("Using Default Sample Dataset")
    cases = pd.read_csv(INPUT_FILE)

try:
    validate_case_data(cases)
except ValueError as error:
    st.error(error)
    st.stop()

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

summary = create_summary_metrics(
    triage_queue,
    urgent_cases,
    pathologist_cases,
)

workflow_alerts = create_workflow_alerts(summary)

workload_interpretations = interpret_workload(summary)

with st.sidebar:
    st.header("Workflow Summary")

    st.write(f"Total Cases: {len(triage_queue)}")
    st.write(f"Urgent Cases: {len(urgent_cases)}")
    st.write(f"Pathologist Review: {len(pathologist_cases)}")
    st.write(f"Imager QC Review: {len(imager_qc_review_cases)}")
    st.write(f"Overdue Cases: {summary['overdue_cases']}")

    st.divider()

    st.write("Current Workflow Status")

display_value_columns = [
    "adequacy",
    "scan_status",
    "diagnosis",
]

overview_tab, queue_tab, qc_tab, turnaround_tab = st.tabs(
    [
        "Overview",
        "Operational Queue",
        "QC Analytics",
        "Turnaround Analytics",
    ]
)

with overview_tab:
    st.subheader("Daily Workflow Metrics")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Cases", len(triage_queue))
    col2.metric("Urgent Cases", len(urgent_cases))
    col3.metric("Pathologist Review", len(pathologist_cases))
    col4.metric("Imager QC Review", len(imager_qc_review_cases))
    col5.metric("Overdue Cases", summary["overdue_cases"])

    st.subheader("Operational Alerts")

    if workflow_alerts:
        for alert in workflow_alerts:
            st.warning(alert)

    st.subheader("Workload Interpretation")

    for interpretation in workload_interpretations:
        st.info(interpretation)

with st.sidebar:
    for interpretation in workload_interpretations:
        st.write(f"- {interpretation}")

    st.divider()
    st.subheader("Workflow Filters")

    workflow_view = st.selectbox(
        "Select Workflow View",
        [
            "All Cases",
            "Immediate Attention",
            "Pathologist Review",
            "Routine",
            "Overdue Cases",
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

def highlight_priority(row):
    if row["Needs Attention"] == "Immediate Attention":
        return ["background-color: #ffe6e6"] * len(row)

    if row["Diagnosis"] == "HSIL":
        return ["background-color: #fff4cc"] * len(row)

    if row["Turnaround Days"] > 5:
        return ["background-color: #e6f0ff"] * len(row)

    return [""] * len(row)

with overview_tab:  
    st.subheader("High Priority Cases")

    high_priority_cases = triage_queue[
        triage_queue["priority"] <= 5
    ]

    high_priority_display = high_priority_cases.copy()

    high_priority_display["needs_attention"] = (
        high_priority_display["needs_attention"]
        .apply(format_workflow_label)
    )

    high_priority_display["qc_flag"] = (
        high_priority_display["qc_flag"]
        .apply(format_workflow_label)
    )

    for column in display_value_columns:
        high_priority_display[column] = (
            high_priority_display[column]
            .apply(format_workflow_label)
        )

    high_priority_columns = {}

    for column in high_priority_display.columns:
        high_priority_columns[column] = format_column_label(column)

    high_priority_display = high_priority_display.rename(
        columns=high_priority_columns
    )

    high_priority_display = high_priority_display.sort_values(
        by="Priority"
    )

    st.caption(
        f"Showing {len(high_priority_display)} High Priority Cases"
    )

    styled_high_priority_display = high_priority_display.style.apply(
        highlight_priority,
        axis=1
    )

    st.dataframe(styled_high_priority_display)

with overview_tab:
    st.subheader("Overview Analytics")
        
    with st.expander("Workflow Distribution", expanded=False):
        workflow_distribution = (
            triage_queue["needs_attention"]
            .apply(format_workflow_label)
            .value_counts()
        )

        st.bar_chart(workflow_distribution)

    with st.expander("Diagnosis Distribution", expanded=False):
        diagnosis_distribution = (
            triage_queue["diagnosis"]
            .apply(format_workflow_label)
            .value_counts()
        )

        st.bar_chart(diagnosis_distribution)

with qc_tab:
    st.subheader("Imager QC Analytics")

    qc_col1, qc_col2 = st.columns(2)

    qc_col1.metric(
        "QC Review Cases",
        summary["imager_qc_review_cases"]
    )

    qc_col2.metric(
        "QC Review %",
        f"{summary['imager_qc_review_pct']:.1f}%"
    )

    qc_distribution = (
        triage_queue["qc_flag"]
        .apply(format_workflow_label)
        .value_counts()
    )

    st.bar_chart(qc_distribution)

with turnaround_tab:
    st.subheader("Turnaround Analytics")

    tat_col1, tat_col2, tat_col3, tat_col4 = st.columns(4)

    tat_col1.metric(
        "Average Turnaround",
        summary["average_turnaround_days"]
    )

    tat_col2.metric(
        "Longest Turnaround",
        summary["longest_turnaround_days"]
    )

    tat_col3.metric(
        "Overdue Cases",
        summary["overdue_cases"]
    )

    tat_col4.metric(
        "Aging Cases",
        summary["aging_cases"]
    )

    st.write("Turnaround Time Distribution")

    turnaround_distribution = (
        triage_queue["turnaround_days"]
        .value_counts()
        .sort_index()
    )

    st.bar_chart(turnaround_distribution)

    st.write("Case Aging Distribution")

    case_age_distribution = (
        triage_queue["case_age_flag"]
        .apply(format_workflow_label)
        .value_counts()
    )

    st.bar_chart(case_age_distribution)

with queue_tab:

    st.subheader("Workflow Queue")

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

    elif workflow_view == "Overdue Cases":
        filtered_queue = triage_queue[
            triage_queue["case_age_flag"] == "overdue"
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

    queue_col1, queue_col2, queue_col3 = st.columns(3)

    queue_col1.metric(
        "Displayed Cases",
        len(filtered_queue)
    )

    queue_col2.metric(
        "Immediate Attention",
        len(
            filtered_queue[
                filtered_queue["needs_attention"] == "immediate_attention"
            ]
        )
    )

    queue_col3.metric(
        "Overdue",
        len(
            filtered_queue[
                filtered_queue["case_age_flag"] == "overdue"
            ]
        )
    )

    display_queue["needs_attention"] = (
        display_queue["needs_attention"]
        .apply(format_workflow_label)
    )

    display_queue["qc_flag"] = (
        display_queue["qc_flag"]
        .apply(format_workflow_label)
    )

    for column in display_value_columns:
        display_queue[column] = (
            display_queue[column]
            .apply(format_workflow_label)
        )

    display_columns = {}

    for column in display_queue.columns:
        display_columns[column] = format_column_label(column)

    display_queue = display_queue.rename(columns=display_columns)

    case_search = st.text_input(
        "Search Case ID"
    )

    if case_search:
        display_queue = display_queue[
            display_queue["Case ID"]
            .str.contains(
                case_search,
                case=False
            )
        ]

    st.caption(
        f"Showing {len(display_queue)} of {len(triage_queue)} Total Cases"
    )

    display_queue = display_queue.sort_values(
        by="Priority"
    )

    styled_display_queue = display_queue.style.apply(
        highlight_priority,
        axis=1
    )

    st.dataframe(styled_display_queue)
