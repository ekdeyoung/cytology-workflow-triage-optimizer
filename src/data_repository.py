import pandas as pd

from database import get_cases_dataframe

def load_cases():
    """
    Load cytology cases from the database.
    """
    return get_cases_dataframe()

def load_case(case_id):
    """
    Load a single case by its case ID.
    """
    cases = load_cases()

    return cases[
        cases["case_id"] == case_id
    ]

def load_high_priority_cases():
    """
    Load cases with priority 5 or higher.
    """
    cases = load_cases()

    return cases[
        cases["priority"] <= 5
    ]