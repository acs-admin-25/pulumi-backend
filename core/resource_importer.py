"""
Resource Import Utility - Helps with importing existing GCP resources
to avoid conflicts when resources already exist.
"""

import pulumi
from typing import Optional, Dict, Any

class ResourceImporter:
    """
    Utility class to handle importing existing GCP resources.
    This helps avoid '409 Resource already exists' errors.
    """
    
    @staticmethod
    def try_import_or_create(
        resource_class,
        resource_name: str,
        import_id: str,
        resource_args: Dict[str, Any],
        opts: Optional[pulumi.ResourceOptions] = None
    ):
        """
        Try to import an existing resource, if that fails, create a new one.
        
        Args:
            resource_class: The Pulumi resource class (e.g., apigateway.Api)
            resource_name: The Pulumi resource name
            import_id: The GCP resource ID for importing
            resource_args: Arguments for creating the resource
            opts: Resource options
            
        Returns:
            The imported or created resource
        """
        if opts is None:
            opts = pulumi.ResourceOptions()
        
        # First try to import the existing resource
        try:
            import_opts = pulumi.ResourceOptions(
                import_=import_id,
                depends_on=opts.depends_on,
                protect=False,  # Allow replacement if needed
                delete_before_replace=True
            )
            
            return resource_class(
                resource_name,
                opts=import_opts,
                **resource_args
            )
        except Exception as e:
            # If import fails, create new resource with replacement behavior
            create_opts = pulumi.ResourceOptions(
                depends_on=opts.depends_on,
                delete_before_replace=True
            )
            
            return resource_class(
                resource_name,
                opts=create_opts,
                **resource_args
            )
    
    @staticmethod
    def get_api_import_id(project: str, api_id: str) -> str:
        """Generate the import ID for a GCP API Gateway API."""
        return f"projects/{project}/locations/global/apis/{api_id}"
    
    @staticmethod
    def get_gateway_import_id(project: str, region: str, gateway_id: str) -> str:
        """Generate the import ID for a GCP API Gateway."""
        return f"projects/{project}/locations/{region}/gateways/{gateway_id}"
    
    @staticmethod
    def get_function_import_id(project: str, region: str, function_name: str) -> str:
        """Generate the import ID for a Cloud Function v2."""
        return f"projects/{project}/locations/{region}/functions/{function_name}"
