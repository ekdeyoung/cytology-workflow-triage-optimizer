"""
QC detector module.

Future purpose:
Detect image quality issues that may affect cytology workflow,
such as blur, staining variation, low contrast, scan artifacts,
or slides that may need rescanning.
"""

def get_qc_issue_types():
    return [
        "blur",
        "air_bubbles",
        "stain_artifact",
        "low_cellularity",
        "coverslip_issue",
        "scan_failure"
    ]