import pandas as pd

def load_cases():
    """
    Load cytology cases from the current data source.

    For now this reads from the CSV file.
    Later it will load from SQLite without requiring
    changes elsewhere in the application.
    """
    return pd.read_csv("data/raw/cytology_cases.csv")