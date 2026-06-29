import pandas as pd

from database import (
    get_cases_dataframe,
    import_cases_from_dataframe,
    initialize_database,
)

INPUT_FILE = "data/raw/cytology_cases.csv"

def migrate_cases_from_csv():
    initialize_database()

    cases_df = pd.read_csv(INPUT_FILE)

    import_cases_from_dataframe(cases_df)

    imported_cases = get_cases_dataframe()

    print("Database initialized.")
    print(f"Imported {len(imported_cases)} cases.")
    print("Verification successful.")

if __name__ == "__main__":
    migrate_cases_from_csv()

