"""
Machine learning scoring module.

Future purpose:
Train or apply models that estimate cytology case priority,
abnormality risk, or workflow review urgency.
"""
from triage_utils import ATTENTION_STATE_ORDER

def get_ml_target_labels():
    return ATTENTION_STATE_ORDER

def summarize_workflow_targets(triage_queue):
    return (
        triage_queue["needs_attention"]
        .value_counts()
        .to_dict()
    )