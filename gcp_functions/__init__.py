import pulumi
from pulumi_gcp import cloudfunctions
from pulumi_gcp.storage import BucketObject
from pulumi import FileArchive
import os
from core.config import load_config

config = load_config()
project = config['pulumi_project']
region = config['pulumi_region']
bucket = config['functions_bucket']

if bucket is None:
    raise ValueError("Functions bucket not found in config. Make sure gcp_buckets module is properly imported.")

# Create Cloud Functions from source directories
def create_function(name, entry_point, source_dir=None):
    if source_dir is None:
        source_dir = os.path.join(os.path.dirname(__file__), name)
    zip_asset = FileArchive(source_dir)
    
    # Create the zip object in the bucket
    zip_object = BucketObject(
        f"{name}-zip",
        bucket=bucket.name,
        source=zip_asset,
        name=f"{name}.zip"
    )
    
    # Create the Cloud Function
    function = cloudfunctions.Function(
        name,
        name=name,
        runtime="python310",
        entry_point=entry_point,
        source_archive_bucket=bucket.name,
        source_archive_object=zip_object.name,
        trigger_http=True,
        available_memory_mb=128,
        region=region,
        project=project,
        environment_variables={"ENV": config.get('ENV', 'production')},
        opts=pulumi.ResourceOptions(depends_on=[zip_object])
    )
    
    return function

login_function = create_function("login", "login", source_dir=os.path.join(os.path.dirname(__file__), "login"))
signup_function = create_function("signup", "signup", source_dir=os.path.join(os.path.dirname(__file__), "signup"))
healthcheck_function = create_function("healthcheck", "healthcheck", source_dir=os.path.join(os.path.dirname(__file__), "healthcheck"))

__all__ = ["login_function", "signup_function", "healthcheck_function", "bucket"]
