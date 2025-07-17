def login(request):
    print("Login request received:", request)
    return {
        "statusCode": 200,
        "body": "Login successful (placeholder)"
    }
