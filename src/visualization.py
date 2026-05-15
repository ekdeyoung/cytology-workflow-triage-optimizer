"""
Visualization module.

Future purpose:
Create charts and visual summaries for cytology workload,
turnaround time, QC metrics, and triage performance.
"""

from image_features import describe_image_feature_plan
from qc_detector import get_qc_issue_types
from ml_scoring import get_ml_target_labels
from qc_detector import get_qc_workflow_states

def summarize_ai_workflow_components():
    return {
        "image_features": describe_image_feature_plan(),
        "qc_issue_types": get_qc_issue_types(),
        "ml_target_labels": get_ml_target_labels(),
        "qc_workflow_states": get_qc_workflow_states(),
    }