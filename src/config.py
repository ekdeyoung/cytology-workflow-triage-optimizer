# Operational Thresholds

WORKFLOW_THRESHOLDS = {
    "turnaround_days": 5,
    "urgent_case_pct": 30,
    "abnormal_case_pct": 40,
    "imager_scan_failure_pct": 0.20,
    "imager_review_pct": 50,
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

# Legacy Operational Triage States
#
# These states support the current v4 dashboard and should not be used
# as the final clinical workflow-routing model.

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

# Cytology Specimen Categories

SPECIMEN_CATEGORIES = {
    "gynecologic": "gynecologic",
    "non_gynecologic": "non_gynecologic",
}


# Cytology Workflow Types

WORKFLOW_TYPES = {
    "routine": "routine",
    "rose": "rose",
}

GYNECOLOGIC = SPECIMEN_CATEGORIES["gynecologic"]
NON_GYNECOLOGIC = SPECIMEN_CATEGORIES["non_gynecologic"]

ROUTINE_WORKFLOW = WORKFLOW_TYPES["routine"]
ROSE_WORKFLOW = WORKFLOW_TYPES["rose"]


# Cytology Workflow Stages

WORKFLOW_STAGES = {
    "specimen_received": "specimen_received",
    "slide_preparation": "slide_preparation",
    "digital_imaging": "digital_imaging",
    "imager_review": "imager_review",
    "rose_procedure": "rose_procedure",
    "rose_adequacy_assessment": "rose_adequacy_assessment",
    "laboratory_processing": "laboratory_processing",
    "primary_cytologist_screening": "primary_cytologist_screening",
    "quality_control_review": "quality_control_review",
    "pathologist_review": "pathologist_review",
    "final_sign_out": "final_sign_out",
    "discrepancy_review": "discrepancy_review",
    "educational_review": "educational_review",
}


# General Workflow Statuses

WORKFLOW_STATUS = {
    "not_started": "not_started",
    "pending": "pending",
    "in_progress": "in_progress",
    "ready": "ready",
    "completed": "completed",
    "on_hold": "on_hold",
    "cancelled": "cancelled",
}


# Laboratory Processing Statuses

PROCESSING_STATUS = {
    "not_started": "not_started",
    "in_progress": "in_progress",
    "ready_for_screening": "ready_for_screening",
    "delayed": "delayed",
    "completed": "completed",
}


# Review Roles

WORKFLOW_ROLES = {
    "performing_rose_cytologist": "performing_rose_cytologist",
    "primary_cytologist": "primary_cytologist",
    "quality_control_reviewer": "quality_control_reviewer",
    "pathologist": "pathologist",
    "laboratory_processing": "laboratory_processing",
    "supervisor": "supervisor",
}

# Clinical Routing Rules

CLINICAL_ROUTING_CONFIG = {
    "gynecologic_negative": {
        "requires_primary_cytologist_screening": True,
        "eligible_for_quality_control_review": True,
        "quality_control_selection_pct": 10,
        "requires_pathologist_review": False,
        "cytologist_sign_out_allowed": True,
    },
    "gynecologic_abnormal": {
        "requires_primary_cytologist_screening": True,
        "eligible_for_quality_control_review": False,
        "requires_pathologist_review": True,
        "cytologist_sign_out_allowed": False,
    },
    "non_gynecologic": {
        "requires_primary_cytologist_screening": True,
        "eligible_for_quality_control_review": False,
        "requires_pathologist_review": True,
        "cytologist_sign_out_allowed": False,
    },
    "rose": {
        "requires_rose_cytologist": True,
        "requires_adequacy_assessment": True,
        "requires_laboratory_processing": True,
        "requires_primary_cytologist_screening": True,
        "requires_pathologist_review": True,
        "requires_discrepancy_review": True,
    },
}

WORKFLOW_CAPABILITIES = {
    "digital_imaging_enabled": True,
    "imager_review_enabled": True,
}

# Canonical Workflow Templates

WORKFLOW_TEMPLATES = {
    "gynecologic_routine": [
        WORKFLOW_STAGES["specimen_received"],
        WORKFLOW_STAGES["slide_preparation"],
        WORKFLOW_STAGES["digital_imaging"],
        WORKFLOW_STAGES["imager_review"],
        WORKFLOW_STAGES["primary_cytologist_screening"],
    ],
    "non_gynecologic_routine": [
        WORKFLOW_STAGES["specimen_received"],
        WORKFLOW_STAGES["slide_preparation"],
        WORKFLOW_STAGES["digital_imaging"],
        WORKFLOW_STAGES["imager_review"],
        WORKFLOW_STAGES["primary_cytologist_screening"],
        WORKFLOW_STAGES["pathologist_review"],
        WORKFLOW_STAGES["final_sign_out"],
    ],
    "rose": [
        WORKFLOW_STAGES["rose_procedure"],
        WORKFLOW_STAGES["rose_adequacy_assessment"],
        WORKFLOW_STAGES["laboratory_processing"],
        WORKFLOW_STAGES["primary_cytologist_screening"],
        WORKFLOW_STAGES["pathologist_review"],
        WORKFLOW_STAGES["final_sign_out"],
        WORKFLOW_STAGES["discrepancy_review"],
    ],
}

GYNECOLOGIC_POST_SCREENING_ROUTES = {
    "negative_not_selected_for_qc": [
        WORKFLOW_STAGES["final_sign_out"],
    ],
    "negative_selected_for_qc": [
        WORKFLOW_STAGES["quality_control_review"],
        WORKFLOW_STAGES["final_sign_out"],
    ],
    "abnormal_or_questionable": [
        WORKFLOW_STAGES["pathologist_review"],
        WORKFLOW_STAGES["final_sign_out"],
    ],
}

DISCREPANCY_REVIEW_ROUTES = {
    "no_discrepancy": [],
    "discrepancy_found": [
        WORKFLOW_STAGES["educational_review"],
    ],
    "teaching_case": [
        WORKFLOW_STAGES["educational_review"],
    ],
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

IMAGER_REVIEW_CONFIG = QC_WORKFLOW_CONFIG

QUALITY_CONTROL_REVIEW_CONFIG = {
    "selection_pct": 10,
    "eligible_specimen_category": GYNECOLOGIC,
    "eligible_screening_result": "negative",
    "review_state": "quality_control_review",
    "completed_state": "quality_control_completed",
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