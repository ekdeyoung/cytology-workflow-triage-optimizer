import sqlite3
from pathlib import Path
import pandas as pd

DATABASE_PATH = Path("data/cytology_workflow.db")


def get_database_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    return connection

def initialize_database():
    connection = get_database_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            case_id TEXT PRIMARY KEY,
            adequacy TEXT,
            scan_status TEXT,
            diagnosis TEXT,
            priority INTEGER,
            needs_attention TEXT
        )
""")
    
    connection.commit()
    connection.close()

def insert_case(
    case_id,
    adequacy,
    scan_status,
    diagnosis,
    priority,
    needs_attention
):
    connection = get_database_connection()

    connection.execute(
        """
        INSERT OR REPLACE INTO cases (
            case_id,
            adequacy,
            scan_status,
            diagnosis,
            priority,
            needs_attention
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            case_id,
            adequacy,
            scan_status,
            diagnosis,
            priority,
            needs_attention
        )
    )

    connection.commit()
    connection.close()

def get_all_cases():
    connection = get_database_connection()

    cursor = connection.execute(
        """
        SELECT *
        FROM cases
        """
    )

    cases = cursor.fetchall()

    connection.close()

    return cases

def get_cases_dataframe():
    connection = get_database_connection()

    cases_df = pd.read_sql_query(
        """
        SELECT *
        FROM cases
        """,
        connection
    )

    connection.close()

    return cases_df

if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")