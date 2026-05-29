# Operational Thresholds

WORKFLOW_THRESHOLDS = {
    "turnaround_days": 5,
    "urgent_case_pct": 30,
    "abnormal_case_pct": 40,
    "imager_scan_failure_pct": 0.20,
    "imager_qc_review_pct": 50,
}


# Workflow Reporting Order

PRIORITY_REASON_ORDER = [
    "Low Cellularity",
    "Imager Scan Failure",
    "HSIL Detected",
    "LSIL Detected",
    "ASCUS Detected",
    "Infection Detected",
    "Routine Normal Case",
]

# Diagnosis Workflow Configuration

DIAGNOSIS_PRIORITY_MAP = {
    "hsil": 3,
    "lsil": 4,
    "ascus": 5,
    "infection": 6,
    "normal": 7,
}

DIAGNOSIS_REASON_MAP = {
    "hsil": "HSIL Detected",
    "lsil": "LSIL Detected",
    "ascus": "ASCUS Detected",
    "infection": "Infection Detected",
    "normal": "Routine Normal Case",
}


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


# QC Workflow Configuration

QC_WORKFLOW_CONFIG = {
    "score_threshold": 0.7,
    "review_state": "imager_qc_review",
    "pass_state": "imager_qc_pass",
    "flag_order": [
        "imager_qc_review",
        "imager_qc_pass",
    ],
}


# ML Workflow Configuration

ML_WORKFLOW_CONFIG = {
    "image_features": [
        "blur_score",
        "artifact_risk_score",
        "cellularity_score",
    ],
    "imager_qc_issue_types": [
        "blur",
        "air_bubbles",
        "stain_artifact",
        "low_cellularity",
        "coverslip_issue",
        "imager_scan_failure",
    ],
    "ml_target_labels": ATTENTION_STATE_ORDER,
    "qc_workflow_states": QC_WORKFLOW_CONFIG["flag_order"],
}


# Export File Configuration

AI_WORKFLOW_OVERVIEW_FILE = "ai_workflow_overview.txt"

SUMMARY_REPORT_FILE = "summary_report.txt"

TRIAGE_REPORT_PREFIX = "triage_report"

URGENT_CASES_FILE = "urgent_cases.csv"
PATHOLOGIST_REVIEW_FILE = "pathologist_review_cases.csv"
HIGH_PRIORITY_FILE = "high_priority_cases.csv"
IMAGER_QC_REVIEW_FILE = "imager_qc_review_cases.csv"

STATIC_OUTPUT_FILES = [
    SUMMARY_REPORT_FILE,
    URGENT_CASES_FILE,
    PATHOLOGIST_REVIEW_FILE,
    HIGH_PRIORITY_FILE,
    IMAGER_QC_REVIEW_FILE,
    AI_WORKFLOW_OVERVIEW_FILE,
]