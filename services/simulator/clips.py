"""Generates short synthetic dashcam clips with ffmpeg (color bars + a text
label per event type) and uploads them once to MinIO. No real video, no real
faces -- see CLAUDE.md rule 3."""

import os
import pathlib
import subprocess
import tempfile

import boto3

EVENT_TYPES = ["harsh_braking", "lane_departure", "drowsiness", "face_mismatch"]
BUCKET = os.environ.get("S3_BUCKET", "haulwise-media")


def _s3():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["S3_ENDPOINT"],
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"],
    )


def ensure_clips():
    client = _s3()
    with tempfile.TemporaryDirectory() as tmp:
        for etype in EVENT_TYPES:
            key = f"clips/{etype}.mp4"
            out_path = pathlib.Path(tmp) / f"{etype}.mp4"
            label = etype.replace("_", " ").upper()
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc=size=480x270:rate=15:duration=3",
                    "-vf",
                    f"drawtext=text='{label} (SYNTHETIC)':fontcolor=white:fontsize=20:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.6",
                    "-t",
                    "3",
                    str(out_path),
                ],
                check=True,
                capture_output=True,
            )
            client.upload_file(str(out_path), BUCKET, key, ExtraArgs={"ContentType": "video/mp4"})
            print(f"clips: uploaded {key}")
