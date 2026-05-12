import pandas as pd
from datetime import datetime
from triage_utils import create_triage_queue, create_summary_metrics, validate_case_data

cases = pd.read_csv("data/raw/cytology_cases.csv")
validate_case_data(cases)



triage_queue = create_triage_queue(cases)
print("\n=== CYTOLOGY TRIAGE REPORT ===\n")
print("\n=== FULL TRIAGE QUEUE ===")
print(triage_queue)

urgent_cases = triage_queue[triage_queue["needs_attention"] == "immediate_attention"]

print("\n=== URGENT CASES ===")
print(urgent_cases)

pathologist_cases = triage_queue[triage_queue["needs_attention"] == "pathologist_review"]

print("\n=== PATHOLOGIST REVIEW CASES ===")
print(pathologist_cases)

today = datetime.today().strftime("%Y-%m-%d")

triage_queue.to_csv(f"results/triage_report_{today}.csv", index=False)
urgent_cases.to_csv("results/urgent_cases.csv", index=False)
pathologist_cases.to_csv("results/pathologist_review_cases.csv", index=False)


summary = create_summary_metrics(triage_queue, urgent_cases, pathologist_cases)

with open("results/summary_report.txt", "w") as file:
    file.write("CYTOLOGY TRIAGE SUMMARY\n\n")
    file.write(f"Urgent cases: {summary['urgent_cases']}\n")
    file.write(f"Pathologist review cases: {summary['pathologist_review_cases']}\n")
    file.write(f"Total cases: {summary['total_cases']}\n")
    file.write(f"Urgent %: {summary['urgent_pct']:.1f}%\n")
    file.write(f"Pathologist review %: {summary['review_pct']:.1f}%\n")
    file.write(f"Abnormal cases: {summary['abnormal_cases']}\n")
    file.write(f"Scan failures: {summary['scan_failures']}\n")
    file.write(f"Unsatisfactory cases: {summary['unsatisfactory_cases']}\n")

print("\n=== SUMMARY ===")
print("Urgent cases:", summary["urgent_cases"])
print("Pathologist review cases:", summary["pathologist_review_cases"])

print(f"Total cases: {summary['total_cases']}")
print(f"Urgent %: {summary['urgent_pct']:.1f}%")
print(f"Pathologist review %: {summary['review_pct']:.1f}%")

print(f"Abnormal cases: {summary['abnormal_cases']}")
print(f"Scan failures: {summary['scan_failures']}")
print(f"Unsatisfactory cases: {summary['unsatisfactory_cases']}")