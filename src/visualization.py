"""
Visualization module.

Future purpose:
Create charts and visual summaries for cytology workload,
turnaround time, QC metrics, and triage performance.
"""

AI_WORKFLOW_SECTION_ORDER = [
    "image_features",
    "qc_issue_types",
    "ml_target_labels",
    "qc_workflow_states",
    "qc_score_threshold"
]

from image_features import describe_image_feature_plan
from ml_scoring import get_ml_target_labels
from qc_detector import (
    get_qc_issue_types,
    get_qc_workflow_states,
    QC_SCORE_THRESHOLD
)

def summarize_ai_workflow_components():
    workflow_components = {
        "image_features": describe_image_feature_plan(),
        "qc_issue_types": get_qc_issue_types(),
        "ml_target_labels": get_ml_target_labels(),
        "qc_workflow_states": get_qc_workflow_states(),
        "qc_score_threshold": [QC_SCORE_THRESHOLD],
    }

    ordered_components = {}

    for section in AI_WORKFLOW_SECTION_ORDER:
        ordered_components[section] = workflow_components[section]

    return ordered_components