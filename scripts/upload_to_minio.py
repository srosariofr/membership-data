from pathlib import Path
import boto3

MINIO_ENDPOINT = "http://localhost:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password123"
BUCKET_NAME = "membership-data"

DATA_DIR = Path("data")

FILES = {
    "companies.csv": "raw/companies.csv",
    "members.csv": "raw/members.csv",
    "membership_applications.csv": "raw/membership_applications.csv",
    "application_status_history.csv": "raw/application_status_history.csv",
    "member_status_history.csv": "raw/member_status_history.csv",
    "payments.csv": "raw/payments.csv",
    "events.csv": "raw/events.csv",
    "event_attendance.csv": "raw/event_attendance.csv",
}


def main():
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
    )

    existing_buckets = [
        bucket["Name"]
        for bucket in s3.list_buckets().get("Buckets", [])
    ]

    if BUCKET_NAME not in existing_buckets:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print(f"Created bucket: {BUCKET_NAME}")

    for local_filename, object_key in FILES.items():
        local_path = DATA_DIR / local_filename

        if not local_path.exists():
            print(f"Skipping missing file: {local_path}")
            continue

        s3.upload_file(
            Filename=str(local_path),
            Bucket=BUCKET_NAME,
            Key=object_key,
        )

        print(f"Uploaded {local_path} → s3://{BUCKET_NAME}/{object_key}")


if __name__ == "__main__":
    main()