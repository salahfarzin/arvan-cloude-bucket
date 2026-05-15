import os
import sys
import math
from typing import Optional
import boto3
from dotenv import load_dotenv

load_dotenv()

MULTIPART_THRESHOLD = int(os.getenv("MULTIPART_THRESHOLD_MB", 16)) * 1024 * 1024
PART_SIZE = int(os.getenv("PART_SIZE_MB", 8)) * 1024 * 1024


def get_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["ARVAN_ENDPOINT"],
        aws_access_key_id=os.environ["ARVAN_ACCESS_KEY"],
        aws_secret_access_key=os.environ["ARVAN_SECRET_KEY"],
    )


def _print_progress(transferred: int, total: int):
    pct = transferred / total * 100
    bar = int(pct / 2)
    print(f"\r  [{'#' * bar}{'-' * (50 - bar)}] {pct:.1f}%  {transferred // (1024*1024)}MB/{total // (1024*1024)}MB", end="", flush=True)


def upload_simple(client, file_path: str, bucket: str, key: str):
    file_size = os.path.getsize(file_path)
    print(f"Uploading '{file_path}' → s3://{bucket}/{key}")
    client.upload_file(
        file_path, bucket, key,
        Callback=lambda b: _print_progress(getattr(upload_simple, '_sent', 0) + b, file_size)
    )
    print("\nUpload complete.")


def upload_multipart(client, file_path: str, bucket: str, key: str):
    file_size = os.path.getsize(file_path)
    total_parts = math.ceil(file_size / PART_SIZE)
    print(f"Uploading '{file_path}' → s3://{bucket}/{key} ({file_size // (1024*1024)} MB, {total_parts} parts)")

    mpu = client.create_multipart_upload(Bucket=bucket, Key=key)
    upload_id = mpu["UploadId"]
    parts = []
    sent = 0

    try:
        with open(file_path, "rb") as f:
            for part_number in range(1, total_parts + 1):
                chunk = f.read(PART_SIZE)
                if not chunk:
                    break
                resp = client.upload_part(
                    Bucket=bucket,
                    Key=key,
                    UploadId=upload_id,
                    PartNumber=part_number,
                    Body=chunk,
                )
                parts.append({"ETag": resp["ETag"], "PartNumber": part_number})
                sent += len(chunk)
                _print_progress(sent, file_size)

        print()  # newline after progress bar
        client.complete_multipart_upload(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )
        print("Multipart upload complete.")

    except Exception as exc:
        print(f"Error during upload: {exc}")
        client.abort_multipart_upload(Bucket=bucket, Key=key, UploadId=upload_id)
        print("Multipart upload aborted.")
        raise


def upload(file_path: str, bucket: str, key: Optional[str] = None):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if key is None:
        key = os.path.basename(file_path)

    client = get_client()
    file_size = os.path.getsize(file_path)

    if file_size > MULTIPART_THRESHOLD:
        upload_multipart(client, file_path, bucket, key)
    else:
        upload_simple(client, file_path, bucket, key)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload.py <file_path> [object_key]")
        sys.exit(1)

    file_arg = sys.argv[1]
    key_arg = sys.argv[2] if len(sys.argv) > 2 else None
    bucket_name = os.environ.get("ARVAN_BUCKET", "")

    if not bucket_name:
        print("Error: ARVAN_BUCKET is not set in .env")
        sys.exit(1)

    upload(file_arg, bucket_name, key_arg)
