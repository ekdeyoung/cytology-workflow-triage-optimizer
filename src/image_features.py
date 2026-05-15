"""
Image feature extraction module.

Future purpose:
Extract simple image measurements such as brightness, contrast,
blur score, color variation, and other features that can support
QC checks or ML triage scoring.
"""

def describe_image_feature_plan():
    return [
        "brightness",
        "contrast",
        "blur_score",
        "color_variation",
        "artifact_risk"
    ]