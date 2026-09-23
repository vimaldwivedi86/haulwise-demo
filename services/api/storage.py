import os

import boto3

_client = None


def s3():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=os.environ["S3_ENDPOINT"],
            aws_access_key_id=os.environ["S3_ACCESS_KEY"],
            aws_secret_access_key=os.environ["S3_SECRET_KEY"],
        )
    return _client


BUCKET = os.environ.get("S3_BUCKET", "haulwise-media")


def put_bytes(key: str, data: bytes, content_type: str = "application/octet-stream"):
    s3().put_object(Bucket=BUCKET, Key=key, Body=data, ContentType=content_type)
    return key


def delete_key(key: str) -> bool:
    if not key:
        return False
    s3().delete_object(Bucket=BUCKET, Key=key)
    return True


def object_url(key: str) -> str:
    endpoint = os.environ["S3_ENDPOINT"].replace("minio", "localhost")
    return f"{endpoint}/{BUCKET}/{key}"
