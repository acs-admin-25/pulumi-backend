"""A Google Cloud Python Pulumi program"""

import pulumi
from pulumi_gcp import storage
from gcp_api_gateway import gateway, api, api_config

# Get current project configuration
project = pulumi.Config("gcp").require("project")
region = pulumi.Config("gcp").get("region") or "us-central1"

# Create a GCP resource (Storage Bucket)
bucket = storage.Bucket('my-bucket', location="US")

# Export the important values
pulumi.export('bucket_name', bucket.url)
pulumi.export('api_gateway_url', gateway.default_hostname.apply(lambda hostname: f"https://{hostname}"))
pulumi.export('function_url', sample_function.https_trigger_url)
pulumi.export('api_id', api.name)
pulumi.export('gateway_id', gateway.name)
