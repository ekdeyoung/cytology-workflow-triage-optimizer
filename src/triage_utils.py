import pandas as pd

from config import (
    WORKFLOW_THRESHOLDS,
    PRIORITY_REASON_ORDER,
    IMMEDIATE_ATTENTION,
    PATHOLOGIST_REVIEW,
    ROUTINE,
    ATTENTION_STATE_ORDER,
    PRIORITY_TO_ATTENTION_STATE,
    DIAGNOSIS_PRIORITY_MAP,
    DIAGNOSIS_REASON_MAP,
    QC_WORKFLOW_CONFIG,
)

def format_label(label):
    formatted_label = label.replace(
        "_",
        " "
    ).title()

    formatted_label = formatted_label.replace("Ai", "AI")
    formatted_label = formatted_label.replace("Id", "ID")
    formatted_label = formatted_label.replace("Qc", "QC")
    formatted_label = formatted_label.replace("Hsil", "HSIL")
    formatted_label = formatted_label.replace("Lsil", "LSIL")
    formatted_label = formatted_label.replace("Ascus", "ASCUS")

    return formatted_label

def format_workflow_label(label):

    return format_label(label)

def format_column_label(label):
    
    return format_label(label)


def assign_priority(adequacy, scan_status, diagnosis):
    
    if adequacy.lower() in ["unsat", "unsatisfactory"]:
        return 1
    
    elif scan_status.lower() in ["fail", "failed"]:
        return 2

    return DIAGNOSIS_PRIORITY_MAP.get(diagnosis.lower(), 99)


def assign_priority_reason(adequacy, scan_status, diagnosis):

    if adequacy.lower() in ["unsat", "unsatisfactory"]:
        return "Low Cellularity"
    
    elif scan_status.lower() in ["fail", "failed"]:
        return "Imager Scan Failure"

    return DIAGNOSIS_REASON_MAP.get(
        diagnosis.lower(), 
        "Unknown Finding"
    )


def assign_attention_flag(priority): 
    return PRIORITY_TO_ATTENTION_STATE.get(priority, ROUTINE)
    
def assign_case_age_flag(turnaround_days):
    if turnaround_days > 7:
        return "overdue"
    if turnaround_days > 5:
        return "aging"
    return "within_target"

def create_triage_queue(df):
    triage_queue = df.copy()

    triage_queue["received_date"] = pd.to_datetime(
        triage_queue["received_date"]
    )

    triage_queue["reported_date"] = pd.to_datetime(
        triage_queue["reported_date"]
    )

    triage_queue["turnaround_days"] = (
        triage_queue["reported_date"]
        - triage_queue["received_date"]
    ).dt.days

    triage_queue["case_age_flag"] = (
        triage_queue["turnaround_days"]
        .apply(assign_case_age_flag)
    )

    triage_queue["priority"] = triage_queue.apply(
        lambda row: assign_priority(
            row["adequacy"],
            row["scan_status"],
            row["diagnosis"],
        ),
        axis=1,
    )

    triage_queue["priority_reason"] = triage_queue.apply(
        lambda row: assign_priority_reason(
            row["adequacy"],
            row["scan_status"],
            row["diagnosis"],
        ),
        axis=1,
    )

    triage_queue["needs_attention"] = (
        triage_queue["priority"]
        .apply(assign_attention_flag)
    )

    triage_queue = (
        triage_queue
        .sort_values("priority")
        .reset_index(drop=True)
    )

    return triage_queue

def create_summary_metrics(triage_queue, urgent_cases, pathologist_cases):
    total_cases = len(triage_queue)

    diagnosis_values = (
        triage_queue["diagnosis"]
        .astype(str)
        .str.lower()
    )

    scan_status_values = (
        triage_queue["scan_status"]
        .astype(str)
        .str.lower()
    )

    adequacy_values = (
        triage_queue["adequacy"]
        .astype(str)
        .str.lower()
    )

    abnormal_cases = triage_queue[
        diagnosis_values != "normal"
    ]

    imager_scan_failures = triage_queue[
        scan_status_values.isin(["fail", "failed"])
    ]

    unsat_cases = triage_queue[
        adequacy_values.isin(["unsat", "unsatisfactory"])
    ]

    overdue_cases = triage_queue[triage_queue["case_age_flag"] == "overdue"]
    aging_cases = triage_queue[triage_queue["case_age_flag"] == "aging"]

    urgent_pct = len(urgent_cases) / total_cases * 100
    review_pct = len(pathologist_cases) / total_cases * 100
    abnormal_pct = len(abnormal_cases) / total_cases * 100

    imager_qc_review_cases = triage_queue[
        triage_queue["qc_flag"] == QC_WORKFLOW_CONFIG["review_state"]
    ]
    imager_review_pct = len(imager_qc_review_cases) / total_cases * 100

    return {
        "total_cases": total_cases,
        "urgent_cases": len(urgent_cases),
        "pathologist_review_cases": len(pathologist_cases),
        "urgent_pct": urgent_pct,
        "review_pct": review_pct,
        "abnormal_pct": abnormal_pct,
        "abnormal_cases": len(abnormal_cases),
        "imager_scan_failures": len(imager_scan_failures),
        "unsatisfactory_cases": len(unsat_cases),
        "average_turnaround_days": round(
            triage_queue["turnaround_days"].mean(), 1
        ),
        "longest_turnaround_days": (
            triage_queue["turnaround_days"].max()
        ),
        "cases_over_threshold": (
            triage_queue["turnaround_days"] > WORKFLOW_THRESHOLDS["turnaround_days"]
        ).sum(), 
        "imager_qc_review_cases": len(imager_qc_review_cases),
        "imager_review_pct": imager_review_pct,
        "overdue_cases": len(overdue_cases),
        "aging_cases": len(aging_cases),
    }

def validate_case_data(df):
    required_columns = [
        "case_id",
        "adequacy",
        "scan_status",
        "diagnosis",
        "received_date",
        "reported_date",
        "blur_score",
        "artifact_risk_score",
    ]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"Missing Required Column: {column}")
    
    allowed_adequacy = ["sat", "unsat", "unsatisfactory"]
    allowed_scan_status = ["pass", "fail", "failed"]
    allowed_diagnosis = ["normal", "infection", "ascus", "lsil", "hsil"]

    for value in df["adequacy"]:
        if value.lower() not in allowed_adequacy:
            raise ValueError(f"Unexpected Adequacy Value: {value}")

    for value in df["scan_status"]:
        if value.lower() not in allowed_scan_status:
            raise ValueError(f"Unexpected scan_status Value: {value}")
        
    for value in df["diagnosis"]:
        if value.lower() not in allowed_diagnosis:
            raise ValueError(f"Unexpected Diagnosis Value: {value}")
        
    return True

def get_urgent_cases(df):
    return df[
        df["needs_attention"] == IMMEDIATE_ATTENTION
    ].copy()

def get_priority_review_cases(df):
    """
    Return cases placed in the legacy review-priority category.

    This is an operational triage category, not a definitive clinical
    pathologist-routing decision.
    """
    return df[
        df["needs_attention"] == PATHOLOGIST_REVIEW
    ].copy()

def get_pathologist_review_cases(df):
    """
    Temporary compatibility wrapper for the existing dashboard.

    The returned cases represent the legacy review-priority category,
    not final specimen-specific pathologist routing.
    """
    return get_priority_review_cases(df)

def get_imager_qc_review_cases(df):
    return df[
        df["qc_flag"] == QC_WORKFLOW_CONFIG["review_state"]
    ].copy()

def interpret_workload(summary):

    interpretations = []

    if (summary["urgent_pct"] 
        >= WORKFLOW_THRESHOLDS["urgent_case_pct"]):
        interpretations.append("High Urgent Workload")

    if (summary["abnormal_pct"] 
        >= WORKFLOW_THRESHOLDS["abnormal_case_pct"]):
        interpretations.append("Elevated Abnormal Case Rate")

    if (summary["imager_scan_failures"] / summary["total_cases"] 
        >= WORKFLOW_THRESHOLDS["imager_scan_failure_pct"]):
        interpretations.append("Elevated Imager Failure Rate")

    if summary["cases_over_threshold"] > 0:
        interpretations.append("Delayed Turnaround Time Cases Present")

    if summary["imager_review_pct"] >= WORKFLOW_THRESHOLDS["imager_review_pct"]:
        interpretations.append("Elevated Imager Review Burden")
    
    if summary["overdue_cases"] > 0:
        interpretations.append("Overdue Case Backlog Present")

    if summary["aging_cases"] > 0:
        interpretations.append("Cases Approaching Delay Threshold")

    if not interpretations:
        interpretations.append("Workflow Within Expected Limits")

    return interpretations

def create_workflow_alerts(summary):

    alerts = []

    if summary["urgent_pct"] >= WORKFLOW_THRESHOLDS["urgent_case_pct"]:
        alerts.append("High Urgent Case Volume Detected")

    if (summary["imager_scan_failures"] / summary["total_cases"] 
        >= WORKFLOW_THRESHOLDS["imager_scan_failure_pct"]):
        alerts.append("High Scan Failure Rate Detected")

    if summary["cases_over_threshold"] > 0:
        alerts.append("Cases Exceeding Turnaround Time Threshold Detected")

    if summary["imager_review_pct"] >= WORKFLOW_THRESHOLDS["imager_review_pct"]:
        alerts.append("High Imager Review Volume Detected")

    if summary["overdue_cases"] > 0:
        alerts.append("Overdue Cases Require Review")

    if summary["aging_cases"] > 0:
        alerts.append("Cases Approaching Turnaround Threshold")

    return alerts