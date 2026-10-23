"""
lambda_handler.py
=================
Mangum adapter — wraps the FastAPI app so it runs inside AWS Lambda.
Lambda receives HTTP events (from Function URL or API Gateway) and
Mangum translates them to ASGI calls that FastAPI understands.
"""
from mangum import Mangum
from main import app

# lifespan="off" because Lambda doesn't support persistent connections.
# api_gateway_base_path handles Lambda Function URL (payload format 2.0)
handler = Mangum(app, lifespan="off", api_gateway_base_path=None)
