# Operational Thresholds

TURNAROUND_THRESHOLD_DAYS = 5

URGENT_CASE_THRESHOLD_PCT = 30
ABNORMAL_CASE_THRESHOLD_PCT = 40
SCAN_FAILURE_THRESHOLD_PCT = 0.20
QC_REVIEW_THRESHOLD_PCT = 50


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
