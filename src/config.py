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

WORKFLOW_STATES = {
    "immediate_attention": "immediate_attention",
    "pathologist_review": "pathologist_review",
    "routine": "routine",
}

IMMEDIATE_ATTENTION = WORKFLOW_STATES["immediate_attention"]
PATHOLOGIST_REVIEW = WORKFLOW_STATES["pathologist_review"]
ROUTINE = WORKFLOW_STATES["routine"]

ATTENTION_STATE_ORDER = [
    IMMEDIATE_ATTENTION,
    PATHOLOGIST_REVIEW,
    ROUTINE,
]

PRIORITY_TO_ATTENTION_STATE = {
    1: IMMEDIATE_ATTENTION,
    2: IMMEDIATE_ATTENTION,
    3: PATHOLOGIST_REVIEW,
    4: PATHOLOGIST_REVIEW,
    5: PATHOLOGIST_REVIEW,
    6: ROUTINE,
    7: ROUTINE,
    99: ROUTINE,
}
