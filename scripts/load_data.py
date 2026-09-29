"""Loads posts.csv into the database and indexes each document in Elasticsearch.

Usage:
    python -m scripts.load_data [path/to/posts.csv] [--batch-size N]
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import csv
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.database import Base, async_session_maker, engine  # noqa: E402
from app.models import Document  # noqa: E402
from app.search_backend import ElasticsearchBackend  # noqa: E402

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_row(row: dict[str, str]) -> dict:
    raw_rubrics = row.get("rubrics") or ""
    rubrics = ast.literal_eval(raw_rubrics) if raw_rubrics.strip() else []
    return {
        "text": row["text"],
        "created_date": datetime.strptime(row["created_date"], DATE_FORMAT),
        "rubrics": rubrics,
    }


async def _flush(batch: list[dict], backend: ElasticsearchBackend) -> int:
    async with async_session_maker() as session:
        documents = [Document(**item) for item in batch]
        session.add_all(documents)
        await session.flush()
        await backend.index_documents(
            {"id": document.id, "text": document.text} for document in documents
        )
        await session.commit()
        return len(documents)


async def load(csv_path: str, batch_size: int) -> int:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    backend = ElasticsearchBackend(settings.elastic_url, settings.elastic_index)
    await backend.ensure_index()

    total = 0
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            batch: list[dict] = []
            for row in reader:
                batch.append(parse_row(row))
                if len(batch) >= batch_size:
                    total += await _flush(batch, backend)
                    batch = []
            if batch:
                total += await _flush(batch, backend)
    finally:
        await backend.close()

    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Load posts.csv into the database and Elasticsearch index")
    parser.add_argument("csv_path", nargs="?", default="posts.csv")
    parser.add_argument("--batch-size", type=int, default=200)
    args = parser.parse_args()

    total = asyncio.run(load(args.csv_path, args.batch_size))
    print(f"Loaded {total} documents")


if __name__ == "__main__":
    main()
