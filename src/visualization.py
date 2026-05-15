"""
Visualization module.

Future purpose:
Create charts and visual summaries for cytology workload,
turnaround time, QC metrics, and triage performance.
"""

from src.image_features import describe_image_feature_plan
from src.qc_detector import get_qc_issue_types
from src.ml_scoring import get_ml_target_labels


def summarize_ai_workflow_components():
    return {
        "image_features": describe_image_feature_plan(),
        "qc_issue_types": get_qc_issue_types(),
        "ml_target_labels": get_ml_target_labels()
    }