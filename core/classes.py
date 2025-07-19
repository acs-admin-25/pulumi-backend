import pulumi
from pulumi_gcp import apigateway
import json
import uuid
import base64

class ACSRequest:
    def __init__(self, properties, required):
        self.schema = {
            "type": "object",
            "properties": properties if properties is not None else {
                "requestId": {"type": "string"},
                "payload": {"type": "object"}
            },
            "required": required
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
    def __init__(self, codes: list, messages: dict):
        self.responses = {}
        default_codes = codes
        default_messages = messages

        for code in default_codes:
            self.responses[str(code)] = {
                "description": default_messages.get(code, "")
            }

    def as_openapi(self):
        return self.responses

class Route:
    VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}

    def __init__(self, path, method, workflow=None, request_headers=None, summary=None, responses=None, request_body=None, function_path=None):
        self.path = path
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
        self.function_path = function_path
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

    def generate_openapi_spec(self, route_function_urls=None):
        def _generate_spec(resolved_urls):
            paths = {}
            for route in self.routes:
                for method in route.methods:
                    method_lower = method.lower()
                    path_item = paths.setdefault(route.path, {})
                    # Generate a unique operationId for each operation
                    operation_id = f"{method_lower}_{route.path.replace('/', '_').replace('{', '').replace('}', '').strip('_')}"
                    if not operation_id or operation_id == method_lower:
                        operation_id = f"{method_lower}_root"
                    op = {
                        "operationId": operation_id,
                        "summary": route.summary or "",
                        "responses": route.responses or {},
                    }
                    # Convert OpenAPI 3.0 requestBody to Swagger 2.0 parameters
                    if route.request_body:
                        # Extract schema from OpenAPI 3.0 format
                        if "content" in route.request_body and "application/json" in route.request_body["content"]:
                            schema = route.request_body["content"]["application/json"]["schema"]
                            op["parameters"] = op.get("parameters", []) + [{
                                "name": "body",
                                "in": "body",
                                "required": True,
                                "schema": schema
                            }]
                    if route.request_headers:
                        op["parameters"] = op.get("parameters", []) + [
                            {"name": h, "in": "header", "required": False, "type": "string"}
                            for h in route.request_headers
                        ]
                    # Add x-google-backend if function URL is available
                    if resolved_urls and route.path in resolved_urls:
                        op["x-google-backend"] = {
                            "address": resolved_urls[route.path],
                            "protocol": "h2"
                        }
                    path_item[method_lower] = op
            spec = {
                "swagger": "2.0",
                "info": {"title": self.title, "version": self.version},
                "produces": ["application/json"],
                "consumes": ["application/json"],
                "paths": paths
            }
            return json.dumps(spec)
        
        # If route_function_urls contains Pulumi Output objects, resolve them first
        if route_function_urls:
            import pulumi
            return pulumi.Output.all(**route_function_urls).apply(_generate_spec)
        else:
            return _generate_spec({})

    def deploy(self, gateway_id, display_name, region, project, route_function_urls=None, depends_on=None):
        openapi_spec = self.generate_openapi_spec(route_function_urls)
        
        # Base64 encode the OpenAPI spec for GCP API Gateway
        def encode_spec(spec_content):
            if isinstance(spec_content, str):
                return base64.b64encode(spec_content.encode('utf-8')).decode('utf-8')
            return spec_content
        
        # Handle both direct strings and Pulumi Output objects
        if hasattr(openapi_spec, 'apply'):
            # If it's a Pulumi Output, apply the encoding function
            encoded_spec = openapi_spec.apply(encode_spec)
        else:
            # If it's a direct string, encode it directly
            encoded_spec = encode_spec(openapi_spec)
        
        # Create API first with proper dependencies
        api_deps = []
        if depends_on:
            if isinstance(depends_on, list):
                api_deps.extend(depends_on)
            else:
                api_deps.append(depends_on)
        
        api_opts = pulumi.ResourceOptions(
            depends_on=api_deps,
            delete_before_replace=True
        ) if api_deps else pulumi.ResourceOptions(delete_before_replace=True)
        api = apigateway.Api(
            f"{gateway_id}-api",
            api_id=gateway_id,
            project=project,
            opts=api_opts
        )
        
        random_suffix = str(uuid.uuid4())[:8]
        config_name = f"{gateway_id}-config-{random_suffix}"
        
        # ApiConfig depends on the Api and all previous dependencies
        api_config_deps = [api] + api_deps
        api_config_opts = pulumi.ResourceOptions(
            depends_on=api_config_deps,
            delete_before_replace=True
        )
        api_config = apigateway.ApiConfig(
            config_name,
            api=api.api_id,  # Use api_id instead of name
            api_config_id=config_name,
            openapi_documents=[{"document": {"path": "openapi.json", "contents": encoded_spec}}],
            project=project,
            opts=api_config_opts
        )
        
        # Gateway depends on ApiConfig and any additional dependencies
        gateway_deps = [api_config] + api_deps
        gateway_opts = pulumi.ResourceOptions(
            depends_on=gateway_deps,
            delete_before_replace=True
        )
        gateway = apigateway.Gateway(
            gateway_id,
            api_config=api_config.name,
            gateway_id=gateway_id,
            display_name=display_name,
            region=region,
            opts=gateway_opts
        )
        return gateway, api, api_config

# Example usage:
# route1 = Route(path="/users", method="GET", summary="List users")
# gateway = Gateway(title="My API", version="1.0.0")
# gateway.add_route(route1)
# print(gateway.get_routes())