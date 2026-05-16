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
    TURNAROUND_THRESHOLD_DAYS,
    create_triage_queue, 
    create_summary_metrics, 
    validate_case_data,
    get_urgent_cases,
    get_pathologist_review_cases,
    get_qc_review_cases,
    interpret_workload,
    create_workflow_alerts,
    PRIORITY_REASON_ORDER,
    IMMEDIATE_ATTENTION,
    PATHOLOGIST_REVIEW,
    ROUTINE,
    ATTENTION_STATE_ORDER,
)

from visualization import summarize_ai_workflow_components

from qc_detector import (
    assign_qc_flag, 
    QC_SCORE_THRESHOLD,
    QC_FLAG_ORDER
)

INPUT_FILE = "data/raw/cytology_cases.csv"
OUTPUT_DIR = "results"

AI_WORKFLOW_OVERVIEW_FILE = "ai_workflow_overview.txt"

SUMMARY_REPORT_FILE = "summary_report.txt"

TRIAGE_REPORT_PREFIX = "triage_report"

STATIC_OUTPUT_FILES = [
    SUMMARY_REPORT_FILE,
    "urgent_cases.csv",
    "pathologist_review_cases.csv",
    "high_priority_cases.csv",
    "qc_review_cases.csv",
    AI_WORKFLOW_OVERVIEW_FILE
]

cases = pd.read_csv(INPUT_FILE)
logging.info(f"Loaded input file: {INPUT_FILE}")

try:
    validate_case_data(cases)
    logging.info("Case data validation passed")

except ValueError as error:
    logging.error(f"Validation failed: {error}")
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
    f"Processed {len(triage_queue)} cytology cases"
)
logging.info("Starting cytology workflow analysis")
print("\n=== FULL TRIAGE QUEUE ===")
print(triage_queue)

urgent_cases = get_urgent_cases(triage_queue)

print("\n=== URGENT CASES ===")
print(urgent_cases)

pathologist_cases = get_pathologist_review_cases(triage_queue)

high_priority_cases = triage_queue[
    triage_queue["priority"] <= 5
]

qc_review_cases = get_qc_review_cases(triage_queue)

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
    
urgent_cases.to_csv("results/urgent_cases.csv", index=False)
pathologist_cases.to_csv("results/pathologist_review_cases.csv", index=False)
high_priority_cases.to_csv(
    "results/high_priority_cases.csv",
    index=False
)
qc_review_cases.to_csv(
    "results/qc_review_cases.csv",
    index=False
)

logging.info("Workflow reports exported successfully")

logging.info(f"Reports exported to: {OUTPUT_DIR}")

generated_files = [
    triage_report_file,
    *STATIC_OUTPUT_FILES
]

logging.info(
    f"Generated {len(generated_files)} output files"
)

logging.info(
    f"Generated output files: {generated_files}"
)


summary = create_summary_metrics(
    triage_queue, 
    urgent_cases, 
    pathologist_cases
)

logging.info(
    "Summary metrics | "
    f"total_cases={summary['total_cases']} | "
    f"urgent_cases={summary['urgent_cases']} | "
    f"pathologist_review_cases={summary['pathologist_review_cases']} | "
    f"qc_review_cases={summary['qc_review_cases']}"
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

    file.write(f"Total cases: {summary['total_cases']}\n")
    file.write(f"Urgent cases: {summary['urgent_cases']}\n")
    file.write(f"Unsatisfactory cases: {summary['unsatisfactory_cases']}\n")
    file.write(f"Scan failures: {summary['scan_failures']}\n")
    file.write(f"Pathologist review cases: {summary['pathologist_review_cases']}\n")
    file.write(f"Abnormal cases: {summary['abnormal_cases']}\n")
   
    file.write("\nDAILY PERCENTAGES\n")
    file.write(f"Urgent %: {summary['urgent_pct']:.1f}%\n")
    file.write(f"Pathologist review %: {summary['review_pct']:.1f}%\n")
    file.write(f"Abnormal %: {summary['abnormal_pct']:.1f}%\n")
    
    file.write("\nTURNAROUND TIME METRICS\n")

    file.write(f"Average turnaround days: {summary['average_turnaround_days']}\n")
    file.write(f"Longest turnaround days: {summary['longest_turnaround_days']}\n")
    file.write(
        f"Cases over {TURNAROUND_THRESHOLD_DAYS} days: "
        f"{summary['cases_over_threshold']}\n"
    )

    file.write("\nQC METRICS\n")
    file.write(
        f"QC review cases: "
        f"{summary['qc_review_cases']}\n"
    )
    file.write(f"QC review %: {summary['qc_review_pct']:.1f}%\n")
    
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
        f"Most common priority reason: {most_common_reason} ({most_common_reason_count} cases)\n"
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
print("Urgent cases:", summary["urgent_cases"])
print("Pathologist review cases:", summary["pathologist_review_cases"])

print(f"Total cases: {summary['total_cases']}")
print(f"Urgent %: {summary['urgent_pct']:.1f}%")
print(f"Pathologist review %: {summary['review_pct']:.1f}%")

print(f"Abnormal cases: {summary['abnormal_cases']}")
print(f"Scan failures: {summary['scan_failures']}")
print(f"Unsatisfactory cases: {summary['unsatisfactory_cases']}")
print(f"Average turnaround days: {summary['average_turnaround_days']}")
print(f"Longest turnaround days: {summary['longest_turnaround_days']}")
print(
    f"Cases over {TURNAROUND_THRESHOLD_DAYS} days: "
    f"{summary['cases_over_threshold']}"
)
print(f"QC review cases: {summary['qc_review_cases']}")
print(f"QC review %: {summary['qc_review_pct']:.1f}%")

ai_workflow_components = summarize_ai_workflow_components()

logging.info(
    f"AI workflow components planned: "
    f"{list(ai_workflow_components.keys())}"
)

logging.info(
    f"QC review cases identified: "
    f"{summary['qc_review_cases']}"
)

logging.info(
    f"QC score threshold used: {QC_SCORE_THRESHOLD}"
)

logging.info(
    f"QC flag reporting order: {QC_FLAG_ORDER}"
)

logging.info(
    f"Priority reason reporting order: {PRIORITY_REASON_ORDER}"
)

attention_states = ATTENTION_STATE_ORDER

logging.info(
    f"Attention workflow states: {attention_states}"
)

logging.info(
    "ML target labels aligned with attention workflow states"
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

logging.info("AI workflow overview exported successfully")

logging.info("Cytology workflow completed successfully")