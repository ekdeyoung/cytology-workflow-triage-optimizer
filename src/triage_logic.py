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
    interpret_workload,
    create_workflow_alerts
)

INPUT_FILE = "data/raw/cytology_cases.csv"

cases = pd.read_csv(INPUT_FILE)
logging.info(f"Loaded input file: {INPUT_FILE}")

try:
    validate_case_data(cases)
    logging.info("Case data validation passed")

except ValueError as error:
    logging.error(f"Validation failed: {error}")
    raise


triage_queue = create_triage_queue(cases)
logging.info("=== CYTOLOGY TRIAGE REPORT ===")
print("\n=== FULL TRIAGE QUEUE ===")
print(triage_queue)

urgent_cases = get_urgent_cases(triage_queue)

print("\n=== URGENT CASES ===")
print(urgent_cases)

pathologist_cases = get_pathologist_review_cases(triage_queue)

high_priority_cases = triage_queue[
    triage_queue["priority"] <= 5
]

print("\n=== PATHOLOGIST REVIEW CASES ===")
print(pathologist_cases)

today = datetime.today().strftime("%Y-%m-%d")

triage_queue.to_csv(f"results/triage_report_{today}.csv", index=False)
urgent_cases.to_csv("results/urgent_cases.csv", index=False)
pathologist_cases.to_csv("results/pathologist_review_cases.csv", index=False)
high_priority_cases.to_csv(
    "results/high_priority_cases.csv",
    index=False
)

logging.info("Workflow reports exported successfully")

summary = create_summary_metrics(triage_queue, urgent_cases, pathologist_cases)

workload_interpretations = interpret_workload(summary)

workflow_alerts = create_workflow_alerts(summary)
for alert in workflow_alerts:
    logging.warning(alert)

with open("results/summary_report.txt", "w") as file:
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

    if workflow_alerts:
        file.write("\nWORKFLOW ALERT\n")

        for alert in workflow_alerts:
            file.write(f"{alert}\n")

    file.write("\nWORKLOAD INTERPRETATION\n")

    for interpretation in workload_interpretations:
        file.write(f"- {interpretation}\n")

    file.write("\nPRIORITY REASON BREAKDOWN\n") 

    reason_counts = triage_queue["priority_reason"].value_counts()

    priority_reason_order =[
        "Low cellularity",
        "Scan failure",
        "HSIL detected",
        "LSIL detected",
        "ASCUS detected",
        "Infection detected",
        "Routine normal case"
    ]

    most_common_reason = reason_counts.idxmax()
    most_common_reason_count = reason_counts.max()

    file.write(
        f"Most common priority reason: {most_common_reason} ({most_common_reason_count} cases)\n"
    )

    file.write("\nDAILY BREAKDOWN\n")

    for reason in priority_reason_order:
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

logging.info("Cytology workflow completed successfully")