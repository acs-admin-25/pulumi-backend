from pulumi_gcp import storage
from core.config import load_config

config = load_config()
project = config['pulumi_project']
region = config.get('pulumi_region', 'us-central1')

functions_bucket = storage.Bucket(
    "acs-functions-bucket",
    location=region,
    project=project,
    force_destroy=True
)


def deploy():

    return {
        "functions_bucket": functions_bucket,
    }
