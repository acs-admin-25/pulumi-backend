import functions_framework
from flask import jsonify

@functions_framework.http
def login(request):
    """HTTP Cloud Function for user login."""
    print("Login request received:", request)
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    # Set CORS headers for the main request
    headers = {'Access-Control-Allow-Origin': '*'}
    
    try:
        # Process login logic here
        return jsonify({
            "statusCode": 200,
            "body": "Login successful (placeholder)"
        }), 200, headers
    except Exception as e:
        return jsonify({
            "statusCode": 500,
            "body": f"Internal server error: {str(e)}"
        }), 500, headers
