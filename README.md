# ArvanCloud Object Storage Scripts

Python scripts for interacting with [ArvanCloud Object Storage](https://www.arvancloud.ir/en/products/cloud-storage) (S3-compatible API).

## Requirements

- Python 3.8+
- An ArvanCloud account with Object Storage enabled

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root:
   ```env
   ARVAN_ENDPOINT=https://s3.ir-thr-at1.arvanstorage.ir
   ARVAN_ACCESS_KEY=your-access-key
   ARVAN_SECRET_KEY=your-secret-key
   ARVAN_BUCKET=your-bucket-name
   ```

3. Optionally tune multipart upload thresholds:
   ```env
   MULTIPART_THRESHOLD_MB=16   # files larger than this use multipart upload (default: 16)
   PART_SIZE_MB=8              # size of each part in multipart upload (default: 8)
   ```

## Scripts

### `create_bucket.py` — Create a bucket
```bash
python3 create_bucket.py <bucket_name>
```

### `list_objects.py` — List objects in a bucket
```bash
# List all objects
python3 list_objects.py

# Filter by prefix
python3 list_objects.py <prefix>
```

### `upload.py` — Upload a file
Automatically uses multipart upload for large files (configurable via `MULTIPART_THRESHOLD_MB`).
```bash
python3 upload.py <file_path> [object_key]
```

### `download.py` — Download an object
```bash
python3 download.py <object_key> [destination_path]
```

### `presign.py` — Generate a pre-signed URL
```bash
python3 presign.py <object_key> [expires_in_seconds]
```
Default expiry is 3600 seconds (1 hour).

## Makefile

A `Makefile` is provided for convenience. See available targets with:
```bash
make help
```
