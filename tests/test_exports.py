import csv
import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def test_csv_and_parquet_exports_roundtrip():
    """
    Write a small dataset to CSV and Parquet inside data/_tmp to ensure the
    project can create export artifacts without touching network resources.
    """

    repo_root = Path(__file__).resolve().parents[1]
    base_dir = repo_root / "data" / "_tmp" / "test_exports"
    base_dir.mkdir(parents=True, exist_ok=True)

    rows = [
        {"team": "Chiefs", "edge": 3.5, "market": "spread"},
        {"team": "Bills", "edge": -1.0, "market": "total"},
    ]
    fieldnames = list(rows[0].keys())

    csv_path = base_dir / "sample.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    csv_contents = csv_path.read_text(encoding="utf-8")
    assert "Chiefs" in csv_contents
    assert csv_contents.count("\n") >= len(rows)

    table = pa.Table.from_pylist(rows)
    parquet_path = base_dir / "sample.parquet"
    pq.write_table(table, parquet_path)

    loaded = pq.read_table(parquet_path).to_pylist()
    assert loaded == rows

    shutil.rmtree(base_dir)
