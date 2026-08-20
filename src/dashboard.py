import streamlit as st
import pandas as pd
from datetime import datetime
from workflow_engine import (
    add_workflow_metadata,
    describe_next_required_action,
    resolve_effective_next_stage,
)

from triage_utils import (
    create_triage_queue,
    get_urgent_cases,
    get_priority_review_cases,
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

def initialize_workflow_session():
    """Create temporary demo workflow storage for the current browser session."""
    if "workflow_case_state" not in st.session_state:
        st.session_state.workflow_case_state = {}

    if "workflow_activity_log" not in st.session_state:
        st.session_state.workflow_activity_log = []


def apply_workflow_session_state(queue):
    """Overlay temporary demo assignments and statuses onto the case queue."""
    session_queue = queue.copy()
    case_state = st.session_state.workflow_case_state

    def resolve_case_state(case):
        case_id = case["case_id"]

        if case_id in case_state:
            return case_state[case_id]

        adequacy_is_satisfactory = (
            str(case.get("adequacy", ""))
            .strip()
            .lower()
            != "unsatisfactory"
        )

        imaging_passed = (
            adequacy_is_satisfactory
            and case.get("qc_flag") == "imager_qc_pass"
            and case.get("next_stage")
            == "primary_cytologist_screening"
        )

        if imaging_passed:
            return {
                "assigned_to": "Unassigned",
                "workflow_status": "awaiting_primary_review",
                "last_action": (
                    "Automatically Routed After Imaging Pass"
                ),
            }

        return {
            "assigned_to": "Unassigned",
            "workflow_status": "not_started",
            "last_action": "No session activity",
        }

    resolved_states = session_queue.apply(
        resolve_case_state,
        axis=1,
    )

    session_queue["assigned_to"] = resolved_states.apply(
        lambda state: state["assigned_to"]
    )

    session_queue["workflow_status"] = resolved_states.apply(
        lambda state: state["workflow_status"]
    )

    session_queue["last_action"] = resolved_states.apply(
        lambda state: state["last_action"]
    )

    return session_queue


def record_workflow_action(case_id, action, workflow_status, assigned_to=None):
    """Update one case and append an auditable action to the session log."""
    current_state = st.session_state.workflow_case_state.get(case_id, {}).copy()

    if assigned_to is not None:
        current_state["assigned_to"] = assigned_to

    standardized_action = {
        "assigned": "Assigned",
        "qc_review": "Entered Imager Review",
        "reviewed": action,
        "completed": "Workflow Completed",
    }.get(workflow_status, action)

    preserve_review_progress = (
        workflow_status == "assigned"
        and assigned_to == "Quality Control Reviewer"
        and current_state.get("last_action")
        == "Primary Review Completed"
    )

    current_state["workflow_status"] = workflow_status
    if not preserve_review_progress:
        current_state["last_action"] = standardized_action
    current_state["updated_at"] = datetime.now().strftime("%H:%M:%S")

    st.session_state.workflow_case_state[case_id] = current_state

    st.session_state.workflow_activity_log.insert(
        0,
        {
            "time": datetime.now().strftime("%H:%M:%S"),
            "case_id": case_id,
            "action": standardized_action,
            "assigned_to": current_state.get("assigned_to", "Unassigned"),
        },
    )


def calculate_session_statistics(queue):
    """Return counts describing workflow actions completed during the demo session."""
    return {
        "assigned": int((queue["workflow_status"] == "assigned").sum()),
        "qc_review": int((queue["workflow_status"] == "qc_review").sum()),
        "reviewed": int(
            (
                (queue["workflow_status"] == "reviewed")
                & ~queue["last_action"].isin(
                    {
                        "Imager Review Completed",
                        "Primary Review Completed",
                        "Random QC Review Completed",
                        "Pathologist Review Completed",
                    }
                )
            ).sum()
        ),
        "awaiting_primary_review": int(
            (
                (
                    queue["workflow_status"]
                    == "awaiting_primary_review"
                )
                |
                (
                    (queue["workflow_status"] == "reviewed")
                    & (
                        queue["last_action"]
                        == "Imager Review Completed"
                    )
                )
            ).sum()
        ),
        "awaiting_pathologist_review": int(
            (
                (queue["workflow_status"] == "reviewed")
                & (
                    queue["last_action"]
                    == "Primary Review Completed"
                )
            ).sum()
        ),
        "completed": int((queue["workflow_status"] == "completed").sum()),
        "actions": len(st.session_state.workflow_activity_log),
        "awaiting_sign_out": int(
            (
                (queue["workflow_status"] == "reviewed")
                & (
                    queue["last_action"].isin(
                        {
                            "Random QC Review Completed",
                            "Pathologist Review Completed",
                        }
                    )
                )
            ).sum()
        ),
    }


def safe_mean(dataframe, column_name):
    """Return a rounded mean or 0.0 when a filtered queue is empty."""
    if dataframe.empty or column_name not in dataframe.columns:
        return 0.0
    return round(float(dataframe[column_name].mean()), 2)


def filter_operational_queue(queue, workflow_view, qc_view, quick_filter):
    """Apply sidebar filters and one-click worklist filters in one place."""
    filtered_queue = queue.copy()

    workflow_filters = {
        "Immediate Attention": filtered_queue["needs_attention"] == "immediate_attention",
        "Priority Review": filtered_queue["needs_attention"] == "pathologist_review",
        "Routine": filtered_queue["needs_attention"] == "routine",
        "Overdue Cases": filtered_queue["case_age_flag"] == "overdue",
        "AI High Risk Cases": filtered_queue["predictive_priority_flag"] == "high_risk",
    }

    if workflow_view in workflow_filters:
        filtered_queue = filtered_queue[workflow_filters[workflow_view]]

    if qc_view == "Imager Review Required":
        filtered_queue = filtered_queue[
            filtered_queue["qc_flag"] == "imager_qc_review"
        ]
    elif qc_view == "Imager Review Passed":
        filtered_queue = filtered_queue[
            filtered_queue["qc_flag"] == "imager_qc_pass"
        ]

    quick_filters = {
        "Immediate Attention": filtered_queue["needs_attention"] == "immediate_attention",
        "Imager Review": filtered_queue["qc_flag"] == "imager_qc_review",
        "Overdue": filtered_queue["case_age_flag"] == "overdue",
        "High AI Risk": filtered_queue["predictive_priority_flag"] == "high_risk",
        "Abnormal": (
            filtered_queue["diagnosis"]
            .astype(str)
            .str.lower()
            .isin(["ascus", "lsil", "asc-h", "hsil", "agc"])
        ),
    }

    if quick_filter in quick_filters:
        filtered_queue = filtered_queue[quick_filters[quick_filter]]

    return filtered_queue.copy()


def sort_operational_queue(queue, sort_option):
    """Apply commercially useful multi-level sorting rules."""
    sortable_queue = queue.copy()
    sortable_queue["workflow_status_rank"] = (
        sortable_queue.get("workflow_status", "not_started")
        .map({
            "not_started": 0,
            "awaiting_primary_review": 1,
            "assigned": 1,
            "qc_review": 1,
            "reviewed": 2,
            "completed": 3,
        })
        .fillna(0)
    )

    sorting_rules = {
        "Recommended Priority": (
            ["workflow_status_rank", "ai_priority_score", "priority", "turnaround_days"],
            [True, False, True, False],
        ),
        "Highest AI Risk": (
            ["predicted_risk_score", "ai_priority_score"],
            [False, False],
        ),
        "Longest Turnaround": (
            ["turnaround_days", "ai_priority_score"],
            [False, False],
        ),
        "Clinical Priority": (
            ["priority", "ai_priority_score"],
            [True, False],
        ),
        "Case ID": (["case_id"], [True]),
    }

    sort_columns, ascending = sorting_rules[sort_option]
    sorted_queue = sortable_queue.sort_values(
        by=sort_columns,
        ascending=ascending,
    ).copy()
    return sorted_queue.drop(columns=["workflow_status_rank"])


def add_worklist_badges(display_queue):
    """Add compact visual status cues while preserving the source data."""
    needs_attention_badges = {
        "immediate_attention": "🔴 Immediate Attention",
        "pathologist_review": "🔵 Priority Review",
        "routine": "🟢 Routine",
    }

    qc_badges = {
        "imager_qc_review": "🟠 Imager Review Required",
        "imager_qc_pass": "🟢 Imager Review Passed",
    }

    age_badges = {
        "overdue": "🔴 Overdue",
        "aging": "🟡 Aging",
        "within_target": "🟢 On Track",
    }

    display_queue["needs_attention"] = (
        display_queue["needs_attention"]
        .map(needs_attention_badges)
        .fillna(display_queue["needs_attention"].apply(format_workflow_label))
    )

    display_queue["qc_flag"] = (
        display_queue["qc_flag"]
        .map(qc_badges)
        .fillna(display_queue["qc_flag"].apply(format_workflow_label))
    )

    display_queue["case_age_flag"] = (
        display_queue["case_age_flag"]
        .map(age_badges)
        .fillna(display_queue["case_age_flag"].apply(format_workflow_label))
    )

    if "workflow_status" in display_queue.columns:
        awaiting_primary_review = (
            display_queue["workflow_status"].eq(
                "awaiting_primary_review"
            )
            |
            (
                display_queue["workflow_status"].eq("reviewed")
                & display_queue["last_action"].eq(
                    "Imager Review Completed"
                )
            )
        )

        awaiting_pathologist_review = (
            display_queue["workflow_status"].eq("reviewed")
            & display_queue["last_action"].eq(
                "Primary Review Completed"
            )
        )
        
        awaiting_sign_out = (
            display_queue["workflow_status"].eq("reviewed")
            & display_queue["last_action"].isin(
                {
                    "Random QC Review Completed",
                    "Pathologist Review Completed",
                }
            )
        )

        workflow_badges = {
            "not_started": "⚪ Not Started",
            "awaiting_primary_review": (
                "🟣 Awaiting Primary Cytologist Review"
            ),
            "assigned": "🔵 Assigned",
            "qc_review": "🟠 In Imager Review",
            "reviewed": "🟣 Reviewed",
            "completed": "🟢 Completed",
        }

        display_queue["workflow_status"] = (
            display_queue["workflow_status"]
            .map(workflow_badges)
            .fillna(
                display_queue["workflow_status"].apply(
                    format_workflow_label
                )
            )
        )

        display_queue.loc[
            awaiting_primary_review,
            "workflow_status",
        ] = "🟣 Awaiting Primary Cytologist Review"

        display_queue.loc[
            awaiting_pathologist_review,
            "workflow_status",
            ] = "🟣 Awaiting Pathologist Review"
        
        display_queue.loc[
            awaiting_sign_out,
            "workflow_status",
        ] = "🟣 Awaiting Final Sign Out"

    return display_queue


def prepare_display_queue(queue, display_value_columns):
    """Format raw queue fields for presentation without changing analytics data."""
    display_queue = add_worklist_badges(queue.copy())

    for column in display_value_columns:
        if column in display_queue.columns:
            display_queue[column] = display_queue[column].apply(format_workflow_label)

    renamed_columns = {
        column: format_column_label(column)
        for column in display_queue.columns
    }

    renamed_columns[
        "predicted_qc_failure_probability"
    ] = "Predicted Imager Failure Probability"

    renamed_columns["qc_flag"] = "Imager Review Status"

    # Use supervisor-friendly labels for fields whose technical names do not
    # translate cleanly through the generic column formatter.
    renamed_columns["case_age_flag"] = "Age Status"
    renamed_columns["assigned_to"] = "Assigned To"
    renamed_columns["workflow_status"] = "Workflow Status"
    renamed_columns["last_action"] = "Last Session Action"
    renamed_columns["specimen_category"] = "Specimen Category"
    renamed_columns["workflow_type"] = "Workflow Type"
    renamed_columns["current_stage"] = "Current Stage"
    renamed_columns["next_stage"] = "Next Stage"
    renamed_columns["next_required_action"] = "Next Required Action"

    return display_queue.rename(columns=renamed_columns)


def highlight_worklist_row(row):
    """Use restrained row highlighting to show operational urgency."""
    age_status = str(row.get("Age Status", ""))
    attention_status = str(row.get("Needs Attention", ""))
    qc_status = str(row.get("Imager Review Status", ""))
    ai_priority = float(row.get("AI Priority Score", 0) or 0)

    if "Overdue" in age_status or "Immediate Attention" in attention_status:
        return ["background-color: #ffe8e8"] * len(row)

    if ai_priority >= 0.75:
        return ["background-color: #fff1df"] * len(row)

    if "Imager Review Required" in qc_status:
        return ["background-color: #fff8d9"] * len(row)

    return [""] * len(row)


def calculate_queue_health(filtered_queue):
    """Summarize worklist condition as an executive-friendly status."""
    if filtered_queue.empty:
        return "No Cases", "No cases match the current filters."

    immediate_count = int(
        (filtered_queue["needs_attention"] == "immediate_attention").sum()
    )
    overdue_count = int((filtered_queue["case_age_flag"] == "overdue").sum())
    high_risk_count = int(
        (filtered_queue["predictive_priority_flag"] == "high_risk").sum()
    )

    risk_points = (immediate_count * 2) + (overdue_count * 2) + high_risk_count

    if risk_points >= 8:
        return "Critical", "Multiple urgent, overdue, or high-risk cases require action."
    if risk_points >= 3:
        return "Watch", "The queue contains active workload risks that should be monitored."
    return "Stable", "The displayed queue is within expected operational limits."


def create_case_recommendation(
        case_record,
        effective_next_stage,
):
    """Generate a concise, explainable next action for the selected case."""
    if case_record["case_age_flag"] == "overdue":
        return "Escalate this case and confirm ownership because turnaround is overdue."
    if case_record["needs_attention"] == "immediate_attention":
        return "Move this case to the front of the active review queue."
    if effective_next_stage == "imager_review":
        return "Route this case to Imager Review before primary cytologist review."
    if case_record["needs_attention"] == "pathologist_review":
        return "Prioritize this case for earlier primary cytologist review."
    if case_record["predictive_priority_flag"] == "high_risk":
        return "Prioritize review and monitor predictive risk indicators closely."
    return "Continue routine workflow processing."


def create_daily_operations_report(
    queue,
    session_statistics,
    queue_health,
    queue_health_message,
    supervisor_notes,
):
    """Create a downloadable plain-text daily operations report."""

    total_cases = len(queue)

    urgent_cases = int(
        (queue["needs_attention"] == "immediate_attention").sum()
    )

    priority_review_cases = int(
        (queue["needs_attention"] == "pathologist_review").sum()
    )

    imager_review_cases = int(
        (queue["qc_flag"] == "imager_qc_review").sum()
    )

    overdue_cases = int(
        (queue["case_age_flag"] == "overdue").sum()
    )

    high_ai_risk_cases = int(
        (queue["predictive_priority_flag"] == "high_risk").sum()
    )

    average_turnaround = safe_mean(
        queue,
        "turnaround_days"
    )

    average_predicted_risk = (
        safe_mean(queue, "predicted_risk_score") * 100
    )

    notes_text = (
        supervisor_notes.strip()
        if supervisor_notes.strip()
        else "No supervisor notes entered."
    )

    if queue_health == "Critical":
        recommended_action = (
            "Prioritize immediate-attention and overdue cases, confirm ownership "
            "of high-risk work, and monitor Imager Review capacity throughout the shift."
        )
    elif queue_health == "Watch":
        recommended_action = (
            "Review active workload risks, monitor turnaround performance, "
            "and confirm coverage for Imager Review and Priority Review."
        )
    else:
        recommended_action = (
            "Continue routine workflow monitoring and maintain current staffing coverage."
        )

    return f"""
CYTOLOGY DAILY OPERATIONS REPORT

Report Generated:
{datetime.now().strftime("%B %d, %Y at %I:%M %p")}

OPERATIONAL SNAPSHOT

Total Cases: {total_cases}
Immediate Attention: {urgent_cases}
Priority Review: {priority_review_cases}
Imager Review: {imager_review_cases}
Overdue Cases: {overdue_cases}
High AI Risk Cases: {high_ai_risk_cases}
Average Turnaround: {average_turnaround:.1f} days
Average Predicted Risk: {average_predicted_risk:.0f}%
Queue Health: {queue_health}
Queue Health Interpretation: {queue_health_message}

SESSION WORKFLOW ACTIVITY

Assigned Cases: {session_statistics["assigned"]}
Cases in Imager Review: {session_statistics["qc_review"]}
Awaiting Primary Cytologist Review: {session_statistics["awaiting_primary_review"]}
Reviewed Cases: {session_statistics["reviewed"]}
Awaiting Final Sign Out: {session_statistics["awaiting_sign_out"]}
Completed Cases: {session_statistics["completed"]}
Recorded Actions: {session_statistics["actions"]}

RECOMMENDED OPERATIONAL ACTION

{recommended_action}

SUPERVISOR NOTES

{notes_text}

Generated by:
Cytology Workflow Triage Optimizer
""".strip()


st.title("Cytology Workflow Triage Optimizer")

st.markdown(
    "A database-backed cytology operations dashboard for AI-assisted triage, "
    "Imager Review, clinical workflow routing, turnaround monitoring, "
    "and predictive workflow intelligence."
)

st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.sidebar.title("Operations Center")
st.sidebar.caption("Workflow Management")
st.sidebar.divider()

uploaded_file = st.sidebar.file_uploader(
    "Upload Cytology Case CSV",
    type=["csv"],
)

if uploaded_file is not None:
    try:
        cases = pd.read_csv(uploaded_file)
        st.sidebar.success("Uploaded CSV Loaded")

    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
        st.error(
            "The uploaded file could not be read as a valid CSV. "
            "Please verify the file format and try again."
        )
        st.stop()

else:
    st.sidebar.info("Using Default Sample Dataset")
    cases = load_cases()

try:
    trend_data = pd.read_csv(TREND_FILE)

    if (
        "imager_review_cases" not in trend_data.columns
        and "qc_review_cases" in trend_data.columns
    ):
        trend_data = trend_data.rename(
            columns={"qc_review_cases": "imager_review_cases"}
        )
    

    required_trend_columns = {
        "date",
        "total_cases",
        "urgent_cases",
        "imager_review_cases",
        "overdue_cases",
    }

    missing_trend_columns = (
        required_trend_columns
        - set(trend_data.columns)
    )

    if missing_trend_columns:
        raise ValueError(
            "Missing trend columns: "
            + ", ".join(sorted(missing_trend_columns))
        )

    trend_data["date"] = pd.to_datetime(
        trend_data["date"],
        errors="coerce"
    )

    trend_data = (
        trend_data
        .dropna(subset=["date"])
        .sort_values("date")
        .reset_index(drop=True)
    )

except (
    FileNotFoundError,
    pd.errors.EmptyDataError,
    pd.errors.ParserError,
    ValueError,
):
    trend_data = pd.DataFrame()


if cases.empty:
    st.error(
        "The selected dataset contains no case records. "
        "Upload a CSV containing at least one cytology case."
    )
    st.stop()

try:
    validate_case_data(cases)

except ValueError as error:
    st.error(
        f"Dataset validation failed: {error}"
    )
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
        row["artifact_risk_score"],
    ),
    axis=1,
)

triage_queue = add_workflow_metadata(
    triage_queue
)

initialize_workflow_session()

triage_queue = apply_workflow_session_state(
    triage_queue
)

urgent_cases = get_urgent_cases(triage_queue)
priority_review_cases = get_priority_review_cases(
    triage_queue
)
imager_qc_review_cases = get_imager_qc_review_cases(triage_queue)

summary = create_summary_metrics(
    triage_queue,
    urgent_cases,
    priority_review_cases,
)

workflow_alerts = create_workflow_alerts(summary)
predictive_alerts = create_predictive_alerts(triage_queue)
workflow_recommendations = create_workflow_recommendations(triage_queue)
forecast_metrics = create_forecasting_metrics(triage_queue)
workload_interpretations = interpret_workload(summary)

with st.sidebar:
    st.header("Workflow Summary")
    st.write(f"Total Cases: {len(triage_queue)}")
    st.write(f"Urgent Cases: {len(urgent_cases)}")
    st.write(f"Priority Review: {len(priority_review_cases)}")
    st.write(f"Imager Review: {len(imager_qc_review_cases)}")
    st.write(f"Overdue Cases: {summary['overdue_cases']}")
    st.divider()
    st.write("Current Workflow Status")

    for interpretation in workload_interpretations:
        st.write(f"- {interpretation}")

    st.divider()
    st.subheader("Workflow Filters")

    workflow_view = st.selectbox(
        "Select Workflow View",
        [
            "All Cases",
            "Immediate Attention",
            "Priority Review",
            "Routine",
            "Overdue Cases",
            "AI High Risk Cases",
        ],
    )

    qc_view = st.selectbox(
        "Select Imager Review View",
        [
            "All Imager Review States",
            "Imager Review Required",
            "Imager Review Passed",
        ],
    )


display_value_columns = [
    "adequacy",
    "scan_status",
    "diagnosis",
    "specimen_category",
    "workflow_type",
    "current_stage",
    "next_stage",
]

(
    overview_tab, 
    queue_tab, 
    intelligence_tab, 
    qc_tab, 
    turnaround_tab, 
    trend_tab,
    reports_tab,
) = st.tabs(
    [
        "Overview",
        "Operational Queue",
        "Workflow Intelligence",
        "Imager Analytics",
        "Turnaround Analytics",
        "Trend Analytics",
        "Executive Reports",
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
        st.markdown("**Current Operational Risks**")

        if len(urgent_cases) >= 3:
            st.write("• High urgent case workload")
        if summary["overdue_cases"] > 0:
            st.write("• Overdue cases require attention")
        if summary["imager_qc_review_cases"] > 5:
            st.write("• Elevated imager review workload")

        st.markdown("**Recommended Next Action**")

        if lab_status == "Watch":
            st.write(
                "Prioritize urgent cases, assign additional imager review resources, "
                "and monitor turnaround times."
            )
        else:
            st.write("Continue routine workflow monitoring.")

        st.divider()
        st.subheader("Key Performance Indicators")
        st.caption("Current operational and predictive performance metrics.")

    st.markdown("**Operations**")
    operations_col1, operations_col2, operations_col3 = st.columns(3)
    operations_col1.metric("Total Cases", len(triage_queue))
    operations_col2.metric("Urgent Cases", len(urgent_cases))
    operations_col3.metric("Overdue Cases", summary["overdue_cases"])

    st.markdown("**AI & Quality**")
    ai_col1, ai_col2, ai_col3 = st.columns(3)

    ai_col1.metric(
        "AI High Risk Cases",
        len(
            triage_queue[
                triage_queue["predictive_priority_flag"] == "high_risk"
            ]
        ),
    )
    ai_col2.metric(
        "Avg Predicted Risk",
        round(triage_queue["predicted_risk_score"].mean(), 2),
    )
    ai_col3.metric(
        "Avg AI Priority Score",
        round(triage_queue["ai_priority_score"].mean(), 2),
    )

    st.divider()
    st.subheader("Action Center")
    st.caption(
        "Operational alerts, predictive risks, and AI recommendations requiring attention."
    )

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

    st.divider()
    st.subheader("Today's Priority Worklist")
    st.caption("Cases requiring the most immediate operational attention.")

    high_priority_cases = triage_queue[triage_queue["priority"] <= 5].copy()
    high_priority_cases = sort_operational_queue(
        high_priority_cases,
        "Recommended Priority",
    )
    high_priority_display = prepare_display_queue(
        high_priority_cases,
        display_value_columns,
    )

    priority_worklist_columns = [
        "Case ID",
        "Diagnosis",
        "Priority",
        "Needs Attention",
        "Imager Review Status",
        "AI Priority Score",
        "Turnaround Days",
    ]

    priority_worklist_display = high_priority_display[
        priority_worklist_columns
    ].copy()

    st.caption(
        f"{len(priority_worklist_display)} cases currently require priority review."
    )

    st.dataframe(
        priority_worklist_display.style.format(
            {
                "AI Priority Score": "{:.2f}",
                "Turnaround Days": "{} days",
            }
        ),
        width="stretch",
        hide_index=True,
    )

with intelligence_tab:
    st.subheader("Workflow Intelligence")
    st.caption("AI-assisted workload interpretation and operational forecasting.")

    st.subheader("Workload Interpretation")
    for interpretation in workload_interpretations:
        st.info(interpretation)

    st.subheader("Operational Forecast")
    forecast_col1, forecast_col2, forecast_col3 = st.columns(3)
    forecast_col1.metric(
        "Projected High Risk Cases",
        forecast_metrics["projected_high_risk_cases"],
    )
    forecast_col2.metric(
        "Projected Imager Review Burden",
        forecast_metrics["projected_qc_review_burden"],
    )
    forecast_col3.metric(
        "Projected Delay Cases",
        forecast_metrics["projected_turnaround_delay_cases"],
    )

with qc_tab:
    st.subheader("Imager Review Analytics")
    qc_col1, qc_col2, qc_col3 = st.columns(3)
    qc_col1.metric("Imager Review Cases", summary["imager_qc_review_cases"])
    qc_col2.metric(
        "Imager Review %",
        f"{summary['imager_review_pct']:.1f}%"
    )
    qc_col3.metric(
        "Avg Predicted Imager Failure",
        f"{triage_queue['predicted_qc_failure_probability'].mean() * 100:.1f}%",
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
    tat_col1.metric("Average Turnaround", summary["average_turnaround_days"])
    tat_col2.metric("Longest Turnaround", summary["longest_turnaround_days"])
    tat_col3.metric("Overdue Cases", summary["overdue_cases"])
    tat_col4.metric("Aging Cases", summary["aging_cases"])
    tat_col5.metric(
        "Avg Predicted TAT Risk",
        f"{triage_queue['predicted_turnaround_risk'].mean() * 100:.1f}%",
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

    if trend_data.empty or len(trend_data) < 2:
        st.info(
            "Historical trend analytics require at least two "
            "valid daily records."
        )

    else:
        trend_range = st.selectbox(
            "Select Trend Range",
            [
                "All Time",
                "Last 7 Days",
                "Last 30 Days",
            ],
        )

        if trend_range == "Last 7 Days":
            filtered_trend_data = trend_data[
                trend_data["date"]
                >= trend_data["date"].max() - pd.Timedelta(days=7)
            ]

        elif trend_range == "Last 30 Days":
            filtered_trend_data = trend_data[
                trend_data["date"]
                >= trend_data["date"].max() - pd.Timedelta(days=30)
            ]

        else:
            filtered_trend_data = trend_data

        if len(filtered_trend_data) < 2:
            st.info(
                "The selected trend range requires at least two "
                "valid daily records."
            )

        else:
            latest_day = filtered_trend_data.iloc[-1]
            previous_day = filtered_trend_data.iloc[-2]

            trend_col1, trend_col2, trend_col3, trend_col4 = (
                st.columns(4)
            )

            trend_col1.metric(
                "Total Cases",
                latest_day["total_cases"],
                latest_day["total_cases"]
                - previous_day["total_cases"],
            )

            trend_col2.metric(
                "Urgent Cases",
                latest_day["urgent_cases"],
                latest_day["urgent_cases"]
                - previous_day["urgent_cases"],
            )

            trend_col3.metric(
                "Imager Review Cases",
                latest_day["imager_review_cases"],
                latest_day["imager_review_cases"]
                - previous_day["imager_review_cases"],
            )

            trend_col4.metric(
                "Overdue Cases",
                latest_day["overdue_cases"],
                latest_day["overdue_cases"]
                - previous_day["overdue_cases"],
            )

            st.write("Daily Total Case Volume")

            st.line_chart(
                filtered_trend_data,
                x="date",
                y="total_cases",
            )

            st.write("Key Operational Trends")

            st.line_chart(
                filtered_trend_data,
                x="date",
                y=[
                    "urgent_cases",
                    "imager_review_cases",
                    "overdue_cases",
                ],
            )

with queue_tab:
    st.subheader("Operational Work Queue")
    st.caption(
        "Prioritized case worklist for daily cytology operations and supervisory review."
    )

    session_statistics = calculate_session_statistics(triage_queue)

    st.markdown("**Demo Session Activity**")
    (
        session_col1,
        session_col2,
        session_col3,
        session_col4,
        session_col5,
        session_col6,
        session_col7,
    ) = st.columns(7)
    session_col1.metric("Assigned", session_statistics["assigned"])
    session_col2.metric("In Imager Review", session_statistics["qc_review"])
    session_col3.metric(
        "Awaiting Primary Review",
        session_statistics["awaiting_primary_review"],
    )
    session_col4.metric("Reviewed", session_statistics["reviewed"])
    session_col5.metric(
        "Awaiting Sign Out",
        session_statistics["awaiting_sign_out"],
    )
    session_col6.metric("Completed", session_statistics["completed"])
    session_col7.metric("Actions", session_statistics["actions"])

    with st.expander("Session Activity Log", expanded=False):
        if st.session_state.workflow_activity_log:
            activity_log_display = pd.DataFrame(
                st.session_state.workflow_activity_log
            ).rename(
                columns={
                    "time": "Time",
                    "case_id": "Case ID",
                    "action": "Workflow Action",
                    "assigned_to": "Assigned To",
                }
            )

            st.dataframe(
                activity_log_display,
                width="stretch",
                hide_index=True,
            )
        else:
            st.caption("No workflow actions have been recorded in this session.")

        if st.button("Reset Demo Session", width="stretch"):
            st.session_state.workflow_case_state = {}
            st.session_state.workflow_activity_log = []
            st.rerun()

    quick_filter = st.radio(
        "Quick View",
        [
            "All Cases",
            "Immediate Attention",
            "Imager Review",
            "Overdue",
            "High AI Risk",
            "Abnormal",
        ],
        horizontal=True,
    )

    control_col1, control_col2, control_col3 = st.columns([2, 2, 1])

    with control_col1:
        case_search = st.text_input(
            "Search Case ID",
            placeholder="Enter a full or partial case ID",
        )

    with control_col2:
        sort_option = st.selectbox(
            "Sort Worklist",
            [
                "Recommended Priority",
                "Highest AI Risk",
                "Longest Turnaround",
                "Clinical Priority",
                "Case ID",
            ],
        )

    with control_col3:
        rows_per_page = st.selectbox(
            "Rows",
            [10, 25, 50, 100],
        )

    filtered_queue = filter_operational_queue(
        triage_queue,
        workflow_view,
        qc_view,
        quick_filter,
    )

    if case_search:
        filtered_queue = filtered_queue[
            filtered_queue["case_id"]
            .astype(str)
            .str.contains(case_search, case=False, na=False)
        ]

    filtered_queue = sort_operational_queue(filtered_queue, sort_option)

    st.markdown("**Queue Summary**")
    queue_health, queue_health_message = calculate_queue_health(filtered_queue)

    queue_col1, queue_col2, queue_col3, queue_col4 = st.columns(4)
    queue_col5, queue_col6, queue_col7, queue_col8 = st.columns(4)

    queue_col1.metric("Displayed Cases", len(filtered_queue))
    queue_col2.metric(
        "Immediate Attention",
        int((filtered_queue["needs_attention"] == "immediate_attention").sum())
        if not filtered_queue.empty
        else 0,
    )
    queue_col3.metric(
        "Priority Review",
        int((filtered_queue["needs_attention"] == "pathologist_review").sum())
        if not filtered_queue.empty
        else 0,
    )
    queue_col4.metric(
        "Imager Review",
        int((filtered_queue["qc_flag"] == "imager_qc_review").sum())
        if not filtered_queue.empty
        else 0,
    )
    queue_col5.metric(
        "Overdue",
        int((filtered_queue["case_age_flag"] == "overdue").sum())
        if not filtered_queue.empty
        else 0,
    )
    queue_col6.metric(
        "High AI Risk",
        int((filtered_queue["predictive_priority_flag"] == "high_risk").sum())
        if not filtered_queue.empty
        else 0,
    )
    queue_col7.metric(
        "Avg Turnaround",
        f"{safe_mean(filtered_queue, 'turnaround_days'):.1f} days",
    )
    queue_col8.metric(
        "Avg Predicted Risk",
        f"{safe_mean(filtered_queue, 'predicted_risk_score') * 100:.0f}%",
    )

    if queue_health == "Critical":
        st.error(f"Queue Health: {queue_health}. {queue_health_message}")
    elif queue_health == "Watch":
        st.warning(f"Queue Health: {queue_health}. {queue_health_message}")
    elif queue_health == "Stable":
        st.success(f"Queue Health: {queue_health}. {queue_health_message}")
    else:
        st.info(f"Queue Health: {queue_health}. {queue_health_message}")

    if filtered_queue.empty:
        st.warning("No cases match the current filters.")
    else:
        available_columns = {
            "Case ID": "Case ID",
            "Priority": "Priority",
            "Diagnosis": "Diagnosis",
            "Needs Attention": "Needs Attention",
            "Imager Review Status": "Imager Review Status",
            "Age Status": "Age Status",
            "Assigned To": "Assigned To",
            "Workflow Status": "Workflow Status",
            "Last Session Action": "Last Session Action",
            "AI Priority Score": "AI Priority Score",
            "Predicted Risk Score": "Predicted Risk Score",
            "Turnaround Days": "Turnaround Days",
            "Adequacy": "Adequacy",
            "Scan Status": "Scan Status",
            "Predicted Abnormal Probability": "Predicted Abnormal Probability",
            "Predicted Imager Failure Probability": (
                "Predicted Imager Failure Probability"
            ),
            "Predicted Turnaround Risk": "Predicted Turnaround Risk",
        }

        default_columns = [
            "Case ID",
            "Priority",
            "Diagnosis",
            "Needs Attention",
            "Imager Review Status",
            "Age Status",
            "Assigned To",
            "Workflow Status",
            "AI Priority Score",
            "Predicted Risk Score",
            "Turnaround Days",
        ]

        with st.expander("Worklist Display Options", expanded=False):
            selected_columns = st.multiselect(
                "Choose Worklist Columns",
                options=list(available_columns.keys()),
                default=default_columns,
            )

        if not selected_columns:
            selected_columns = default_columns

        selected_case_id = st.selectbox(
            "Select Case for Detailed Review",
            filtered_queue["case_id"].tolist(),
        )

        st.caption(
            f"Showing {min(len(filtered_queue), rows_per_page)} of "
            f"{len(filtered_queue)} filtered cases, from {len(triage_queue)} total cases."
        )

        case_record = filtered_queue[
            filtered_queue["case_id"] == selected_case_id
        ].iloc[0]

        st.subheader("Selected Case Summary")
        case_col1, case_col2, case_col3, case_col4 = st.columns(4)
        case_col1.metric("Case ID", case_record["case_id"])
        case_col2.metric("Priority", case_record["priority"])
        case_col3.metric("AI Priority", f"{case_record['ai_priority_score']:.2f}")
        case_col4.metric(
            "Predicted Risk",
            f"{case_record['predicted_risk_score'] * 100:.0f}%",
        )

        detail_col1, detail_col2 = st.columns(2)

        with detail_col1:
            st.markdown("**Clinical Information**")
            st.write(f"**Diagnosis:** {format_workflow_label(case_record['diagnosis'])}")
            st.write(f"**Adequacy:** {format_workflow_label(case_record['adequacy'])}")
            st.write(f"**Scan Status:** {format_workflow_label(case_record['scan_status'])}")

        with detail_col2:
            st.markdown("**Workflow Status**")
            attention_status = {
                "pathologist_review": "Priority Review",
            }.get(
                case_record["needs_attention"],
                format_workflow_label(case_record["needs_attention"]),
            )

            st.write(f"**Needs Attention:** {attention_status}")
            imager_review_status = {
                "imager_qc_review": "Imager Review Required",
                "imager_qc_pass": "Imager Review Passed",
            }.get(
                case_record["qc_flag"],
                format_workflow_label(case_record["qc_flag"]),
            )

            st.write(f"**Imager Review Status:** {imager_review_status}")
            turnaround_days = int(case_record["turnaround_days"])
            turnaround_label = "day" if turnaround_days == 1 else "days"

            st.write(
                f"**Turnaround:** "
                f"{turnaround_days} {turnaround_label}"
            )
            st.write(f"**Age Status:** {format_workflow_label(case_record['case_age_flag'])}")

        st.markdown("**Clinical Workflow Routing**")

        workflow_col1, workflow_col2 = st.columns(2)

        with workflow_col1:
            st.write(
                f"**Specimen Category:** "
                f"{format_workflow_label(case_record['specimen_category'])}"
            )
            st.write(
                f"**Workflow Type:** "
                f"{format_workflow_label(case_record['workflow_type'])}"
            )
            st.write(
                f"**Current Stage:** "
                f"{format_workflow_label(case_record['current_stage'])}"
            )

        with workflow_col2:
            display_next_stage = resolve_effective_next_stage(
                workflow_stages=case_record.get("workflow_path", []),
                next_stage=case_record.get("next_stage"),
                last_action=case_record.get("last_action"),
                assigned_to=case_record.get(
                    "assigned_to",
                    "Unassigned",
                ),
            )

            next_stage_label = (
                format_workflow_label(display_next_stage)
                if pd.notna(display_next_stage)
                else "Workflow Complete"
            )

            st.write(f"**Next Stage:** {next_stage_label}")
            st.write(
                f"**Next Required Action:** "
                f"{describe_next_required_action(display_next_stage)}"
            )

        st.markdown("**Predictive Assessment**")
        
        risk_col1, risk_col2, risk_col3 = st.columns(3)
            
        risk_col1.metric(
            "Abnormal Probability",
            f"{case_record['predicted_abnormal_probability'] * 100:.0f}%",
        )
        risk_col2.metric(
            "Imager Failure Risk",
            f"{case_record['predicted_qc_failure_probability'] * 100:.0f}%",
        )
        risk_col3.metric(
            "Turnaround Risk",
            f"{case_record['predicted_turnaround_risk'] * 100:.0f}%",
        )

        st.markdown("**Recommended Action**")
        st.info(
            create_case_recommendation(
                case_record,
                display_next_stage,
            )
        )

        st.markdown("**Workflow Action Center**")
        st.caption(
            "These actions update only the current Streamlit session and do not modify source data."
        )

        current_assignee = case_record.get(
            "assigned_to",
            "Unassigned",
        )

        current_workflow_status = case_record.get(
            "workflow_status",
            "not_started",
        )

        effective_next_stage = resolve_effective_next_stage(
            workflow_stages=case_record.get("workflow_path", []),
            next_stage=case_record.get("next_stage"),
            last_action=case_record.get("last_action"),
            assigned_to=current_assignee,
        )
        
        if effective_next_stage == "imager_review":
            reviewer_options = [
                "Unassigned",
                "Imager Review Specialist",
            ]

        elif effective_next_stage == "pathologist_review":
            reviewer_options = [
                "Unassigned",
                "Pathologist",
            ]

        elif effective_next_stage == "quality_control_review":
            reviewer_options = [
                "Unassigned",
                "Quality Control Reviewer",
            ]

        elif effective_next_stage == "final_sign_out":
            if (
                "pathologist_review"
                in case_record.get("workflow_path", [])
            ):
                reviewer_options = [
                    "Unassigned",
                    "Pathologist",
                ]
            else:
                reviewer_options = [
                    "Unassigned",
                    "Cytologist",
                    "Senior Cytologist",
                ]

        else:
            reviewer_options = [
                "Unassigned",
                "Cytologist",
                "Senior Cytologist",
            ]

        default_reviewer_index = (
            reviewer_options.index(current_assignee)
            if current_assignee in reviewer_options
            else 0
        )

        action_col1, action_col2 = st.columns([2, 1])
        with action_col1:
            selected_reviewer = st.selectbox(
                "Assign Reviewer",
                reviewer_options,
                index=default_reviewer_index,
                key=f"reviewer_{selected_case_id}",
            )
        with action_col2:
            if (
                current_workflow_status
                == "awaiting_primary_review"
                or (
                    effective_next_stage
                    == "primary_cytologist_screening"
                    and case_record.get("last_action")
                    == "Imager Review Completed"
                )
            ):
                session_status = "Awaiting Primary Cytologist Review"

            elif (
                effective_next_stage == "pathologist_review"
                and case_record.get("last_action")
                == "Primary Review Completed"
            ):
                session_status = "Awaiting Pathologist Review"

            elif (
                effective_next_stage == "final_sign_out"
                and case_record.get("last_action") in {
                    "Primary Review Completed",
                    "Random QC Review Completed",
                    "Pathologist Review Completed",
                }
            ):
                session_status = "Awaiting Final Sign Out"

            else:
                session_status = {
                    "not_started": "Not Started",
                    "assigned": "Assigned",
                    "qc_review": "In Imager Review",
                    "reviewed": "Reviewed",
                    "completed": "Completed",
                }.get(
                    current_workflow_status,
                    format_workflow_label(current_workflow_status),
                )

            st.metric(
                "Session Status",
                session_status,
            )

            st.caption(
                f"Assigned to: "
                f"{case_record.get('assigned_to', 'Unassigned')}"
            )

        case_is_completed = (
            current_workflow_status == "completed"
        )

        case_is_reviewed = (
            current_workflow_status == "reviewed"
            and case_record.get("last_action") in {
                "Primary Review Completed",
                "Random QC Review Completed",
                "Pathologist Review Completed",
            }
        )

        button_col1, button_col2, button_col3, button_col4 = st.columns(4)

        if button_col1.button(
            "Assign Case",
            width="stretch",
            disabled=(
                selected_reviewer == "Unassigned"
                or case_is_completed
                or (
                    selected_reviewer == current_assignee
                    and current_workflow_status in {
                        "assigned",
                        "qc_review",
                    }
                )
            ),
        ):
            assignment_status = (
                "qc_review"
                if effective_next_stage == "imager_review"
                else "assigned"
            )

            assignment_action = (
                "Assigned for Imager Review"
                if assignment_status == "qc_review"
                else f"Assigned to {selected_reviewer}"
            )

            record_workflow_action(
                selected_case_id,
                assignment_action,
                assignment_status,
                selected_reviewer,
            )
            st.rerun()

        if button_col2.button(
            "Send to Imager Review",
            width="stretch",
            disabled=(
                case_is_completed
                or current_workflow_status == "qc_review"
                or effective_next_stage != "imager_review"
            ),
        ):
            imager_assignee = (
                selected_reviewer
                if selected_reviewer != "Unassigned"
                else "Imager Review Specialist"
            )

            record_workflow_action(
                selected_case_id,
                "Sent to Imager Review",
                "qc_review",
                imager_assignee,
            )
            st.rerun()

        if button_col3.button(
            "Mark Reviewed",
            width="stretch",
            disabled=(
                case_is_completed
                or case_is_reviewed
                or case_record.get("assigned_to", "Unassigned") == "Unassigned"
            ),
        ):
            if current_workflow_status == "qc_review":
                review_action = "Imager Review Completed"
            elif effective_next_stage == "quality_control_review":
                review_action = "Random QC Review Completed"
            elif current_assignee == "Pathologist":
                review_action = "Pathologist Review Completed"
            else:
                review_action = "Primary Review Completed"

            record_workflow_action(
                selected_case_id,
                review_action,
                "reviewed",
                (
                    selected_reviewer
                    if selected_reviewer != "Unassigned"
                    else None
                ),
            )
            st.rerun()

        if button_col4.button(
            "Complete Workflow",
            width="stretch",
            disabled=(
                case_is_completed
                or case_record.get("last_action") not in {
                    "Primary Review Completed",
                    "Random QC Review Completed",
                    "Pathologist Review Completed",
                }
                or effective_next_stage != "final_sign_out"
            ),
        ):
            
            record_workflow_action(
                selected_case_id,
                "Workflow completed",
                "completed",
                (
                    selected_reviewer
                    if selected_reviewer != "Unassigned"
                    else None
                ),
            )
            st.rerun()

        if case_is_completed:
            st.success(
                "This case has completed the simulated workflow."
            )
        elif not case_is_reviewed:
            st.caption(
                "Mark the case reviewed before completing the workflow."
            )

        st.subheader("Operational Worklist")

        display_queue = prepare_display_queue(
            filtered_queue,
            display_value_columns,
        )

        valid_selected_columns = [
            column
            for column in selected_columns
            if column in display_queue.columns
        ]

        if not valid_selected_columns:
            valid_selected_columns = [
                column
                for column in default_columns
                if column in display_queue.columns
            ]

        paged_display_queue = (
            display_queue[valid_selected_columns]
            .head(rows_per_page)
            .copy()
        )

        formatters = {
            "AI Priority Score": "{:.2f}",
            "Predicted Risk Score": "{:.2f}",
            "Predicted Abnormal Probability": "{:.0%}",
            "Predicted Imager Failure Probability": "{:.0%}",
            "Predicted Turnaround Risk": "{:.0%}",
            "Turnaround Days": "{} days",
        }

        active_formatters = {
            column: formatter
            for column, formatter in formatters.items()
            if column in paged_display_queue.columns
        }

        styled_display_queue = (
            paged_display_queue.style
            .apply(highlight_worklist_row, axis=1)
            .format(active_formatters)
        )

        st.dataframe(
            styled_display_queue,
            width="stretch",
            hide_index=True,
        )

        csv_export = display_queue.to_csv(index=False)

        st.download_button(
            label="Export Filtered Queue",
            data=csv_export,
            file_name=(
                f"{workflow_view.lower().replace(' ', '_')}"
                f"_workflow_queue.csv"
            ),
            mime="text/csv",
        )

with reports_tab:
    st.subheader("Executive Reports")

    st.caption(
        "Supervisor-ready operational reporting for workload, quality, "
        "turnaround, and AI-assisted workflow monitoring."
    )

    report_session_statistics = calculate_session_statistics(
        triage_queue
    )

    report_queue_health, report_queue_health_message = (
        calculate_queue_health(triage_queue)
    )

    st.markdown("**Daily Operational Snapshot**")

    report_col1, report_col2, report_col3 = st.columns(3)
    report_col4, report_col5, report_col6 = st.columns(3)

    report_col1.metric(
        "Total Cases",
        len(triage_queue)
    )

    report_col2.metric(
        "Immediate Attention",
        int(
            (
                triage_queue["needs_attention"]
                == "immediate_attention"
            ).sum()
        )
    )

    report_col3.metric(
        "Imager Review",
        int(
            (
                triage_queue["qc_flag"]
                == "imager_qc_review"
            ).sum()
        )
    )

    report_col4.metric(
        "Overdue",
        int(
            (
                triage_queue["case_age_flag"]
                == "overdue"
            ).sum()
        )
    )

    report_col5.metric(
        "Average Turnaround",
        f"{safe_mean(triage_queue, 'turnaround_days'):.1f} days"
    )

    report_col6.metric(
        "Average AI Risk",
        (
            f"{safe_mean(triage_queue, 'predicted_risk_score') * 100:.0f}%"
        )
    )

    if report_queue_health == "Critical":
        st.error(
            f"Queue Health: {report_queue_health}. "
            f"{report_queue_health_message}"
        )

    elif report_queue_health == "Watch":
        st.warning(
            f"Queue Health: {report_queue_health}. "
            f"{report_queue_health_message}"
        )

    else:
        st.success(
            f"Queue Health: {report_queue_health}. "
            f"{report_queue_health_message}"
        )

    st.divider()

    st.markdown("**Workflow Activity Summary**")

    (
        activity_col1,
        activity_col2,
        activity_col3,
        activity_col4,
        activity_col5,
        activity_col6
    ) = st.columns(6)

    activity_col1.metric(
        "Assigned",
        report_session_statistics["assigned"],
    )

    activity_col2.metric(
        "In Imager Review",
        report_session_statistics["qc_review"],
    )

    activity_col3.metric(
        "Awaiting Primary Review",
        report_session_statistics["awaiting_primary_review"],
    )

    activity_col4.metric(
        "Reviewed",
        report_session_statistics["reviewed"],
    )

    activity_col5.metric(
        "Awaiting Sign Out",
        report_session_statistics["awaiting_sign_out"],
    )

    activity_col6.metric(
        "Completed",
        report_session_statistics["completed"],
    )

    st.divider()

    st.markdown("**AI and Quality Summary**")

    ai_report_col1, ai_report_col2, ai_report_col3, ai_report_col4 = (
        st.columns(4)
    )

    ai_report_col1.metric(
        "High AI Risk Cases",
        int(
            (
                triage_queue["predictive_priority_flag"]
                == "high_risk"
            ).sum()
        )
    )

    ai_report_col2.metric(
        "Abnormal Probability",
        (
            f"{safe_mean(
                triage_queue,
                'predicted_abnormal_probability'
            ) * 100:.0f}%"
        )
    )

    ai_report_col3.metric(
        "Imager Failure Risk",
        (
            f"{safe_mean(
                triage_queue,
                'predicted_qc_failure_probability'
            ) * 100:.0f}%"
        )
    )

    ai_report_col4.metric(
        "Turnaround Risk",
        (
            f"{safe_mean(
                triage_queue,
                'predicted_turnaround_risk'
            ) * 100:.0f}%"
        )
    )

    high_risk_diagnoses = (
        triage_queue[
            triage_queue["predictive_priority_flag"]
            == "high_risk"
        ]["diagnosis"]
        .apply(format_workflow_label)
        .value_counts()
    )

    if not high_risk_diagnoses.empty:
        st.markdown("**High-Risk Diagnostic Mix**")

        st.dataframe(
            high_risk_diagnoses
            .rename_axis("Diagnosis")
            .reset_index(name="High-Risk Cases"),
            width="stretch",
            hide_index=True,
        )

    st.divider()

    st.markdown("**Supervisor Notes**")

    supervisor_notes = st.text_area(
        "Operational Notes",
        placeholder=(
            "Enter staffing concerns, escalation notes, "
            "follow-up items, or shift handoff information."
        ),
        key="executive_report_notes",
        height=140,
    )

    daily_operations_report = create_daily_operations_report(
        queue=triage_queue,
        session_statistics=report_session_statistics,
        queue_health=report_queue_health,
        queue_health_message=report_queue_health_message,
        supervisor_notes=supervisor_notes,
    )

    st.divider()

    st.markdown("**Report Export Center**")

    export_col1, export_col2, export_col3 = st.columns(3)

    with export_col1:
        st.download_button(
            label="Download Daily Operations Report",
            data=daily_operations_report,
            file_name=(
                f"cytology_daily_operations_"
                f"{datetime.now().strftime('%Y_%m_%d')}.txt"
            ),
            mime="text/plain",
            width="stretch",
        )

    qc_report_columns = [
        "case_id",
        "diagnosis",
        "qc_flag",
        "predicted_qc_failure_probability",
        "blur_score",
        "artifact_risk_score",
    ]

    available_qc_report_columns = [
        column
        for column in qc_report_columns
        if column in triage_queue.columns
    ]

    qc_report = triage_queue[
        available_qc_report_columns
    ].copy()

    with export_col2:
        st.download_button(
            label="Download Imager Review Summary",
            data=qc_report.to_csv(index=False),
            file_name=(
                f"cytology_imager_review_summary_"
                f"{datetime.now().strftime('%Y_%m_%d')}.csv"
            ),
            mime="text/csv",
            width="stretch",
        )

    ai_report_columns = [
        "case_id",
        "diagnosis",
        "ai_priority_score",
        "predicted_risk_score",
        "predicted_abnormal_probability",
        "predicted_qc_failure_probability",
        "predicted_turnaround_risk",
        "predictive_priority_flag",
    ]

    available_ai_report_columns = [
        column
        for column in ai_report_columns
        if column in triage_queue.columns
    ]

    ai_report = triage_queue[
        available_ai_report_columns
    ].copy()

    with export_col3:
        st.download_button(
            label="Download AI Workflow Report",
            data=ai_report.to_csv(index=False),
            file_name=(
                f"cytology_ai_workflow_report_"
                f"{datetime.now().strftime('%Y_%m_%d')}.csv"
            ),
            mime="text/csv",
            width="stretch",
        )

st.divider()
st.caption("Cytology Workflow Dashboard v4.4 | Conference Reliability")
st.caption(f"Last Refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
