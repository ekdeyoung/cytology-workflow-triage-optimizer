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

def format_workflow_label(label):
    formatted_label = label.replace(
        "_",
        " "
    ).title()

    formatted_label = formatted_label.replace(
        "Id",
        "ID"
    )

    formatted_label = formatted_label.replace(
        "Qc",
        "QC"
    )

    formatted_label = formatted_label.replace(
        "Hsil",
        "HSIL"
    )

    formatted_label = formatted_label.replace(
        "Lsil",
        "LSIL"
    )

    formatted_label = formatted_label.replace(
        "Ascus",
        "ASCUS"
    )

    return formatted_label

def format_column_label(label):
    formatted_label = label.replace(
        "_",
        " "
    ).title()

    formatted_label = formatted_label.replace(
        "Id",
        "ID"
    )

    formatted_label = formatted_label.replace(
        "Qc",
        "QC"
    )

    formatted_label = formatted_label.replace(
        "Hsil",
        "HSIL"
    )

    formatted_label = formatted_label.replace(
        "Lsil",
        "LSIL"
    )

    formatted_label = formatted_label.replace(
        "Ascus",
        "ASCUS"
    )
    
    return formatted_label


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
        return "Scan Failure"

    return DIAGNOSIS_REASON_MAP.get(
        diagnosis.lower(), 
        "Unknown Finding"
    )


def assign_attention_flag(priority): 
    return PRIORITY_TO_ATTENTION_STATE.get(priority, ROUTINE)
    

def create_triage_queue(df):
    df["received_date"] = pd.to_datetime(df["received_date"])
    df["reported_date"] = pd.to_datetime(df["reported_date"])

    df["turnaround_days"] = (
        df["reported_date"] - df["received_date"]
    ).dt.days

    df["priority"] = df.apply(
        lambda row: assign_priority(
            row["adequacy"], 
            row["scan_status"], 
            row["diagnosis"]
        ), 
        axis=1
    
    )
    df["priority_reason"] = df.apply(
        lambda row: assign_priority_reason(
            row["adequacy"],
            row["scan_status"],
            row["diagnosis"]
        ),
        axis=1
    )

    df["needs_attention"] = df["priority"].apply(assign_attention_flag)

    df = df.sort_values("priority")
    df = df.reset_index(drop=True)

    return df

def create_summary_metrics(triage_queue, urgent_cases, pathologist_cases):
    total_cases = len(triage_queue)

    abnormal_cases = triage_queue[triage_queue["diagnosis"] != "normal"]
    imager_scan_failures = triage_queue[triage_queue["scan_status"] == "fail"]
    unsat_cases = triage_queue[triage_queue["adequacy"] == "unsat"]
    
    urgent_pct = len(urgent_cases) / total_cases * 100
    review_pct = len(pathologist_cases) / total_cases * 100
    abnormal_pct = len(abnormal_cases) / total_cases * 100

    imager_qc_review_cases = triage_queue[
        triage_queue["qc_flag"] == QC_WORKFLOW_CONFIG["review_state"]
    ]
    imager_qc_review_pct = len(imager_qc_review_cases) / total_cases * 100

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
        "imager_qc_review_pct": imager_qc_review_pct,
    }

def validate_case_data(df):
    required_columns = ["case_id", "adequacy", "scan_status", "diagnosis"]

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
    return df[df["needs_attention"] == IMMEDIATE_ATTENTION]

def get_pathologist_review_cases(df):
    return df[df["needs_attention"] == PATHOLOGIST_REVIEW]

def get_imager_qc_review_cases(df):
    return df[df["qc_flag"] == QC_WORKFLOW_CONFIG["review_state"]]

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

    if summary["imager_qc_review_pct"] >= WORKFLOW_THRESHOLDS["imager_qc_review_pct"]:
        interpretations.append("Elevated Imager QC Review Burden")

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

    if summary["imager_qc_review_pct"] >= WORKFLOW_THRESHOLDS["imager_qc_review_pct"]:
        alerts.append("High Imager QC Review Volume Detected")

    return alerts