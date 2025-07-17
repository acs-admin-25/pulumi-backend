"""A Google Cloud Python Pulumi program"""

import pulumi
from gcp_api_gateway import gateway_resource, api_resource, api_config_resource
from gcp_functions import login_function, signup_function, healthcheck_function, bucket

# Export the important values
pulumi.export('bucket_name', bucket.url)
pulumi.export('api_gateway_url', gateway_resource.default_hostname.apply(lambda hostname: f"https://{hostname}"))
pulumi.export('login_function_url', login_function.https_trigger_url)
pulumi.export('signup_function_url', signup_function.https_trigger_url)
pulumi.export('healthcheck_function_url', healthcheck_function.https_trigger_url)
pulumi.export('api_id', api_resource.name)
pulumi.export('gateway_id', gateway_resource.name)
