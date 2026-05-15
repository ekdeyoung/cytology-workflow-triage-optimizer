"""
QC detector module.

Future purpose:
Detect image quality issues that may affect cytology workflow,
such as blur, staining variation, low contrast, scan artifacts,
or slides that may need rescanning.
"""

QC_REVIEW = "qc_review"
QC_PASS = "qc_pass"
QC_SCORE_THRESHOLD = 0.7

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