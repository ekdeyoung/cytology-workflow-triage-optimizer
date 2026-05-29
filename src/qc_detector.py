"""
QC detector module.

Future purpose:
Detect image quality issues that may affect cytology workflow,
such as blur, staining variation, low contrast, scan artifacts,
or slides that may need rescanning.
"""

from config import QC_WORKFLOW_CONFIG

QC_REVIEW = QC_WORKFLOW_CONFIG["review_state"]
QC_PASS = QC_WORKFLOW_CONFIG["pass_state"]
QC_SCORE_THRESHOLD = QC_WORKFLOW_CONFIG["score_threshold"]
QC_FLAG_ORDER = QC_WORKFLOW_CONFIG["flag_order"]

def get_qc_issue_types():
    return [
        "blur",
        "air_bubbles",
        "stain_artifact",
        "low_cellularity",
        "coverslip_issue",
        "scan_failure"
    ]

def assign_qc_flag(blur_score, artifact_risk_score):
    if (
        blur_score >= QC_SCORE_THRESHOLD
        or artifact_risk_score >= QC_SCORE_THRESHOLD
    ):
        return QC_REVIEW
    
    return QC_PASS

def get_qc_workflow_states():
    return [
        QC_REVIEW,
        QC_PASS
    ]