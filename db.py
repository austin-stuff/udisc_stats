from __future__ import annotations

import hashlib
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd

# Constants for storage locations
DB_PATH = Path("data/app.db")
UPLOADS_DIR = Path("data/uploads")


def _ensure_storage_locations_exist() -> None:
    """Create the database directory and uploads directory if missing."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def _connect() -> Iterable[sqlite3.Connection]:
    """Context manager to open a SQLite connection with sensible defaults."""
    _ensure_storage_locations_exist()
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute("PRAGMA journal_mode=WAL;")
        connection.row_factory = sqlite3.Row
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    """Create required tables if they do not exist."""
    _ensure_storage_locations_exist()
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_hash TEXT NOT NULL UNIQUE,
                uploaded_at TEXT NOT NULL,
                num_rows INTEGER NOT NULL,
                num_cols INTEGER NOT NULL
            );
            """
        )


def _compute_sha256(file_bytes: bytes) -> str:
    """Return the SHA-256 hash (hex) of the provided bytes."""
    sha256 = hashlib.sha256()
    sha256.update(file_bytes)
    return sha256.hexdigest()


@dataclass
class UploadRecord:
    id: int
    filename: str
    file_hash: str
    uploaded_at: str
    num_rows: int
    num_cols: int

    @property
    def parquet_path(self) -> Path:
        return UPLOADS_DIR / f"{self.id}.parquet"

    @property
    def csv_path(self) -> Path:
        return UPLOADS_DIR / f"{self.id}.csv"


def _row_to_upload_record(row: sqlite3.Row) -> UploadRecord:
    return UploadRecord(
        id=row["id"],
        filename=row["filename"],
        file_hash=row["file_hash"],
        uploaded_at=row["uploaded_at"],
        num_rows=row["num_rows"],
        num_cols=row["num_cols"],
    )


def list_uploads() -> List[UploadRecord]:
    """Return all saved uploads, most recent first."""
    initialize_database()
    with _connect() as connection:
        rows = connection.execute(
            "SELECT * FROM uploads ORDER BY datetime(uploaded_at) DESC"
        ).fetchall()
    return [_row_to_upload_record(row) for row in rows]


def get_upload(upload_id: int) -> Optional[UploadRecord]:
    initialize_database()
    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM uploads WHERE id = ?",
            (upload_id,),
        ).fetchone()
    return _row_to_upload_record(row) if row else None


def save_upload(filename: str, file_bytes: bytes, cleaned_df: pd.DataFrame) -> UploadRecord:
    """Persist an uploaded file and its cleaned DataFrame.

    - Deduplicates by SHA-256 of the original bytes.
    - Saves cleaned DataFrame to Parquet under `data/uploads/<id>.parquet`.
    - Also writes the original CSV bytes to `data/uploads/<id>.csv` for reference.
    - Returns the corresponding UploadRecord.
    """
    if not isinstance(cleaned_df, pd.DataFrame):
        raise TypeError("cleaned_df must be a pandas DataFrame")

    initialize_database()

    file_hash = _compute_sha256(file_bytes)
    uploaded_at = datetime.now(timezone.utc).isoformat()

    # Try to find an existing record by hash (dedupe)
    with _connect() as connection:
        existing = connection.execute(
            "SELECT * FROM uploads WHERE file_hash = ?",
            (file_hash,),
        ).fetchone()
        if existing is None:
            cursor = connection.execute(
                """
                INSERT INTO uploads (filename, file_hash, uploaded_at, num_rows, num_cols)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    filename,
                    file_hash,
                    uploaded_at,
                    int(cleaned_df.shape[0]),
                    int(cleaned_df.shape[1]),
                ),
            )
            upload_id = int(cursor.lastrowid)
            record = UploadRecord(
                id=upload_id,
                filename=filename,
                file_hash=file_hash,
                uploaded_at=uploaded_at,
                num_rows=int(cleaned_df.shape[0]),
                num_cols=int(cleaned_df.shape[1]),
            )
        else:
            record = _row_to_upload_record(existing)

    # Ensure files exist on disk (idempotent writes)
    record.parquet_path.parent.mkdir(parents=True, exist_ok=True)
    if not record.parquet_path.exists():
        cleaned_df.to_parquet(record.parquet_path)
    if not record.csv_path.exists():
        with open(record.csv_path, "wb") as csv_file:
            csv_file.write(file_bytes)

    return record


def load_upload_df(upload_id: int) -> pd.DataFrame:
    """Load a previously saved cleaned DataFrame by upload id."""
    record = get_upload(upload_id)
    if record is None:
        raise ValueError(f"No upload found with id {upload_id}")
    if not record.parquet_path.exists():
        raise FileNotFoundError(
            f"Stored parquet not found at {record.parquet_path}. The upload may be corrupted."
        )
    return pd.read_parquet(record.parquet_path)
