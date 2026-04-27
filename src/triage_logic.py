def assign_priority(case_type):
    priority_map = {
        "unsatisfactory_cellularity": 1,
        "scan_failure": 2,
        "HSIL": 3,
        "LSIL": 4,
        "ASCUS": 5,
        "infection": 6,
        "normal": 7
    }
    return priority_map.get(case_type, 99)

cases = [
    "normal",
    "HSIL",
    "scan_failure",
    "infection",
    "unsatisfactory_cellularity"
]

for case in cases:
    print(case, "-> Priority", assign_priority(case))