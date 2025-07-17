import pulumi
from pulumi_gcp import cloudfunctions
from pulumi_gcp.storage import Bucket

# Get current project configuration
project = pulumi.Config("gcp").require("project")
region = pulumi.Config("gcp").get("region") or "us-central1"

# Create a GCP resource (Storage Bucket)
bucket = Bucket('my-bucket', location="US")

# Create Cloud Functions for each route
def create_function(name, entry_point):
    return cloudfunctions.Function(
        name,
        name=name,
        runtime="python310",
        entry_point=entry_point,
        source_archive_bucket=bucket.name,
        source_archive_object=f"{name}.zip",
        trigger_http=True,
        available_memory_mb=128,
        region=region,
        project=project,
        environment_variables={"ENV": "production"},
    )

login_function = create_function("login", "login")
signup_function = create_function("signup", "signup")
healthcheck_function = create_function("healthcheck", "healthcheck")

__all__ = ["login_function", "signup_function", "healthcheck_function", "bucket"]
