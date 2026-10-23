#!/usr/bin/env python3
"""
deploy_lambda.py
================
Full deployment script: builds the Docker image, pushes to ECR,
creates/updates the Lambda function, and enables a public Function URL.

Run once to deploy, run again any time to push updates.

Usage:
    python deploy_lambda.py

Requirements:
    - Docker running
    - AWS CLI configured (uses credentials from .env)
    - IAM user needs: ECR, Lambda, IAM permissions (see README)
"""

import os
import subprocess
import sys
import json
import time
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
ACCOUNT_ID   = "876493682275"
REGION       = os.getenv("AWS_REGION", "us-east-1")
ECR_REPO     = "ai-shopping-assistant"   # reuse existing repo — Lead-Generation can push here
LAMBDA_NAME  = "tretter-shopping-assistant"
IMAGE_TAG    = "tretter-latest"
ECR_URI      = f"{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/{ECR_REPO}"
IMAGE_URI    = f"{ECR_URI}:{IMAGE_TAG}"

# Lambda config
LAMBDA_MEMORY  = 3008   # MB — FAISS search needs memory
LAMBDA_TIMEOUT = 60     # seconds
LAMBDA_ROLE    = f"arn:aws:iam::{ACCOUNT_ID}:role/tretter-lambda-role"

# ── Helpers ───────────────────────────────────────────────────────────────────
def run(cmd, check=True, capture=False):
    print(f"\n$ {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(
        cmd, shell=isinstance(cmd, str),
        capture_output=capture, text=True
    )
    if check and result.returncode != 0:
        if capture:
            print(result.stderr)
        sys.exit(result.returncode)
    return result


def run_out(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout.strip()


def aws(args, capture=False):
    return run(["aws"] + args +
               ["--region", REGION,
                "--output", "json"], check=False, capture=capture)


# ── Step 1: Create ECR repo (ignore if already exists) ───────────────────────
def ensure_ecr_repo():
    print("\n[1/6] Using existing ECR repository...")
    print(f"  ECR repo: {ECR_URI}")


# ── Step 2: Docker login to ECR ───────────────────────────────────────────────
def docker_login():
    print("\n[2/6] Logging Docker into ECR...")
    pwd = run_out(f"aws ecr get-login-password --region {REGION}")
    run(f'docker login --username AWS --password-stdin {ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com',
        cmd_input=pwd)


def run_with_input(cmd, input_text):
    print(f"\n$ {cmd}")
    result = subprocess.run(cmd, shell=True, input=input_text,
                            capture_output=False, text=True)
    if result.returncode != 0:
        sys.exit(result.returncode)


# ── Step 3: Build Docker image ────────────────────────────────────────────────
def build_image():
    print("\n[3/6] Building Docker image (this takes a few minutes)...")
    run(["docker", "build", "--platform", "linux/amd64", "-t", ECR_REPO, "."])
    run(["docker", "tag", ECR_REPO, IMAGE_URI])
    print(f"  Tagged: {IMAGE_URI}")


# ── Step 4: Push to ECR ───────────────────────────────────────────────────────
def push_image():
    print("\n[4/6] Pushing image to ECR...")
    # Login
    pwd = run_out(f"aws ecr get-login-password --region {REGION}")
    login_cmd = f"docker login --username AWS --password-stdin {ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com"
    subprocess.run(login_cmd, shell=True, input=pwd, text=True)
    run(["docker", "push", IMAGE_URI])
    print(f"  Pushed: {IMAGE_URI}")


# ── Step 5: Create IAM role (if needed) ──────────────────────────────────────
def ensure_lambda_role():
    print("\n[5/6] Ensuring Lambda IAM role exists...")
    r = subprocess.run(
        ["aws", "iam", "get-role", "--role-name", "tretter-lambda-role",
         "--region", REGION, "--output", "json"],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        print("  IAM role already exists.")
        return

    trust = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    })

    subprocess.run([
        "aws", "iam", "create-role",
        "--role-name", "tretter-lambda-role",
        "--assume-role-policy-document", trust,
        "--region", REGION
    ], check=True)

    # Attach managed policies
    for policy in [
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        "arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
        "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
    ]:
        subprocess.run([
            "aws", "iam", "attach-role-policy",
            "--role-name", "tretter-lambda-role",
            "--policy-arn", policy,
            "--region", REGION
        ], check=True)
        print(f"  Attached: {policy.split('/')[-1]}")

    print("  Waiting 15s for IAM role to propagate...")
    time.sleep(15)


# ── Step 6: Create/update Lambda + enable Function URL ───────────────────────
def deploy_lambda():
    print("\n[6/6] Deploying Lambda function...")

    # Read env vars from .env to pass as Lambda environment variables.
    env_vars = {}
    for key in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION",
                "EMBEDDING_MODEL_ID", "IMAGE_EMBEDDING_MODEL_ID", "CHAT_MODEL_ID",
                "DYNAMODB_TABLE", "LEADS_TABLE"]:
        v = os.getenv(key, "")
        if v:
            env_vars[key] = v
    # Override index paths to /var/task (Lambda working dir)
    env_vars.update({
        "TEXT_INDEX": "text_index.faiss",
        "TEXT_META": "text_metadata.json",
        "IMAGE_INDEX": "image_index.faiss",
        "IMAGE_META": "image_metadata.json",
    })
    env_str = "Variables={" + ",".join(f"{k}={v}" for k, v in env_vars.items()) + "}"

    # Check if function exists
    r = subprocess.run(
        ["aws", "lambda", "get-function", "--function-name", LAMBDA_NAME,
         "--region", REGION, "--output", "json"],
        capture_output=True, text=True
    )

    if r.returncode != 0:
        # Create new function
        print("  Creating new Lambda function...")
        subprocess.run([
            "aws", "lambda", "create-function",
            "--function-name", LAMBDA_NAME,
            "--package-type", "Image",
            "--code", f"ImageUri={IMAGE_URI}",
            "--role", LAMBDA_ROLE,
            "--memory-size", str(LAMBDA_MEMORY),
            "--timeout", str(LAMBDA_TIMEOUT),
            "--environment", env_str,
            "--region", REGION,
        ], check=True)
    else:
        # Update existing function
        print("  Updating existing Lambda function...")
        subprocess.run([
            "aws", "lambda", "update-function-code",
            "--function-name", LAMBDA_NAME,
            "--image-uri", IMAGE_URI,
            "--region", REGION,
        ], check=True)
        print("  Waiting for update to complete...")
        time.sleep(10)
        subprocess.run([
            "aws", "lambda", "update-function-configuration",
            "--function-name", LAMBDA_NAME,
            "--memory-size", str(LAMBDA_MEMORY),
            "--timeout", str(LAMBDA_TIMEOUT),
            "--environment", env_str,
            "--region", REGION,
        ], check=True)

    # Enable Function URL (public HTTPS endpoint — no API Gateway needed)
    r2 = subprocess.run([
        "aws", "lambda", "get-function-url-config",
        "--function-name", LAMBDA_NAME,
        "--region", REGION, "--output", "json"
    ], capture_output=True, text=True)

    if r2.returncode != 0:
        print("  Creating Function URL...")
        r3 = subprocess.run([
            "aws", "lambda", "create-function-url-config",
            "--function-name", LAMBDA_NAME,
            "--auth-type", "NONE",
            "--cors", "AllowOrigins=*,AllowMethods=*,AllowHeaders=*",
            "--region", REGION, "--output", "json"
        ], capture_output=True, text=True, check=True)
        url_data = json.loads(r3.stdout)
        # Allow public access
        subprocess.run([
            "aws", "lambda", "add-permission",
            "--function-name", LAMBDA_NAME,
            "--statement-id", "FunctionURLAllowPublicAccess",
            "--action", "lambda:InvokeFunctionUrl",
            "--principal", "*",
            "--function-url-auth-type", "NONE",
            "--region", REGION
        ], capture_output=True)
    else:
        url_data = json.loads(r2.stdout)

    url = url_data.get("FunctionUrl", "")
    print(f"\n  ✅ Lambda Function URL: {url}")
    return url


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  TRETTER Shopping Assistant — Lambda Deployment")
    print("=" * 60)
    ensure_ecr_repo()
    build_image()
    push_image()
    ensure_lambda_role()
    deploy_lambda()
    print("\n✅ Deployment complete!")
    print(f"   ECR image: {IMAGE_URI}")
    print(f"   Lambda:    {LAMBDA_NAME} ({REGION})")
