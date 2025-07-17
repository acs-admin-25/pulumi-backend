def healthcheck(request):
    print("Healthcheck request received:", request)
    return {
        "statusCode": 200,
        "body": "Healthcheck OK (placeholder)"
    }
