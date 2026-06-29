import pandas as pd

from database import get_cases_dataframe

def load_cases():
    """
    Load cytology cases from the database.
    """
    return get_cases_dataframe()