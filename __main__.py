"""A Google Cloud Python Pulumi program"""

import pulumi
import gcp_buckets
import gcp_functions
import gcp_api_gateway
import core.config

# Access bucket resource directly
bucket_resources = gcp_buckets.deploy()
functions_bucket = bucket_resources['functions_bucket']

# Deploy functions
function_resources = gcp_functions.deploy()
login_function = function_resources['login_function']
signup_function = function_resources['signup_function']
healthcheck_function = function_resources['healthcheck_function']

# Deploy API Gateway
api_gateway_resources = {
    "route_function_urls": {
        "/login": login_function.https_trigger_url,
        "/signup": signup_function.https_trigger_url,
    },
    "functions": [login_function, signup_function],
}
api_resources = gcp_api_gateway.deploy(api_gateway_resources)
gateway_resource = api_resources['gateway_resource']
api_resource = api_resources['api_resource']

# Export the important values
pulumi.export('bucket_name', functions_bucket.url)
pulumi.export('api_gateway_url', gateway_resource.default_hostname.apply(lambda hostname: f"https://{hostname}"))
pulumi.export('api_id', api_resource.name)
pulumi.export('gateway_id', gateway_resource.name)
pulumi.export('login_function_url', login_function.https_trigger_url)
pulumi.export('signup_function_url', signup_function.https_trigger_url)
pulumi.export('healthcheck_function_url', healthcheck_function.https_trigger_url)
