from pulumi_gcp import storage
from core.config import load_config
import pulumi

config = load_config()
project = config['pulumi_project']
region = config.get('pulumi_region', 'us-central1')

functions_bucket = storage.Bucket(
    "acs-functions-bucket",
    location=region,
    project=project,
    force_destroy=True,
    opts=pulumi.ResourceOptions(delete_before_replace=True)
)

def deploy():
    return {
        "functions_bucket": functions_bucket,
    }
