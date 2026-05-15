import os
import sys
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()


def get_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["ARVAN_ENDPOINT"],
        aws_access_key_id=os.environ["ARVAN_ACCESS_KEY"],
        aws_secret_access_key=os.environ["ARVAN_SECRET_KEY"],
    )


def create_bucket(bucket_name: str):
    client = get_client()
    try:
        client.create_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' created successfully.")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "BucketAlreadyExists":
            print(f"Error: bucket '{bucket_name}' is already taken. Choose a different name.")
            sys.exit(1)
        elif code == "BucketAlreadyOwnedByYou":
            print(f"Bucket '{bucket_name}' already exists and is owned by you.")
        else:
            raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 create_bucket.py <bucket_name>")
        sys.exit(1)

    create_bucket(sys.argv[1])
