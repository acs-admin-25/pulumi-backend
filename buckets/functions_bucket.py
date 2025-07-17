import pulumi
from pulumi_gcp import storage
from core.config import load_config

config = load_config()
project = config['pulumi_project']
region = config.get('pulumi_region', 'us-central1')

# Create a GCP bucket for function source archives
bucket = storage.Bucket(
    "acs-functions-bucket",
    location=region,
    project=project,
    force_destroy=True
)

bucket_name = bucket.name

__all__ = ["bucket", "bucket_name"]
