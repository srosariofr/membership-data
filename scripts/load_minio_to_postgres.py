from io import BytesIO
import boto3
import pandas as pd
from sqlalchemy import create_engine, text, inspect


# ------------------------------------------------------------
# MinIO config
# ------------------------------------------------------------

MINIO_ENDPOINT = "http://localhost:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password123"
BUCKET_NAME = "membership-data"


# ------------------------------------------------------------
# PostgreSQL config
# ------------------------------------------------------------

POSTGRES_USER = "admin"
POSTGRES_PASSWORD = "password123"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
POSTGRES_DB = "membership_db"

POSTGRES_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:"
    f"{POSTGRES_PASSWORD}@{POSTGRES_HOST}:"
    f"{POSTGRES_PORT}/{POSTGRES_DB}"
)


# ------------------------------------------------------------
# Files to load
# ------------------------------------------------------------

TABLES = {
    "companies": {
        "object_key": "raw/companies.csv",
        "table_name": "companies",
    },
    "members": {
        "object_key": "raw/members.csv",
        "table_name": "members",
    },
    "membership_applications": {
        "object_key": "raw/membership_applications.csv",
        "table_name": "membership_applications",
    },
    "application_status_history": {
        "object_key": "raw/application_status_history.csv",
        "table_name": "application_status_history",
    },
    "member_status_history": {
        "object_key": "raw/member_status_history.csv",
        "table_name": "member_status_history",
    },
    "payments": {
        "object_key": "raw/payments.csv",
        "table_name": "payments",
    },
    "events": {
        "object_key": "raw/events.csv",
        "table_name": "events",
    },
    "event_attendance": {
        "object_key": "raw/event_attendance.csv",
        "table_name": "event_attendance",
    },
}


def get_minio_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
    )


def read_csv_from_minio(s3_client, object_key):
    response = s3_client.get_object(
        Bucket=BUCKET_NAME,
        Key=object_key,
    )

    csv_bytes = response["Body"].read()

    return pd.read_csv(BytesIO(csv_bytes))


def normalize_column_names(df):
    df = df.copy()

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    return df


def create_raw_schema(engine):
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))


def load_dataframe_to_postgres(df, engine, schema_name, table_name):
    inspector = inspect(engine)
    table_exists = inspector.has_table(table_name, schema=schema_name)

    full_table_name = f'"{schema_name}"."{table_name}"'

    with engine.begin() as conn:
        if table_exists:
            conn.execute(text(f"TRUNCATE TABLE {full_table_name};"))
            if_exists_mode = "append"
        else:
            if_exists_mode = "replace"

        df.to_sql(
            name=table_name,
            con=conn,
            schema=schema_name,
            if_exists=if_exists_mode,
            index=False,
            method="multi",
            chunksize=1000,
        )


def main():
    s3_client = get_minio_client()
    engine = create_engine(POSTGRES_URL)

    create_raw_schema(engine)

    for source_name, config in TABLES.items():
        object_key = config["object_key"]
        table_name = config["table_name"]

        print(f"Reading s3://{BUCKET_NAME}/{object_key}")

        df = read_csv_from_minio(
            s3_client=s3_client,
            object_key=object_key,
        )

        df = normalize_column_names(df)

        print(f"Loading raw.{table_name} with {len(df):,} rows")

        load_dataframe_to_postgres(
            df=df,
            engine=engine,
            schema_name="raw",
            table_name=table_name,
        )

        print(f"Loaded raw.{table_name}")

    print("All files loaded successfully.")


if __name__ == "__main__":
    main()