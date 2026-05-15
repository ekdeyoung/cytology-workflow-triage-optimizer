"""
Machine learning scoring module.

Future purpose:
Train or apply models that estimate cytology case priority,
abnormality risk, or workflow review urgency.
"""

def get_ml_target_labels():
    return [
        "immediate_attention",
        "pathologist_review",
        "routine"
    ]

def summarize_workflow_targets(triage_queue):
    return (
        triage_queue["needs_attention"]
        .value_counts()
        .to_dict()
    )