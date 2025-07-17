import pulumi
from pulumi_gcp import storage
from core.config import load_config

config = load_config()
project = config['pulumi_project']
region = config.get('pulumi_region', 'us-central1')

# Create a GCP bucket for function source archives
functions_bucket = storage.Bucket(
    "acs-functions-bucket",
    location=region,
    project=project,
    force_destroy=True
)

functions_bucket_name = functions_bucket.name

__all__ = ["functions_bucket", "functions_bucket_name"]
