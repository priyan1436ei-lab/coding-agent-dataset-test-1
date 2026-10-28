"""Stream reader for processing large datasets incrementally without exhausting RAM."""
import json
import logging
import os
from typing import Iterator, Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("stream_reader")

def stream_jsonl(filepath: str, max_records: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """Yield records from a JSONL file line-by-line."""
    count = 0
    malformed = 0
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                record["_source_line"] = line_no
                yield record
                count += 1
                if max_records and count >= max_records:
                    break
            except json.JSONDecodeError as e:
                malformed += 1
                logger.warning(f"Malformed JSON at {filepath}:{line_no} -> {e}")
                continue
    if malformed > 0:
        logger.warning(f"Encountered {malformed} malformed lines in {filepath}")

def stream_json_array(filepath: str, max_records: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """Stream records from a JSON file containing a list of records.
    Uses chunked buffer approach to avoid loading huge lists all at once if large,
    or falls back safely.
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                for idx, item in enumerate(data):
                    if isinstance(item, dict):
                        item["_source_index"] = idx
                        yield item
                        if max_records and (idx + 1) >= max_records:
                            break
            elif isinstance(data, dict):
                yield data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON file {filepath}: {e}")

def stream_records(filepath: str, max_records: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """Autodetect format (JSONL, JSON, Parquet) and stream records safely."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Source file does not exist: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == ".jsonl":
        yield from stream_jsonl(filepath, max_records=max_records)
    elif ext == ".json":
        yield from stream_json_array(filepath, max_records=max_records)
    elif ext == ".parquet":
        # Stream parquet row groups if pyarrow / polars available
        try:
            import pyarrow.parquet as pq
            parquet_file = pq.ParquetFile(filepath)
            count = 0
            for i in range(parquet_file.num_row_groups):
                table = parquet_file.read_row_group(i)
                dicts = table.to_pylist()
                for d in dicts:
                    yield d
                    count += 1
                    if max_records and count >= max_records:
                        return
        except ImportError:
            # Fallback to polars
            try:
                import polars as pl
                df = pl.read_parquet(filepath)
                count = 0
                for row in df.iter_rows(named=True):
                    yield row
                    count += 1
                    if max_records and count >= max_records:
                        break
            except Exception as e:
                logger.error(f"Parquet streaming requires pyarrow or polars: {e}")
                raise
    else:
        # Default try JSONL
        yield from stream_jsonl(filepath, max_records=max_records)

def stream_chunks(filepath: str, chunk_size: int = 500, max_records: Optional[int] = None) -> Iterator[List[Dict[str, Any]]]:
    """Yield records grouped into fixed-size chunks to optimize batch throughput."""
    chunk = []
    total = 0
    for record in stream_records(filepath, max_records=max_records):
        chunk.append(record)
        total += 1
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
