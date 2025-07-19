"""
Gateway Manager - Handles incremental updates to API Gateway configurations
instead of replacing the entire gateway when only routes change.
"""

import pulumi
from pulumi_gcp import apigateway
import json
import uuid
import base64
from typing import Dict, List, Optional
from .resource_importer import ResourceImporter

class GatewayManager:
    """
    Manages API Gateway configurations with smart update strategies.
    
    This class can:
    1. Update only the API configuration when routes change
    2. Replace the entire gateway when structural changes are needed
    3. Handle both scenarios based on what actually changed
    """
    
    def __init__(self, gateway_id: str, project: str, region: str):
        self.gateway_id = gateway_id
        self.project = project
        self.region = region
        self._api = None
        self._current_config = None
        self._gateway = None
    
    def get_or_create_api(self, depends_on: Optional[List] = None):
        """
        Get existing API or create new one if it doesn't exist.
        Uses import/protect strategy to handle existing resources.
        """
        if self._api is None:
            api_deps = depends_on or []
            
            # Use ResourceImporter to handle existing APIs
            import_id = ResourceImporter.get_api_import_id(self.project, self.gateway_id)
            
            self._api = ResourceImporter.try_import_or_create(
                resource_class=apigateway.Api,
                resource_name=f"{self.gateway_id}-api",
                import_id=import_id,
                resource_args={
                    "api_id": self.gateway_id,
                    "project": self.project
                },
                opts=pulumi.ResourceOptions(depends_on=api_deps)
            )
        
        return self._api
    
    def create_or_update_config(self, openapi_spec: str, depends_on: Optional[List] = None):
        """
        Create a new API configuration. Each config gets a unique ID
        so we can deploy new configurations without conflicts.
        """
        # Ensure we have the API
        api = self.get_or_create_api(depends_on)
        
        # Generate unique config name with timestamp for versioning
        import time
        timestamp = str(int(time.time()))
        config_name = f"{self.gateway_id}-config-{timestamp}"
        
        # Base64 encode the OpenAPI spec
        def encode_spec(spec_content):
            if isinstance(spec_content, str):
                return base64.b64encode(spec_content.encode('utf-8')).decode('utf-8')
            return spec_content
        
        # Handle both direct strings and Pulumi Output objects
        if hasattr(openapi_spec, 'apply'):
            encoded_spec = openapi_spec.apply(encode_spec)
        else:
            encoded_spec = encode_spec(openapi_spec)
        
        # Create new config
        api_config_deps = [api] + (depends_on or [])
        self._current_config = apigateway.ApiConfig(
            config_name,
            api=api.api_id,
            api_config_id=config_name,
            openapi_documents=[{
                "document": {
                    "path": "openapi.json", 
                    "contents": encoded_spec
                }
            }],
            project=self.project,
            opts=pulumi.ResourceOptions(
                depends_on=api_config_deps,
                delete_before_replace=True
            )
        )
        
        return self._current_config
    
    def get_or_create_gateway(self, display_name: str, api_config, depends_on: Optional[List] = None):
        """
        Get existing gateway or create new one, updating it to use the new config.
        """
        if self._gateway is None:
            gateway_deps = [api_config] + (depends_on or [])
            
            # Use ResourceImporter to handle existing gateways
            import_id = ResourceImporter.get_gateway_import_id(self.project, self.region, self.gateway_id)
            
            self._gateway = ResourceImporter.try_import_or_create(
                resource_class=apigateway.Gateway,
                resource_name=f"{self.gateway_id}-gateway",
                import_id=import_id,
                resource_args={
                    "api_config": api_config.name,
                    "gateway_id": self.gateway_id,
                    "display_name": display_name,
                    "region": self.region,
                    "project": self.project
                },
                opts=pulumi.ResourceOptions(depends_on=gateway_deps)
            )
        
        return self._gateway
    
    def deploy_with_smart_updates(self, openapi_spec: str, display_name: str, depends_on: Optional[List] = None):
        """
        Deploy API Gateway with smart update strategy:
        1. Always create new API config (versioned)
        2. Update gateway to point to new config
        3. Old configs are automatically cleaned up by GCP
        """
        # Step 1: Ensure API exists
        api = self.get_or_create_api(depends_on)
        
        # Step 2: Create new configuration
        api_config = self.create_or_update_config(openapi_spec, depends_on)
        
        # Step 3: Update gateway to use new config
        gateway = self.get_or_create_gateway(display_name, api_config, depends_on)
        
        return {
            'gateway': gateway,
            'api': api,
            'api_config': api_config
        }

def create_gateway_manager(gateway_id: str, project: str, region: str) -> GatewayManager:
    """Factory function to create a GatewayManager instance."""
    return GatewayManager(gateway_id, project, region)
