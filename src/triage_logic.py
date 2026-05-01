from datetime import datetime

import pandas as pd
import csv


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

def assign_attention_flag(priority): 
    if priority in [1, 2]:
        return "immediate_attention" 
    elif priority in [3, 4, 5]:
        return "pathologist_review"
    else:
        return "routine"
    
def create_triage_queue(file_path):
    df = pd.read_csv(file_path)
    df["priority"] = df.apply(lambda row: assign_priority(row["adequacy"], row["scan_status"], row["diagnosis"]), axis=1)
    df["needs_attention"] = df["priority"].apply(assign_attention_flag)
    df = df.sort_values("priority")
    df = df.reset_index(drop=True)
    return df

triage_queue = create_triage_queue("data/raw/cytology_cases.csv")
print(triage_queue)

today = datetime.today().strftime("%Y-%m-%d")

triage_queue.to_csv(f"results/triage_report_{today}.csv", index=False)

# ranked_cases = []

# with open("data/raw/cytology_cases.csv") as file:
    # reader = csv.DictReader(file)

    # for row in reader:
        # adequacy = row["adequacy"]
        # scan_status = row["scan_status"]
        # diagnosis = row["diagnosis"]

        # priority = assign_priority(adequacy, scan_status, diagnosis)

        # row["priority"] = priority
        # ranked_cases.append(row)

# ranked_cases = sorted(ranked_cases, key=lambda x: x["priority"])

# for case in ranked_cases:
    # print(case)
        