"""
Visualization module.

Future purpose:
Create charts and visual summaries for cytology workload,
turnaround time, QC metrics, and triage performance.
"""

from config import ML_WORKFLOW_CONFIG
from config import QC_WORKFLOW_CONFIG

AI_WORKFLOW_SECTION_ORDER = [
    "image_features",
    "imager_qc_issue_types",
    "ml_target_labels",
    "qc_workflow_states",
    "qc_score_threshold"
]

def summarize_ai_workflow_components():
    workflow_components = {
        "image_features": ML_WORKFLOW_CONFIG["image_features"],
        "imager_qc_issue_types": ML_WORKFLOW_CONFIG["imager_qc_issue_types"],
        "ml_target_labels": ML_WORKFLOW_CONFIG["ml_target_labels"],
        "qc_workflow_states": ML_WORKFLOW_CONFIG["qc_workflow_states"],
        "qc_score_threshold": [
            QC_WORKFLOW_CONFIG["score_threshold"]
        ],
    }

    ordered_components = {}

    for section in AI_WORKFLOW_SECTION_ORDER:
        ordered_components[section] = workflow_components[section]

    return ordered_components