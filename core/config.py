import os
import importlib
import pulumi


def load_config():
    """
    Loads configuration variables from environment, Pulumi config, and imports the project module.
    Returns a dictionary of global config variables.
    """
    config = {}
    # Load environment variables
    config['ENV'] = os.environ.get('ENV', 'development')
    config['DEBUG'] = os.environ.get('DEBUG', 'False') == 'True'
    config['PROJECT_NAME'] = os.environ.get('PROJECT_NAME', 'default_project')
    # Import project module if specified
    project_module_name = os.environ.get('PROJECT_MODULE')
    if project_module_name:
        try:
            config['project'] = importlib.import_module(project_module_name)
        except ImportError:
            config['project'] = None
    else:
        config['project'] = None
    # Load Pulumi config
    gcp_config = pulumi.Config("gcp")
    config['pulumi_project'] = gcp_config.require("project")
    config['pulumi_region'] = gcp_config.get("region") or "us-central1"
    return config

# Example usage:
# config = load_config()
# print(config)
