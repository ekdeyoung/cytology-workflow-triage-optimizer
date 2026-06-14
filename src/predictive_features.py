def add_predictive_features(cases):
    """
    Adds synthetic predictive workflow features to the cytology case dataset.

    These are not machine learning predictions yet.
    They are rule-based simulated scores that prepare the project for future ML.
    """

    cases = cases.copy()

    cases["predicted_risk_score"] = (
        (cases["blur_score"] * 0.4)
        + (cases["artifact_risk_score"] * 0.6)
    )

    cases["predicted_risk_score"] = (
        cases["predicted_risk_score"].round(2)
    )

    cases["predicted_abnormal_probability"] = 0.10
    
    abnormal_diagnoses = [
        "ascus",
        "lsil",
        "hsil",
    ]
    
    cases.loc[
        cases["diagnosis"].isin(abnormal_diagnoses),
        "predicted_abnormal_probability"
    ] = 0.85
    
    cases["predicted_qc_failure_probability"] = (
        (cases["blur_score"] * 0.5)
        + (cases["artifact_risk_score"] * 0.5)
    ).round(2)

    cases["predicted_turnaround_risk"] = (
        cases["turnaround_days"] / 7
    ).clip(upper=1.0).round(2)

    cases["predictive_priority_flag"] = "standard"

    cases.loc[
        (
            (cases["predicted_risk_score"] >= 0.70)
            |
            (cases["predicted_abnormal_probability"] >= 0.80)
        ),
        "predictive_priority_flag"
    ] = "high_risk"

    return cases

def create_predictive_alerts(cases):
    """
    Creates workflow alerts based on synthetic predictive analytics.
    """

    alerts = []

    cases["ai_priority_score"] = (
        (cases["predicted_risk_score"] * 0.30)
        + (cases["predicted_abnormal_probability"] * 0.35)
        + (cases["predicted_qc_failure_probability"] * 0.20)
        + (cases["predicted_turnaround_risk"] * 0.15)
    ).round(2)
    
    high_risk_cases = cases[
        cases["predictive_priority_flag"] == "high_risk"
    ]

    if len(high_risk_cases) >= 5:
        alerts.append("High AI-predicted risk case volume detected")

    if cases["predicted_qc_failure_probability"].mean() >= 0.50:
        alerts.append("Elevated predicted QC failure risk detected")

    if cases["predicted_turnaround_risk"].mean() >= 0.40:
        alerts.append("Elevated predicted turnaround delay risk detected")

    return alerts

def create_workflow_recommendations(cases):
    """
    Creates AI workflow recommendations based on predictive metrics.
    """

    recommendations = []

    high_risk_cases = cases[
        cases["predictive_priority_flag"] == "high_risk"
    ]

    if len(high_risk_cases) >= 5:
        recommendations.append(
            "Consider assigning additional review resources to high-risk cases."
        )

    if cases["predicted_qc_failure_probability"].mean() >= 0.50:
        recommendations.append(
            "Consider prioritizing imager QC review workload."
        )

    if cases["predicted_turnaround_risk"].mean() >= 0.40:
        recommendations.append(
            "Consider reallocating resources to reduce turnaround delays."
        )

    return recommendations