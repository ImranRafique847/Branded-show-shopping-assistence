import boto3
import json
import time
import uuid
import os
import sys

from dotenv import load_dotenv
load_dotenv()

REGION = os.getenv("AWS_REGION", "us-east-1")
LAMBDA_URL_HOST = "i5cfzoa7rqtak6c3href27m4lm0urqpi.lambda-url.us-east-1.on.aws"
LAMBDA_FUNCTION_URL = f"https://{LAMBDA_URL_HOST}/"

client = boto3.client("cloudfront", region_name=REGION)

print("Checking for existing distributions...")
existing_id = None
existing_domain = None
try:
    paginator = client.get_paginator("list_distributions")
    for page in paginator.paginate():
        items = page.get("DistributionList", {}).get("Items", [])
        for dist in items:
            for origin in dist.get("Origins", {}).get("Items", []):
                if LAMBDA_URL_HOST in origin.get("DomainName", ""):
                    existing_id = dist["Id"]
                    existing_domain = dist["DomainName"]
                    print(f"Found existing: {existing_id} -> {existing_domain}")
                    break
except Exception as e:
    print(f"Could not list distributions: {e}")
    sys.exit(1)

if existing_id:
    dist_id = existing_id
    domain_name = existing_domain
else:
    print("Creating new CloudFront distribution...")
    caller_ref = str(uuid.uuid4())
    config = {
        "CallerReference": caller_ref,
        "Comment": "TRETTER shopping assistant CloudFront distribution",
        "Enabled": True,
        "DefaultRootObject": "",
        "Origins": {
            "Quantity": 1,
            "Items": [{
                "Id": "tretter-lambda-origin",
                "DomainName": LAMBDA_URL_HOST,
                "CustomOriginConfig": {
                    "HTTPPort": 80, "HTTPSPort": 443,
                    "OriginProtocolPolicy": "https-only",
                    "OriginSslProtocols": {"Quantity": 1, "Items": ["TLSv1.2"]},
                },
            }],
        },
        "DefaultCacheBehavior": {
            "TargetOriginId": "tretter-lambda-origin",
            "ViewerProtocolPolicy": "redirect-to-https",
            "AllowedMethods": {
                "Quantity": 7,
                "Items": ["GET","HEAD","OPTIONS","PUT","POST","PATCH","DELETE"],
                "CachedMethods": {"Quantity": 2, "Items": ["GET","HEAD"]},
            },
            "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",
            "OriginRequestPolicyId": "b689b0a8-53d0-40ab-baf2-68738e2966ac",
            "Compress": True,
        },
        "PriceClass": "PriceClass_All",
    }
    resp = client.create_distribution(DistributionConfig=config)
    dist = resp["Distribution"]
    dist_id = dist["Id"]
    domain_name = dist["DomainName"]
    print(f"Created: {dist_id} -> {domain_name}")

print(f"\nWaiting for Deployed status...")
start = time.time()
while True:
    resp = client.get_distribution(Id=dist_id)
    status = resp["Distribution"]["Status"]
    elapsed = int(time.time() - start)
    print(f"  [{elapsed}s] {status}")
    if status == "Deployed":
        break
    if elapsed > 1200:
        print("Timeout."); sys.exit(1)
    time.sleep(30)

print(f"\nDistribution ID : {dist_id}")
print(f"CloudFront URL  : https://{domain_name}/")

result = {"distribution_id": dist_id, "cloudfront_domain": domain_name,
          "cloudfront_url": f"https://{domain_name}/"}
with open("cloudfront_result.json", "w") as f:
    json.dump(result, f, indent=2)
print("Results saved to cloudfront_result.json")
