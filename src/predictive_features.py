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

    cases["predicted_turnaround_risk"] = 0.0

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
