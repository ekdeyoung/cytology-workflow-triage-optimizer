import sqlite3
from pathlib import Path
import pandas as pd

DATABASE_PATH = Path("data/cytology_workflow.db")


def get_database_connection():
    """Create a configured SQLite database connection."""
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection

def add_missing_case_columns(connection):
    """Add workflow columns to an existing cases table without deleting data."""

    existing_columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(cases)"
        ).fetchall()
    }

    workflow_columns = {
        "specimen_category": "TEXT DEFAULT 'gynecologic'",
        "workflow_type": "TEXT DEFAULT 'routine'",
        "current_stage": "TEXT DEFAULT 'digital_imaging'",
        "screening_result": "TEXT",
        "selected_for_quality_control": "INTEGER DEFAULT 0",
        "discrepancy_review_status": "TEXT DEFAULT 'no_discrepancy'",
    }

    for column_name, column_definition in workflow_columns.items():
        if column_name not in existing_columns:
            connection.execute(
                f"""
                ALTER TABLE cases
                ADD COLUMN {column_name} {column_definition}
                """
            )

def ensure_case_columns(connection):
    """Add missing legacy case columns without deleting existing data."""

    existing_columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(cases)"
        ).fetchall()
    }

    required_columns = {
        "priority": "INTEGER",
        "needs_attention": "TEXT",
    }

    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            connection.execute(
                f"""
                ALTER TABLE cases
                ADD COLUMN {column_name} {column_type}
                """
            )

def initialize_database():
    """Create the core case and workflow-support tables."""

    connection = get_database_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS cases (
            case_id TEXT PRIMARY KEY,
            adequacy TEXT,
            scan_status TEXT,
            diagnosis TEXT,
            received_date TEXT,
            reported_date TEXT,
            blur_score REAL,
            artifact_risk_score REAL,
            priority INTEGER,
            needs_attention TEXT
        )
        """
    )

    ensure_case_columns(connection)

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS staff (
            staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_name TEXT NOT NULL,
            staff_role TEXT NOT NULL,
            availability_status TEXT NOT NULL DEFAULT 'available',
            active INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS case_workflow (
            case_id TEXT PRIMARY KEY,
            specimen_category TEXT,
            workflow_type TEXT,
            current_stage TEXT,
            processing_status TEXT,
            current_owner_id INTEGER,
            primary_cytologist_id INTEGER,
            rose_cytologist_id INTEGER,
            qc_reviewer_id INTEGER,
            pathologist_id INTEGER,
            updated_at TEXT,
            FOREIGN KEY (case_id)
                REFERENCES cases(case_id)
                ON DELETE CASCADE,
            FOREIGN KEY (current_owner_id)
                REFERENCES staff(staff_id),
            FOREIGN KEY (primary_cytologist_id)
                REFERENCES staff(staff_id),
            FOREIGN KEY (rose_cytologist_id)
                REFERENCES staff(staff_id),
            FOREIGN KEY (qc_reviewer_id)
                REFERENCES staff(staff_id),
            FOREIGN KEY (pathologist_id)
                REFERENCES staff(staff_id)
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS workflow_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            workflow_stage TEXT,
            actor_staff_id INTEGER,
            event_timestamp TEXT NOT NULL,
            event_details TEXT,
            FOREIGN KEY (case_id)
                REFERENCES cases(case_id)
                ON DELETE CASCADE,
            FOREIGN KEY (actor_staff_id)
                REFERENCES staff(staff_id)
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS rose_assessments (
            case_id TEXT PRIMARY KEY,
            rose_adequacy_call TEXT,
            final_adequacy TEXT,
            concordance_status TEXT,
            discrepancy_type TEXT,
            procedure_site TEXT,
            procedure_datetime TEXT,
            FOREIGN KEY (case_id)
                REFERENCES cases(case_id)
                ON DELETE CASCADE
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS diagnostic_reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL,
            review_type TEXT NOT NULL,
            reviewer_staff_id INTEGER,
            diagnosis TEXT,
            adequacy TEXT,
            areas_of_interest_marked INTEGER,
            review_notes TEXT,
            completed_at TEXT,
            FOREIGN KEY (case_id)
                REFERENCES cases(case_id)
                ON DELETE CASCADE,
            FOREIGN KEY (reviewer_staff_id)
                REFERENCES staff(staff_id)
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS educational_reviews (
            educational_review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL,
            review_reason TEXT,
            educational_priority TEXT,
            pathologist_feedback TEXT,
            learning_takeaway TEXT,
            follow_up_action TEXT,
            review_status TEXT NOT NULL DEFAULT 'pending',
            reviewed_with_staff_id INTEGER,
            reviewed_at TEXT,
            FOREIGN KEY (case_id)
                REFERENCES cases(case_id)
                ON DELETE CASCADE,
            FOREIGN KEY (reviewed_with_staff_id)
                REFERENCES staff(staff_id)
        )
        """
    )

    add_missing_case_columns(connection)

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
    """Return all case records as SQLite rows."""

    connection = get_database_connection()

    try:
        cursor = connection.execute(
            """
            SELECT *
            FROM cases
            """
        )

        return cursor.fetchall()

    finally:
        connection.close()

def get_cases_dataframe():
    """Return all current cases as a Pandas DataFrame."""

    connection = get_database_connection()

    try:
        return pd.read_sql_query(
            """
            SELECT *
            FROM cases
            """,
            connection,
        )

    finally:
        connection.close()

def import_cases_from_dataframe(cases_df):
    """Replace case records without replacing the database schema."""

    connection = get_database_connection()

    try:
        connection.execute(
            "DELETE FROM cases"
        )

        cases_df.to_sql(
            "cases",
            connection,
            if_exists="append",
            index=False,
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")