#!/bin/bash
set -e # Exit immediately if a command fails

# --- Configuration ---
# This repository is PUBLIC — do NOT hardcode the AWS account ID here.
# Provide it via the environment: export AWS_ACCOUNT_ID=<your-12-digit-account-id>
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:?Error: set AWS_ACCOUNT_ID first (export AWS_ACCOUNT_ID=<your-12-digit-account-id>)}"
AWS_REGION="us-east-2"
ECR_REPOSITORY="iopha-backend"
IMAGE_TAG="latest" 

# Construct the full ECR URI
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

echo "🔍 Checking if ECR repository exists..."
# Create the repo only when describe says it is genuinely missing.
# AccessDenied just means the caller lacks ecr:DescribeRepositories
# (least-privilege CI user) — assume the repo exists and let the push fail if it doesn't.
DESCRIBE_ERR=$(aws ecr describe-repositories --repository-names ${ECR_REPOSITORY} --region ${AWS_REGION} 2>&1 > /dev/null) || \
{
    if echo "${DESCRIBE_ERR}" | grep -q "RepositoryNotFoundException"; then
        echo "️  Repository not found. Creating '${ECR_REPOSITORY}'..."
        aws ecr create-repository --repository-name ${ECR_REPOSITORY} --region ${AWS_REGION}
    else
        echo "️  Cannot verify repository (insufficient describe permissions) — assuming it exists."
    fi
}

echo " Authenticating Docker with ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

echo "🏗️  Building Docker image from IOPHA-backend directory..."
# Build using the Dockerfile inside the IOPHA-backend folder.
# --provenance=false: skip BuildKit attestation manifests — AWS Lambda rejects
# OCI image indexes / attestation manifests and requires a single plain image manifest.
# --platform linux/arm64: must match the Lambda function's architecture.
docker build --platform linux/arm64 --provenance=false -t ${ECR_REPOSITORY}:${IMAGE_TAG} -f IOPHA-backend/Dockerfile IOPHA-backend

echo "🏷️  Tagging image for ECR..."
docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} ${ECR_URI}:${IMAGE_TAG}

echo "🚀 Pushing image to ECR..."
docker push ${ECR_URI}:${IMAGE_TAG}

echo "✅ Success! Image pushed to: ${ECR_URI}:${IMAGE_TAG}" 
