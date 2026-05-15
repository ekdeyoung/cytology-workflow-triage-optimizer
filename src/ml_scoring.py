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