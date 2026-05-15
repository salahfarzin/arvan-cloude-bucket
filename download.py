import hashlib
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

load_dotenv()

PART_SIZE = int(os.getenv("PART_SIZE_MB", 8)) * 1024 * 1024
MULTIPART_THRESHOLD = int(os.getenv("MULTIPART_THRESHOLD_MB", 16)) * 1024 * 1024
MAX_CONCURRENCY = int(os.getenv("DOWNLOAD_CONCURRENCY", 10))
MAX_RETRIES = int(os.getenv("DOWNLOAD_RETRIES", 3))


def get_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["ARVAN_ENDPOINT"],
        aws_access_key_id=os.environ["ARVAN_ACCESS_KEY"],
        aws_secret_access_key=os.environ["ARVAN_SECRET_KEY"],
        config=Config(max_pool_connections=MAX_CONCURRENCY),
    )


def _print_progress(transferred: int, total: int):
    pct = transferred / total * 100
    bar = int(pct / 2)
    print(
        f"\r  [{'#' * bar}{'-' * (50 - bar)}] {pct:.1f}%  "
        f"{transferred // (1024 * 1024)}MB/{total // (1024 * 1024)}MB",
        end="",
        flush=True,
    )


def _resolve_filename(head: dict, key: str) -> str:
    """Get filename from Content-Disposition header, falling back to the key basename."""
    content_disposition = head.get("ContentDisposition", "")
    if content_disposition:
        for part in content_disposition.split(";"):
            part = part.strip()
            if part.lower().startswith("filename="):
                return part[9:].strip('" ')
    return os.path.basename(key) or key


def _md5(file_path: str) -> str:
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify(dest_path: str, total_size: int, etag: str):
    actual_size = os.path.getsize(dest_path)
    if actual_size != total_size:
        raise ValueError(f"Size mismatch: expected {total_size}B, got {actual_size}B")

    # ETag without a dash is the MD5 of the full file (single-part object)
    etag_clean = etag.strip('"')
    if "-" not in etag_clean:
        actual_md5 = _md5(dest_path)
        if actual_md5 != etag_clean:
            raise ValueError(f"MD5 mismatch: expected {etag_clean}, got {actual_md5}")
        print(f"  checksum OK ({actual_md5})")
    else:
        print(f"  size OK ({actual_size} bytes) — multipart ETag, skipping MD5")


def _resolve_dest(dest_path: str, filename: str) -> str:
    """If dest_path is a directory (or None), append the server filename."""
    if dest_path is None or os.path.isdir(dest_path):
        base = dest_path or "."
        return os.path.join(base, filename)
    return dest_path


def download(key: str, dest_path: str = None):
    client = get_client()
    bucket = os.environ["ARVAN_BUCKET"]

    head = client.head_object(Bucket=bucket, Key=key)
    total_size = head["ContentLength"]
    etag = head.get("ETag", "")

    filename = _resolve_filename(head, key)
    dest_path = _resolve_dest(dest_path, filename)

    size_mb = total_size // (1024 * 1024)
    print(
        f"Downloading s3://{bucket}/{key} → '{dest_path}'"
        f" ({size_mb} MB, concurrency={MAX_CONCURRENCY})"
    )

    # Small files: single-threaded download
    if total_size <= MULTIPART_THRESHOLD:
        transferred = [0]

        def _callback(n: int):
            transferred[0] += n
            _print_progress(transferred[0], total_size)

        client.download_file(bucket, key, dest_path, Callback=_callback)
        print("\nVerifying...")
        _verify(dest_path, total_size, etag)
        print(f"Done → {dest_path}")
        return

    # Large files: parallel ranged parts with resume support
    parts = []
    offset = 0
    part_num = 0
    while offset < total_size:
        end = min(offset + PART_SIZE - 1, total_size - 1)
        parts.append((part_num, offset, end))
        offset = end + 1
        part_num += 1

    transferred = [0]
    lock = threading.Lock()

    def _download_part(pnum: int, start: int, end: int):
        part_file = f"{dest_path}.part{pnum}"
        expected = end - start + 1

        # Resume: skip already-completed parts
        if os.path.exists(part_file) and os.path.getsize(part_file) == expected:
            with lock:
                transferred[0] += expected
                _print_progress(transferred[0], total_size)
            return

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = client.get_object(Bucket=bucket, Key=key, Range=f"bytes={start}-{end}")
                written = 0
                with open(part_file, "wb") as f:
                    for chunk in resp["Body"].iter_chunks(chunk_size=1024 * 1024):
                        f.write(chunk)
                        written += len(chunk)
                        with lock:
                            transferred[0] += len(chunk)
                            _print_progress(transferred[0], total_size)

                if written != expected:
                    raise ValueError(f"Part {pnum}: wrote {written}B, expected {expected}B")
                return

            except (BotoCoreError, ClientError, ValueError) as exc:
                # Remove incomplete part file so it won't be mistaken as complete on resume
                if os.path.exists(part_file):
                    os.remove(part_file)
                # Undo progress counter for the failed attempt
                with lock:
                    transferred[0] -= written if "written" in dir() else 0

                if attempt == MAX_RETRIES:
                    msg = f"Part {pnum} failed after {MAX_RETRIES} retries: {exc}"
                    raise RuntimeError(msg) from exc

                wait = 2**attempt
                print(f"\n  Part {pnum} attempt {attempt} failed ({exc}), retrying in {wait}s...")
                time.sleep(wait)

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as executor:
        futures = {executor.submit(_download_part, *part): part for part in parts}
        for future in as_completed(futures):
            future.result()

    print("\nMerging parts...")
    with open(dest_path, "wb") as out:
        for pnum, _, _ in parts:
            part_file = f"{dest_path}.part{pnum}"
            with open(part_file, "rb") as pf:
                out.write(pf.read())
            os.remove(part_file)

    print("Verifying...")
    _verify(dest_path, total_size, etag)
    print(f"Done → {dest_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 download.py <object_key> [destination_path]")
        sys.exit(1)

    key_arg = sys.argv[1]
    dest_arg = sys.argv[2] if len(sys.argv) > 2 else None

    download(key_arg, dest_arg)
