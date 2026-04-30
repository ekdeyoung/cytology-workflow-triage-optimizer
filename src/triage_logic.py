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


df = pd.read_csv("data/raw/cytology_cases.csv")
df["priority"] = df.apply(lambda row: assign_priority(row["adequacy"], row["scan_status"], row["diagnosis"]), axis=1)
df = df.sort_values("priority")
df = df.reset_index(drop=True)
print(df)

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
        