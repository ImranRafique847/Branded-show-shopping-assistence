# ──────────────────────────────────────────────────────────────
# TRETTER AI Shopping Assistant — Lambda Container Image
# ──────────────────────────────────────────────────────────────
FROM public.ecr.aws/lambda/python:3.11

WORKDIR /var/task

# Install build tools needed for faiss-cpu and other packages
RUN yum install -y gcc gcc-c++ make && yum clean all

# Upgrade pip
RUN pip install --upgrade pip

# Install faiss-cpu first using pre-built wheel (avoids compile issues)
RUN pip install --no-cache-dir "faiss-cpu==1.7.4" --prefer-binary

# Install remaining dependencies
COPY requirements_lambda.txt .
RUN pip install --no-cache-dir -r requirements_lambda.txt --prefer-binary

# Copy application code
COPY main.py .
COPY lambda_handler.py .
COPY static/ static/

# Copy FAISS indexes and metadata (baked into the image)
COPY text_index.faiss .
COPY text_metadata.json .
COPY image_index.faiss .
COPY image_metadata.json .

# Lambda reads env vars from function configuration (not .env file)
# But copy .env as fallback for local testing
COPY .env .

# Lambda handler entry point
CMD ["lambda_handler.handler"]
