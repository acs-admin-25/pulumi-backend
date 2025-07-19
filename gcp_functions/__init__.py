import pulumi
from pulumi_gcp import cloudfunctionsv2, projects
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

# Enable Cloud Functions v2 API
cloudfunctions_service = projects.Service(
    "cloudfunctions-api",
    service="cloudfunctions.googleapis.com",
    project=project,
    disable_on_destroy=False
)

# Enable Cloud Run API (required for Cloud Functions v2)
cloudrun_service = projects.Service(
    "cloudrun-api",
    service="run.googleapis.com", 
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

# Create Cloud Functions v2 from source directories
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
    
    # Create the Cloud Function v2
    function = cloudfunctionsv2.Function(
        name,
        name=name,
        location=region,
        project=project,
        build_config=cloudfunctionsv2.FunctionBuildConfigArgs(
            runtime="python310",
            entry_point=entry_point,
            source=cloudfunctionsv2.FunctionBuildConfigSourceArgs(
                storage_source=cloudfunctionsv2.FunctionBuildConfigSourceStorageSourceArgs(
                    bucket=functions_bucket.name,
                    object=zip_object.name,
                )
            )
        ),
        service_config=cloudfunctionsv2.FunctionServiceConfigArgs(
            max_instance_count=100,
            min_instance_count=0,
            available_memory="128Mi",
            timeout_seconds=60,
            environment_variables={"ENV": config.get('ENV', 'production')},
            ingress_settings="ALLOW_ALL",
            all_traffic_on_latest_revision=True,
        ),
        opts=pulumi.ResourceOptions(depends_on=[zip_object, cloudfunctions_service, cloudrun_service, cloudbuild_service])
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
