import pulumi
from pulumi_gcp import cloudfunctions
from pulumi_gcp.storage import Bucket, BucketObject
from pulumi import FileArchive
import os
from core.config import load_config

config = load_config()
project = config['pulumi_project']
region = config['pulumi_region']

# Use bucket from config if available, else create
if config.get('functions_bucket'):
    bucket = Bucket(config['functions_bucket'], location="US")
else:
    bucket = Bucket('my-bucket', location="US")

# Create Cloud Functions from source directories
def create_function(name, entry_point, source_dir=None):
    if source_dir is None:
        source_dir = os.path.join(os.path.dirname(__file__), name)
    zip_asset = FileArchive(source_dir)
    # Ensure bucket.name is resolved before creating BucketObject
    def create_zip_object(resolved_bucket_name):
        return BucketObject(
            f"{name}-zip",
            bucket=resolved_bucket_name,
            source=zip_asset,
            name=f"{name}.zip"
        )
    zip_object = bucket.name.apply(create_zip_object)
    def make_function(bucket_name, zip_name):
        return cloudfunctions.Function(
            name,
            name=name,
            runtime="python310",
            entry_point=entry_point,
            source_archive_bucket=bucket_name,
            source_archive_object=zip_name,
            trigger_http=True,
            available_memory_mb=128,
            region=region,
            project=project,
            environment_variables={"ENV": config.get('ENV', 'production')},
            opts=pulumi.ResourceOptions(depends_on=[zip_object])
        )
    return pulumi.Output.all(bucket.name, zip_object.name).apply(lambda args: make_function(args[0], args[1]))

login_function = create_function("login", "login", source_dir=os.path.join(os.path.dirname(__file__), "login"))
signup_function = create_function("signup", "signup", source_dir=os.path.join(os.path.dirname(__file__), "signup"))
healthcheck_function = create_function("healthcheck", "healthcheck", source_dir=os.path.join(os.path.dirname(__file__), "healthcheck"))

__all__ = ["login_function", "signup_function", "healthcheck_function", "bucket"]
