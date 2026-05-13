import pandas as pd

def assign_priority(adequacy, scan_status, diagnosis):
    
    if adequacy.lower() in ["unsat", "unsatisfactory"]:
        return 1
    
    elif scan_status.lower() in ["fail", "failed"]:
        return 2
    
    diagnosis_map = {
        "hsil": 3,
        "lsil": 4,
        "ascus": 5,
        "infection": 6,
        "normal": 7
    }

    return diagnosis_map.get(diagnosis.lower(), 99)

def assign_priority_reason(adequacy, scan_status, diagnosis):

    if adequacy.lower() in ["unsat", "unsatisfactory"]:
        return "Low cellularity"
    
    elif scan_status.lower() in ["fail", "failed"]:
        return "Scan failure"
    
    diagnosis_map = {
        "hsil": "HSIL detected",
        "lsil": "LSIL detected",
        "ascus": "ASCUS detected",
        "infection": "Infection detected",
        "normal": "Routine normal case"
    }

    return diagnosis_map.get(diagnosis.lower(), "Unknown finding")

def assign_attention_flag(priority): 
    if priority in [1, 2]:
        return "immediate_attention" 
    elif priority in [3, 4, 5]:
        return "pathologist_review"
    else:
        return "routine"
    

def create_triage_queue(df):
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
    scan_failures = triage_queue[triage_queue["scan_status"] == "fail"]
    unsat_cases = triage_queue[triage_queue["adequacy"] == "unsat"]
    
    urgent_pct = len(urgent_cases) / total_cases * 100
    review_pct = len(pathologist_cases) / total_cases * 100
    abnormal_pct = len(abnormal_cases) / total_cases * 100


    return {
        "total_cases": total_cases,
        "urgent_cases": len(urgent_cases),
        "pathologist_review_cases": len(pathologist_cases),
        "urgent_pct": urgent_pct,
        "review_pct": review_pct,
        "abnormal_pct": abnormal_pct,
        "abnormal_cases": len(abnormal_cases),
        "scan_failures": len(scan_failures),
        "unsatisfactory_cases": len(unsat_cases), 
    }

def validate_case_data(df):
    required_columns = ["case_id", "adequacy", "scan_status", "diagnosis"]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"Missing required column: {column}")
    
    allowed_adequacy = ["sat", "unsat", "unsatisfactory"]
    allowed_scan_status = ["pass", "fail", "failed"]
    allowed_diagnosis = ["normal", "infection", "ascus", "lsil", "hsil"]

    for value in df["adequacy"]:
            if value.lower() not in allowed_adequacy:
                raise ValueError(f"Unexpected adequacy value: {value}")

    for value in df["scan_status"]:
        if value.lower() not in allowed_scan_status:
            raise ValueError(f"Unexpected scan_status value: {value}")
        
    for value in df["diagnosis"]:
        if value.lower() not in allowed_diagnosis:
            raise ValueError(f"Unexpected diagnosis value: {value}")
        
    return True

def get_urgent_cases(df):
    return df[df["needs_attention"] == "immediate_attention"]

def get_pathologist_review_cases(df):
    return df[df["needs_attention"] == "pathologist_review"]

def interpret_workload(summary):

    interpretations = []

    if summary["urgent_pct"] >= 30:
        interpretations.append("High urgent workload")

    if summary["abnormal_pct"] >= 40:
        interpretations.append("Elevated abnormal case rate")

    if summary["scan_failures"] / summary["total_cases"] >= 0.20:
        interpretations.append("Elevated scan failure rate")

    if not interpretations:
        interpretations.append("Workflow within expected limits")

    return interpretations

def create_workflow_alerts(summary):

    alerts = []

    if summary["urgent_pct"] >= 30:
        alerts.append("High urgent case volume detected")

    if summary["scan_failures"] / summary["total_cases"] >= 0.20:
        alerts.append("High scan failure rate detected")

    return alerts