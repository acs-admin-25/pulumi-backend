import pulumi
from pulumi_gcp import apigateway
import json
import uuid

class ACSRequest:
    def __init__(self, properties=None, required=None):
        self.schema = {
            "type": "object",
            "properties": properties if properties is not None else {
                "requestId": {"type": "string"},
                "payload": {"type": "object"}
            },
            "required": required if required is not None else ["requestId", "payload"]
        }

    def as_openapi(self):
        return {
            "content": {
                "application/json": {
                    "schema": self.schema
                }
            }
        }

class ACSResponse:
    def __init__(self, codes=None, messages=None):
        self.responses = {}
        default_codes = codes if codes is not None else [200, 400, 401, 404, 500]
        default_messages = messages if messages is not None else {
            200: "Success",
            400: "Bad request",
            401: "Unauthorized",
            404: "Not found",
            500: "Internal server error"
        }
        for code in default_codes:
            self.responses[str(code)] = {
                "description": default_messages.get(code, "")
            }

    def as_openapi(self):
        return self.responses

class Route:
    VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}

    def __init__(self, path, method, workflow=None, request_headers=None, summary=None, responses=None, request_body=None):
        self.path = path
        # Parse method(s)
        if isinstance(method, str):
            methods = [m.strip() for m in method.split(",")]
            for m in methods:
                if m not in self.VALID_METHODS:
                    raise ValueError(f"Invalid HTTP method: {m}. Must be one of {self.VALID_METHODS}")
            self.methods = methods
        else:
            raise ValueError("Method must be a comma-separated string of uppercase HTTP methods.")
        self.workflow = workflow
        self.request_headers = request_headers or []
        self.summary = summary
        if not isinstance(request_body, (ACSRequest, dict, type(None))):
            raise ValueError("request_body must be an instance of ACSRequest, dict, or None")
        if not isinstance(responses, (ACSResponse, dict, type(None))):
            raise ValueError("responses must be an instance of ACSResponse, dict, or None")
        self.request_body = request_body.as_openapi() if isinstance(request_body, ACSRequest) else (request_body if request_body is not None else None)
        self.responses = responses.as_openapi() if isinstance(responses, ACSResponse) else (responses if responses is not None else None)

class Gateway:
    def __init__(self, title, version):
        self.title = title
        self.version = version
        self.routes = []

    def add_route(self, route: Route):
        self.routes.append(route)

    def get_routes(self):
        return self.routes

    def add_routes(self, routes: list):
        self.routes.extend(routes)

    def generate_openapi_spec(self):
        paths = {}
        for route in self.routes:
            for method in route.methods:
                method_lower = method.lower()
                path_item = paths.setdefault(route.path, {})
                op = {
                    "summary": route.summary or "",
                    "responses": route.responses or {},
                }
                if route.request_body:
                    op["requestBody"] = route.request_body
                if route.request_headers:
                    op["parameters"] = [
                        {"name": h, "in": "header", "required": False, "schema": {"type": "string"}}
                        for h in route.request_headers
                    ]
                path_item[method_lower] = op
        spec = {
            "openapi": "3.0.0",
            "info": {"title": self.title, "version": self.version},
            "paths": paths
        }
        return json.dumps(spec)

    def deploy(self, gateway_id, display_name, region, project):
        openapi_spec = self.generate_openapi_spec()
        random_suffix = str(uuid.uuid4())[:8]
        api = apigateway.Api(f"{gateway_id}-api", api_id=gateway_id, project=project)
        config_name = f"{gateway_id}-config-{random_suffix}"
        api_config = apigateway.ApiConfig(
            config_name,
            api=api.name,
            api_config_id=config_name,
            openapi_documents=[{"document": {"path": "openapi.json", "contents": openapi_spec}}],
            project=project,
        )
        gateway = apigateway.Gateway(
            gateway_id,
            api_config=api_config.name,
            gateway_id=gateway_id,
            display_name=display_name,
            region=region,
            opts=pulumi.ResourceOptions(depends_on=[api_config])
        )
        return gateway, api, api_config

# Example usage:
# route1 = Route(path="/users", method="GET", summary="List users")
# gateway = Gateway(title="My API", version="1.0.0")
# gateway.add_route(route1)
# print(gateway.get_routes())