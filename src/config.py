# Operational Thresholds

WORKFLOW_THRESHOLDS = {
    "turnaround_days": 5,
    "urgent_case_pct": 30,
    "abnormal_case_pct": 40,
    "scan_failure_pct": 0.20,
    "qc_review_pct": 50,
}


# Workflow Reporting Order

PRIORITY_REASON_ORDER = [
    "Low cellularity",
    "Scan failure",
    "HSIL detected",
    "LSIL detected",
    "ASCUS detected",
    "Infection detected",
    "Routine normal case"
]


# Workflow State Definitions

IMMEDIATE_ATTENTION = "immediate_attention"
PATHOLOGIST_REVIEW = "pathologist_review"
ROUTINE = "routine"

ATTENTION_STATE_ORDER = [
    IMMEDIATE_ATTENTION,
    PATHOLOGIST_REVIEW,
    ROUTINE
]
