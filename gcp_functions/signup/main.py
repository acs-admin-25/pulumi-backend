def signup(request):
    print("Signup request received:", request)
    return {
        "statusCode": 201,
        "body": "Signup successful (placeholder)"
    }
