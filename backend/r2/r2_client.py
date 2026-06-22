from pathlib import Path

from imports.source_truth.r2.harvest_pdfs import (
    create_r2_client,
    load_r2_config,
    r2_bucket_name,
)


def upload_file_to_r2(local_path: Path, r2_key: str) -> dict:
    config = load_r2_config()
    client = create_r2_client(config)
    bucket = r2_bucket_name(config)

    client.upload_file(str(local_path), bucket, r2_key)

    return {
        "ok": True,
        "bucket": bucket,
        "key": r2_key,
        "size": local_path.stat().st_size,
    }
