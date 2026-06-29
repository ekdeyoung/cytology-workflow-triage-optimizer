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

from predictive_features import (
    add_predictive_features,
    create_predictive_alerts,
    create_workflow_recommendations,
    create_forecasting_metrics,
)

from qc_detector import assign_qc_flag
from data_repository import load_cases

INPUT_FILE = "data/raw/cytology_cases.csv"
TREND_FILE = "data/raw/cytology_daily_metrics.csv"

st.title("Cytology Workflow Triage Optimizer")

st.markdown(
    "A database-backed cytology operations dashboard for triage, QC review, "
    "turnaround monitoring, and predictive workflow intelligence."
)

st.caption(
    f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)

st.sidebar.title("Operations Center")
st.sidebar.caption("Workflow Management")
st.sidebar.divider()

uploaded_file = st.sidebar.file_uploader(
    "Upload Cytology Case CSV",
    type=["csv"]
)

if uploaded_file is not None:
    st.sidebar.success("Uploaded CSV Loaded")
    cases = pd.read_csv(uploaded_file)
else:
    st.sidebar.info("Using Default Sample Dataset")
    cases = load_cases()

trend_data = pd.read_csv(TREND_FILE)
trend_data["date"] = pd.to_datetime(trend_data["date"])

try:
    validate_case_data(cases)
except ValueError as error:
    st.error(error)
    st.stop()

with st.sidebar.expander("Dataset Preview", expanded=False):
    st.write(f"Rows: {len(cases)}")
    st.write(f"Columns: {len(cases.columns)}")
    st.dataframe(cases.head())

st.sidebar.success("Dataset Validation Passed")

triage_queue = create_triage_queue(cases)

triage_queue = add_predictive_features(triage_queue)

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

predictive_alerts = create_predictive_alerts(triage_queue)

workflow_recommendations = (
    create_workflow_recommendations(triage_queue)
)

forecast_metrics = (
    create_forecasting_metrics(triage_queue)
)

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

overview_tab, queue_tab, qc_tab, turnaround_tab, trend_tab = st.tabs(
    [
        "Overview",
        "Operational Queue",
        "QC Analytics",
        "Turnaround Analytics",
        "Trend Analytics",
    ]
)

with overview_tab:
    st.subheader("Lab Status Overview")
    st.caption("Key operational indicators for the current cytology workload.")
    st.divider()

    if summary["overdue_cases"] > 0 or len(urgent_cases) >= 3:
        lab_status = "Watch"
        lab_status_message = "Active workload risks require monitoring."
    else:
        lab_status = "Stable"
        lab_status_message = "No major operational risks detected."

    with st.container():
        st.subheader(f"🟡 Lab Status: {lab_status}")
        st.write(lab_status_message)

    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)

    col1.metric("Total Cases", len(triage_queue))
    col2.metric("Urgent Cases", len(urgent_cases))
    col3.metric("Pathologist Review", len(pathologist_cases))
    col4.metric("Imager QC Review", len(imager_qc_review_cases))
    col5.metric("Overdue Cases", summary["overdue_cases"])
    col6.metric(
        "Avg Predicted Risk",
        round(
            triage_queue["predicted_risk_score"].mean(),
            2
        )
    )
    col7.metric(
        "Avg Abnormal Probability",
        f"{triage_queue['predicted_abnormal_probability'].mean() * 100:.1f}%"
    )
    col8.metric(
        "AI High Risk Cases",
        len(
            triage_queue[
                triage_queue["predictive_priority_flag"] == "high_risk"
            ]
        )
    )
    col9.metric(
        "Avg AI Priority Score",
        round(
            triage_queue["ai_priority_score"].mean(),
            2
        )
    )

    st.divider()
    st.subheader("Action Center")
    st.caption("Operational alerts, predictive risks, and AI recommendations requiring attention.")

    st.markdown("### Critical Operational Alerts")

    if workflow_alerts:
        for alert in workflow_alerts:
            st.warning(alert)

    st.markdown("### Predictive Risks")

    if predictive_alerts:
        for alert in predictive_alerts:
            st.warning(alert)
    else:
        st.success("No Predictive Alerts")

    st.markdown("### Recommended Actions")

    if workflow_recommendations:
        for recommendation in workflow_recommendations:
            st.info(recommendation)
    else:
        st.success("No AI Workflow Recommendations")

    st.subheader("Workload Interpretation")

    for interpretation in workload_interpretations:
        st.info(interpretation)


    st.subheader("Operational Forecast")

    forecast_col1, forecast_col2, forecast_col3 = st.columns(3)

    forecast_col1.metric(
        "Projected High Risk Cases",
        forecast_metrics["projected_high_risk_cases"]
    )

    forecast_col2.metric(
        "Projected QC Review Burden",
        forecast_metrics["projected_qc_review_burden"]
    )

    forecast_col3.metric(
        "Projected Delay Cases",
        forecast_metrics["projected_turnaround_delay_cases"]
    )

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
            "AI High Risk Cases",
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

    with st.expander("Predicted Risk Distribution", expanded=False):
        risk_distribution = (
            triage_queue["predictive_priority_flag"]
            .apply(format_workflow_label)
            .value_counts()
        )

        st.bar_chart(risk_distribution)

with qc_tab:
    st.subheader("Imager QC Analytics")

    qc_col1, qc_col2, qc_col3 = st.columns(3)

    qc_col1.metric(
        "QC Review Cases",
        summary["imager_qc_review_cases"]
    )

    qc_col2.metric(
        "QC Review %",
        f"{summary['imager_qc_review_pct']:.1f}%"
    )

    qc_col3.metric(
        "Avg Predicted QC Failure",
        f"{triage_queue['predicted_qc_failure_probability'].mean() * 100:.1f}%"
    )

    qc_distribution = (
        triage_queue["qc_flag"]
        .apply(format_workflow_label)
        .value_counts()
    )

    st.bar_chart(qc_distribution)

with turnaround_tab:
    st.subheader("Turnaround Analytics")

    tat_col1, tat_col2, tat_col3, tat_col4, tat_col5 = st.columns(5)

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

    tat_col5.metric(
        "Avg Predicted TAT Risk",
        f"{triage_queue['predicted_turnaround_risk'].mean() * 100:.1f}%"
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

with trend_tab:
    st.subheader("Historical Trend Analytics")

    trend_range = st.selectbox(
        "Select Trend Range",
        [
            "All Time",
            "Last 7 Days",
            "Last 30 Days",
        ]
    )

    if trend_range == "Last 7 Days":
        filtered_trend_data = trend_data[
            trend_data["date"] >= trend_data["date"].max() - pd.Timedelta(days=7)
        ]

    elif trend_range == "Last 30 Days":
        filtered_trend_data = trend_data[
            trend_data["date"] >= trend_data["date"].max() - pd.Timedelta(days=30)
        ]

    else:
        filtered_trend_data = trend_data

    latest_day = filtered_trend_data.iloc[-1]
    previous_day = filtered_trend_data.iloc[-2]

    trend_col1, trend_col2, trend_col3, trend_col4 = st.columns(4)

    trend_col1.metric(
        "Total Cases",
        latest_day["total_cases"],
        latest_day["total_cases"] - previous_day["total_cases"]
    )

    trend_col2.metric(
        "Urgent Cases",
        latest_day["urgent_cases"],
        latest_day["urgent_cases"] - previous_day["urgent_cases"]
    )

    trend_col3.metric(
        "QC Review Cases",
        latest_day["qc_review_cases"],
        latest_day["qc_review_cases"] - previous_day["qc_review_cases"]
    )

    trend_col4.metric(
        "Overdue Cases",
        latest_day["overdue_cases"],
        latest_day["overdue_cases"] - previous_day["overdue_cases"]
    )

    st.write("Daily Total Case Volume")

    st.line_chart(
        filtered_trend_data,
        x="date",
        y="total_cases"
    )

    st.write("Key Operational Trends")

    st.line_chart(
        filtered_trend_data,
        x="date",
        y=[
            "urgent_cases",
            "qc_review_cases",
            "overdue_cases",
        ]
    )

with queue_tab:
    st.subheader("Workflow Queue")

    rows_per_page = st.selectbox(
        "Rows Per Page",
        [10, 25, 50, 100]
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

    elif workflow_view == "Overdue Cases":
        filtered_queue = triage_queue[
            triage_queue["case_age_flag"] == "overdue"
        ]

    elif workflow_view == "AI High Risk Cases":
        filtered_queue = triage_queue[
            triage_queue["predictive_priority_flag"] == "high_risk"
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

    if display_queue.empty:
        st.warning("No Cases Match the Current Filters.")
        st.stop()

    selected_case = st.selectbox(
        "Select Case",
        display_queue["Case ID"]
    )

    st.caption(
        f"Showing {len(display_queue)} of {len(triage_queue)} Total Cases"
    )

    display_queue = display_queue.sort_values(
        by=[
            "AI Priority Score",
            "Priority",
        ],
        ascending=[
            False,
            True,
        ]
    )

    paged_display_queue = display_queue.head(rows_per_page)

    styled_display_queue = paged_display_queue.style.apply(
        highlight_priority,
        axis=1
    )

    csv_export = display_queue.to_csv(index=False)

    st.download_button(
        label="Export Filtered Queue",
        data=csv_export,
        file_name=f"{workflow_view.lower().replace(' ', '_')}_workflow_queue.csv",
        mime="text/csv",
    )

    st.subheader("Case Detail View")

    case_detail = display_queue[
        display_queue["Case ID"] == selected_case
    ]

    case_detail_display = (
        case_detail
        .astype(str)
        .T
        .rename(columns={case_detail.index[0]: "Case Details"})
    )

    st.dataframe(case_detail_display)

    st.dataframe(styled_display_queue)

st.divider()

st.caption(
    "Cytology Workflow Dashboard v4.0 | Database-Backed Workflow"
)

st.caption(
    f"Last Refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
