from pulumi_gcp import apigateway, projects
from core.classes import Route, Gateway, ACSRequest, ACSResponse
from core.config import load_config
from gcp_functions import login_function, signup_function, healthcheck_function

# Resource creation - define all resources but don't deploy

"""Create and configure API Gateway resources without deploying"""
config = load_config()
project = config['pulumi_project']

# Define routes
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

# Create and configure gateway
gateway = Gateway(title="ACS API Gateway", version="1.0.0")
gateway.add_routes([login_route, signup_route])

# Map routes to function URLs
route_function_urls = {
    "/login": login_function.https_trigger_url,
    "/signup": signup_function.https_trigger_url,
}

resources = {
    "gateway": gateway,
    "route_function_urls": route_function_urls,
    "functions": [login_function, signup_function, healthcheck_function],
    "config": config,
    "project": project
}

def deploy():
    """Deploy API Gateway resources, returning deployed resources"""
    # Get created resources
    gateway = resources["gateway"]
    route_function_urls = resources["route_function_urls"]
    functions = resources["functions"]
    config = resources["config"]
    project = resources["project"]

    # Enable GCP API Gateway service
    api_gateway_api = projects.Service("api-gateway-api",
        service="apigateway.googleapis.com",
        project=project,
        disable_on_destroy=False
    )

    # Deploy API Gateway with all dependencies
    gateway_resource, api_resource, api_config_resource = gateway.deploy(
        gateway_id="acs-public-gateway",
        display_name="acs gateway",
        region=config.get("region", "us-central1"),
        project=project,
        route_function_urls=route_function_urls,
        depends_on=functions + [api_gateway_api]
    )

    # Return deployed resources for main stack
    return {
        "gateway_resource": gateway_resource,
        "api_resource": api_resource,
        "api_config_resource": api_config_resource,
        "gateway_url": gateway_resource.default_hostname,
        "api_service": api_gateway_api
    }
