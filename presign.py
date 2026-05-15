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


def presign(key: str, expires_in: int = 3600) -> str:
    client = get_client()
    bucket = os.environ["ARVAN_BUCKET"]
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )
    return url


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 presign.py <object_key> [expires_in_seconds]")
        sys.exit(1)

    key_arg = sys.argv[1]
    expires_arg = int(sys.argv[2]) if len(sys.argv) > 2 else 3600

    print(presign(key_arg, expires_arg))
