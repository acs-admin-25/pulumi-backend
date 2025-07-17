import pulumi
from pulumi_gcp import apigateway, projects, serviceaccount
from core.classes import Route, Gateway, ACSRequest, ACSResponse
from core.config import load_config


config = load_config()
project = config['pulumi_project']

# API to enable GCP API Gateway
api_gateway_api = projects.Service("api-gateway-api",
    service="apigateway.googleapis.com",
    project=project,
    disable_on_destroy=False
)

login_route = Route(
    path="/login",
    method="POST",
    summary="User login",
    request_body=ACSRequest(properties={
        "username": {"type": "string"},
        "password": {"type": "string"}
    }, required=["username", "password"]),
    responses=ACSResponse(codes=[200, 401], messages={200: "Login successful", 401: "Unauthorized"}),
    source="gcp_functions/login/main.py"
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
    source="gcp_functions/signup/main.py"
)

# Optionally, add a healthcheck route if needed:
# healthcheck_route = Route(
#     path="/healthcheck",
#     method="GET",
#     summary="Healthcheck",
#     responses=ACSResponse(codes=[200], messages={200: "Healthcheck OK"}),
#     source="gcp_functions/healthcheck/main.py"
# )

routes = [login_route, signup_route]

gateway = Gateway(title="ACS API Gateway", version="1.0.0")
gateway.add_routes(routes)

gateway_resource, api_resource, api_config_resource = gateway.deploy(
    gateway_id="acs-public-gateway",
    display_name="acs gateway",
    region=config.get("region", "us-central1"),
    project=project
)

__all__ = ["gateway", "gateway_resource", "api_resource", "api_config_resource"]
