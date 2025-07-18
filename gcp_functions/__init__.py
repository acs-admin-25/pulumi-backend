import pulumi
from pulumi_gcp import cloudfunctions, projects
from pulumi_gcp.storage import BucketObject
from pulumi import FileArchive
import os
from core.config import load_config
import gcp_buckets # Ensure buckets are created before functions

# Resource creation - define all resources but don't deploy
config = load_config()
project = config['pulumi_project']
region = config['pulumi_region']
functions_bucket = gcp_buckets.functions_bucket

# Enable Cloud Functions API
cloudfunctions_service = projects.Service(
    "cloudfunctions-api",
    service="cloudfunctions.googleapis.com",
    project=project,
    disable_on_destroy=False
)

# Enable Cloud Build API (required for Cloud Functions deployment)
cloudbuild_service = projects.Service(
    "cloudbuild-api", 
    service="cloudbuild.googleapis.com",
    project=project,
    disable_on_destroy=False
)

# Create Cloud Functions from source directories
def create_function(name, entry_point, source_dir=None):
    if source_dir is None:
        source_dir = os.path.join(os.path.dirname(__file__), name)
    zip_asset = FileArchive(source_dir)
    
    # Create the zip object in the bucket
    zip_object = BucketObject(
        f"{name}-zip",
        bucket=functions_bucket.name,
        source=zip_asset,
        name=f"{name}.zip",
        opts=pulumi.ResourceOptions(depends_on=[functions_bucket])
    )
    
    # Create the Cloud Function
    function = cloudfunctions.Function(
        name,
        name=name,
        runtime="python310",
        entry_point=entry_point,
        source_archive_bucket=functions_bucket.name,
        source_archive_object=zip_object.name,
        trigger_http=True,
        available_memory_mb=128,
        region=region,
        project=project,
        environment_variables={"ENV": config.get('ENV', 'production')},
        opts=pulumi.ResourceOptions(depends_on=[zip_object, cloudfunctions_service, cloudbuild_service])
    )
    
    return function


def deploy():
    # Create all functions at module level
    login_function = create_function("login", "login", source_dir=os.path.join(os.path.dirname(__file__), "login"))
    signup_function = create_function("signup", "signup", source_dir=os.path.join(os.path.dirname(__file__), "signup"))
    healthcheck_function = create_function("healthcheck", "healthcheck", source_dir=os.path.join(os.path.dirname(__file__), "healthcheck"))

    """Deploy function and return function resources"""
    return {
        "login_function": login_function,
        "signup_function": signup_function,
        "healthcheck_function": healthcheck_function,
        "bucket": functions_bucket.name
    }
