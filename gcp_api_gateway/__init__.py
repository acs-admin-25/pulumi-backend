import pulumi
from pulumi_gcp import apigateway, projects, serviceaccount, cloudfunctions
from core.classes import Route, Gateway, ACSRequest, ACSResponse
from core.config import load_config
import os
import uuid


config = load_config()
project = config['pulumi_project']

# API to enable GCP API Gateway
api_gateway_api = projects.Service("api-gateway-api",
    service="apigateway.googleapis.com",
    project=project,
    disable_on_destroy=False
)

# Generate routes for API Gateway
login_route = Route(
    path="/login",
    method="POST",
    summary="User login",
    request_body=ACSRequest(properties={
        "username": {"type": "string"},
        "password": {"type": "string"}
    }, required=["username", "password"]),
    responses=ACSResponse(codes=[200, 401], messages={200: "Login successful", 401: "Unauthorized"}),
    function_path="gcp_functions/login/main.py"
)

signup_route = Route(
    path="/signup",
    method="POST",
    summary="User signup",
    request_body=ACSRequest(properties={
        "username": {"type": "string"},
        "password": {"type": "string"},
        "email": {"type": "string"}
    }, required=["username", "password", "email"]),
    responses=ACSResponse(codes=[201, 400], messages={201: "Signup successful", 400: "Bad request"}),
    function_path="gcp_functions/signup/main.py"
)

# Optionally, add a healthcheck route if needed:
# healthcheck_route = Route(
#     path="/healthcheck",
#     method="GET",
#     summary="Healthcheck",
#     responses=ACSResponse(codes=[200], messages={200: "Healthcheck OK"}),
#     function_path="gcp_functions/healthcheck/main.py"
# )

routes = [login_route, signup_route]

gateway = Gateway(title="ACS API Gateway", version="1.0.0")
gateway.add_routes(routes)

# For each route, set up a list of associated cloud functions and map their URLs
route_functions = []
route_function_urls = {}
for route in routes:
    if route.function_path:
        fname = os.path.basename(os.path.dirname(route.function_path))
        cloud_function = cloudfunctions.Function(
            f"{fname}",
            name=f"{fname}",
            runtime="python39",
            entry_point=fname,
            source_archive_bucket=config["bucket_name"],
            source_archive_object=config.get(f"{fname}_object_name"),
            trigger_http=True,
            available_memory_mb=128,
            project=project,
            region=config.get("region", "us-central1"),
        )
        route_functions.append(cloud_function)
        route_function_urls[route.path] = cloud_function.https_trigger_url


# Deploy API Gateway
gateway_resource, api_resource, api_config_resource = gateway.deploy(
    gateway_id="acs-public-gateway",
    display_name="acs gateway",
    region=config.get("region", "us-central1"),
    project=project,
    route_function_urls=route_function_urls,
    depends_on=route_functions
)

# Export the important values to pulumi main stack
__all__ = ["gateway", "gateway_resource", "api_resource", "api_config_resource"]
