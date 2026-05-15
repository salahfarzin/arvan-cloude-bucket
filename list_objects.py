import os
import sys
import boto3
from dotenv import load_dotenv

load_dotenv()


def get_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["ARVAN_ENDPOINT"],
        aws_access_key_id=os.environ["ARVAN_ACCESS_KEY"],
        aws_secret_access_key=os.environ["ARVAN_SECRET_KEY"],
    )


def list_objects(prefix: str = ""):
    client = get_client()
    bucket = os.environ["ARVAN_BUCKET"]

    paginator = client.get_paginator("list_objects_v2")
    kwargs = {"Bucket": bucket}
    if prefix:
        kwargs["Prefix"] = prefix

    total_objects = 0
    total_size = 0

    print(f"{'Key':<60} {'Size':>12}  {'Last Modified'}")
    print("-" * 90)

    for page in paginator.paginate(**kwargs):
        for obj in page.get("Contents", []):
            size_kb = obj["Size"] / 1024
            modified = obj["LastModified"].strftime("%Y-%m-%d %H:%M:%S")
            print(f"{obj['Key']:<60} {size_kb:>10.1f}KB  {modified}")
            total_objects += 1
            total_size += obj["Size"]

    print("-" * 90)
    print(f"{total_objects} object(s), {total_size / (1024 * 1024):.2f} MB total")


if __name__ == "__main__":
    prefix_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    list_objects(prefix_arg)
