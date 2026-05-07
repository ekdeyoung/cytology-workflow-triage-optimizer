from triage_utils import create_triage_queue

from datetime import datetime

triage_queue = create_triage_queue("data/raw/cytology_cases.csv")
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

total_cases = len(triage_queue)

urgent_pct = len(urgent_cases) / total_cases * 100
review_pct = len(pathologist_cases) / total_cases * 100

abnormal_cases = triage_queue[triage_queue["diagnosis"] != "normal"]

scan_failures = triage_queue[triage_queue["scan_status"] == "fail"]

unsat_cases = triage_queue[triage_queue["adequacy"] == "unsat"]

with open("results/summary_report.txt", "w") as file:
    file.write("CYTOLOGY TRIAGE SUMMARY\n\n")
    file.write(f"Urgent cases: {len(urgent_cases)}\n")
    file.write(f"Pathologist review cases: {len(pathologist_cases)}\n")
    file.write(f"Total cases: {total_cases}\n")
    file.write(f"Urgent %: {urgent_pct:.1f}%\n")
    file.write(f"Pathologist review %: {review_pct:.1f}%\n")
    file.write(f"Abnoraml cases: {len(abnormal_cases)}\n")
    file.write(f"Scan failures: {len(scan_failures)}\n")
    file.write(f"Unsatisfactory cases: {len(unsat_cases)}\n")

print("\n=== SUMMARY ===")
print("Urgent cases:", len(urgent_cases))
print("Pathologist review cases:", len(pathologist_cases))

print(f"Total cases: {total_cases}")
print(f"Urgent %: {urgent_pct:.1f}%")
print(f"Pathologist review %: {review_pct:.1f}%")

print(f"Abnormal cases: {len(abnormal_cases)}")
print(f"Scan failures: {len(scan_failures)}")
print(f"Unsatisfactory cases: {len(unsat_cases)}")