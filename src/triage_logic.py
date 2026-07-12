import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    filename="results/workflow.log",
    filemode="a"
)

import pandas as pd

from datetime import datetime

from triage_utils import (
    create_triage_queue, 
    create_summary_metrics, 
    validate_case_data,
    get_urgent_cases,
    get_pathologist_review_cases,
    get_imager_qc_review_cases,
    interpret_workload,
    create_workflow_alerts,
    PRIORITY_REASON_ORDER,
    IMMEDIATE_ATTENTION,
    PATHOLOGIST_REVIEW,
    ROUTINE,
    ATTENTION_STATE_ORDER,
)

from config import (
    WORKFLOW_THRESHOLDS,
    AI_WORKFLOW_OVERVIEW_FILE,
    SUMMARY_REPORT_FILE,
    TRIAGE_REPORT_PREFIX,
    URGENT_CASES_FILE,
    PATHOLOGIST_REVIEW_FILE,
    HIGH_PRIORITY_FILE,
    IMAGER_QC_REVIEW_FILE,
    STATIC_OUTPUT_FILES,
)

from visualization import summarize_ai_workflow_components

from qc_detector import (
    assign_qc_flag, 
    QC_SCORE_THRESHOLD,
    QC_FLAG_ORDER
)

INPUT_FILE = "data/raw/cytology_cases.csv"
OUTPUT_DIR = "results"

cases = pd.read_csv(INPUT_FILE)
logging.info(f"Loaded Input File: {INPUT_FILE}")

try:
    validate_case_data(cases)
    logging.info("Case Data Validation Passed")

except ValueError as error:
    logging.error(f"Validation Failed: {error}")
    raise

triage_queue = create_triage_queue(cases)

triage_queue["qc_flag"] = triage_queue.apply(
    lambda row: assign_qc_flag(
        row["blur_score"],
        row["artifact_risk_score"]
    ),
    axis=1
)

logging.info(
    f"Processed {len(triage_queue)} Cytology Cases"
)
logging.info("Starting Cytology Workflow Analysis")
print("\n=== FULL TRIAGE QUEUE ===")
print(triage_queue)

urgent_cases = get_urgent_cases(triage_queue)

print("\n=== URGENT CASES ===")
print(urgent_cases)

pathologist_cases = get_pathologist_review_cases(triage_queue)

high_priority_cases = triage_queue[
    triage_queue["priority"] <= 5
]

imager_qc_review_cases = get_imager_qc_review_cases(triage_queue)

print("\n=== PATHOLOGIST REVIEW CASES ===")
print(pathologist_cases)

today = datetime.today().strftime("%Y-%m-%d")

triage_report_file = (
    f"{TRIAGE_REPORT_PREFIX}_{today}.csv"
)

triage_queue.to_csv(
    f"{OUTPUT_DIR}/{triage_report_file}",
    index=False
)
    
urgent_cases.to_csv(
    f"{OUTPUT_DIR}/{URGENT_CASES_FILE}",
    index=False
)

pathologist_cases.to_csv(
    f"{OUTPUT_DIR}/{PATHOLOGIST_REVIEW_FILE}", 
    index=False
)

high_priority_cases.to_csv(
    f"{OUTPUT_DIR}/{HIGH_PRIORITY_FILE}",
    index=False
)

imager_qc_review_cases.to_csv(
    f"{OUTPUT_DIR}/{IMAGER_QC_REVIEW_FILE}",
    index=False
)

logging.info("Workflow Reports Exported Successfully")

logging.info(f"Reports Exported To: {OUTPUT_DIR}")

generated_files = [
    triage_report_file,
    *STATIC_OUTPUT_FILES
]

logging.info(
    f"Generated {len(generated_files)} Output Files"
)

logging.info(
    f"Generated Output Files: {generated_files}"
)


summary = create_summary_metrics(
    triage_queue, 
    urgent_cases, 
    pathologist_cases
)

logging.info(
    "Summary Metrics | "
    f"total_cases={summary['total_cases']} | "
    f"urgent_cases={summary['urgent_cases']} | "
    f"pathologist_review_cases={summary['pathologist_review_cases']} | "
    f"imager_qc_review_cases={summary['imager_qc_review_cases']}"
)

workload_interpretations = interpret_workload(summary)

workflow_alerts = create_workflow_alerts(summary)
for alert in workflow_alerts:
    logging.warning(alert)

with open(
    f"{OUTPUT_DIR}/{SUMMARY_REPORT_FILE}",
    "w"
) as file:

    file.write(f"CYTOLOGY TRIAGE SUMMARY | {today}\n\n")

    file.write(f"Total Cases: {summary['total_cases']}\n")
    file.write(f"Urgent Cases: {summary['urgent_cases']}\n")
    file.write(f"Unsatisfactory Cases: {summary['unsatisfactory_cases']}\n")
    file.write(f"Scan Failures: {summary['imager_scan_failures']}\n")
    file.write(f"Pathologist Review Cases: {summary['pathologist_review_cases']}\n")
    file.write(f"Abnormal Cases: {summary['abnormal_cases']}\n")
   
    file.write("\nDAILY PERCENTAGES\n")
    file.write(f"Urgent %: {summary['urgent_pct']:.1f}%\n")
    file.write(f"Pathologist Review %: {summary['review_pct']:.1f}%\n")
    file.write(f"Abnormal %: {summary['abnormal_pct']:.1f}%\n")
    
    file.write("\nTURNAROUND TIME METRICS\n")

    file.write(f"Average Turnaround Time In Days: {summary['average_turnaround_days']}\n")
    file.write(f"Longest Turnaround Time In Days: {summary['longest_turnaround_days']}\n")
    file.write(
        f"Cases Over {WORKFLOW_THRESHOLDS['turnaround_days']} Days: "
        f"{summary['cases_over_threshold']}\n"
    )

    file.write("\nIMAGER QC METRICS\n")
    file.write(
        f"Imager Review Cases: "
        f"{summary['imager_qc_review_cases']}\n"
    )
    file.write(f"Imager Review %: {summary['imager_review_pct']:.1f}%\n")
    
    file.write("\nQC FLAG BREAKDOWN\n")

    qc_flag_counts = triage_queue["qc_flag"].value_counts()

    qc_flag_order = QC_FLAG_ORDER

    for flag in qc_flag_order:
        count = qc_flag_counts.get(flag, 0)
        file.write(f"{flag}: {count}\n")

    if workflow_alerts:
        file.write("\nWORKFLOW ALERT\n")

        for alert in workflow_alerts:
            file.write(f"{alert}\n")


    file.write("\nWORKLOAD INTERPRETATION\n")

    for interpretation in workload_interpretations:
        file.write(f"- {interpretation}\n")

    file.write("\nPRIORITY REASON BREAKDOWN\n") 

    reason_counts = triage_queue["priority_reason"].value_counts()

    most_common_reason = reason_counts.idxmax()
    most_common_reason_count = reason_counts.max()

    file.write(
        f"Most Common Priority Reason: {most_common_reason} ({most_common_reason_count} Cases)\n"
    )

    file.write("\nDAILY BREAKDOWN\n")

    for reason in PRIORITY_REASON_ORDER:
        matching_cases = triage_queue[
            triage_queue["priority_reason"] == reason
        ]

        if not matching_cases.empty:
            count = len(matching_cases)
            file.write(f"{reason}: {count}\n")


print("\n=== SUMMARY ===")
print("Urgent Cases:", summary["urgent_cases"])
print("Pathologist Review Cases:", summary["pathologist_review_cases"])

print(f"Total Cases: {summary['total_cases']}")
print(f"Urgent %: {summary['urgent_pct']:.1f}%")
print(f"Pathologist Review %: {summary['review_pct']:.1f}%")

print(f"Abnormal Cases: {summary['abnormal_cases']}")
print(f"Scan Failures: {summary['imager_scan_failures']}")
print(f"Unsatisfactory Cases: {summary['unsatisfactory_cases']}")
print(f"Average Turnaround Time In Days: {summary['average_turnaround_days']}")
print(f"Longest Turnaround Time In Days: {summary['longest_turnaround_days']}")
print(
    f"Cases Over {WORKFLOW_THRESHOLDS['turnaround_days']} Days: "
    f"{summary['cases_over_threshold']}"
)
print(f"Imager Review Cases: {summary['imager_qc_review_cases']}")
print(f"Imager Review %: {summary['imager_review_pct']:.1f}%")

ai_workflow_components = summarize_ai_workflow_components()

logging.info(
    f"AI Workflow Components Planned: "
    f"{list(ai_workflow_components.keys())}"
)

logging.info(
    f"Imager Review Cases Identified: "
    f"{summary['imager_qc_review_cases']}"
)

logging.info(
    f"QC Score Threshold Used: {QC_SCORE_THRESHOLD}"
)

logging.info(
    f"Imager Review Flag Order: {QC_FLAG_ORDER}"
)

logging.info(
    f"Priority Reason Reporting Order: {PRIORITY_REASON_ORDER}"
)

attention_states = ATTENTION_STATE_ORDER

logging.info(
    f"Attention Workflow States: {attention_states}"
)

logging.info(
    "ML Target Labels Aligned With Attention Workflow States"
)

with open(
    f"{OUTPUT_DIR}/{AI_WORKFLOW_OVERVIEW_FILE}",
    "w"
) as file:
    file.write("AI WORKFLOW OVERVIEW\n\n")

    for section, items in ai_workflow_components.items():
        file.write(f"{section}\n")

        for item in items:
            file.write(f"- {item}\n")

        file.write("\n")

logging.info("AI Workflow Overview Exported Successfully")

logging.info("Cytology Workflow Completed Successfully")