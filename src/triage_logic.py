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

    return diagnosis_map.get(diagnosis, 99)

slides = [
    ("sat", "pass", "normal"),
    ("sat", "pass", "hsil"),
    ("sat", "fail", "normal"),
    ("unsat", "pass", "normal"),
    ("sat", "pass", "infection")
]
    
for slide in slides:
    adequacy, scan_status, diagnosis = slide
    print(slide, "-> Priority", assign_priority(adequacy, scan_status, diagnosis))