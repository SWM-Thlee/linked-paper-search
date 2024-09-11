#!/bin/bash

# Set variables
AWS_REGION=${AWS_REGION:-$(aws configure get region)}  # Use the configured AWS region if not set
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}  # Fetch the account ID using AWS CLI
ECR_REPOSITORY_NAME="search_service_image" # e.g., next_production_image
IMAGE_TAG="latest" # Set your image tag (e.g., latest, v1.0.0, etc.)
DOCKERFILE="Dockerfile.prod" # Path to your Dockerfile (default: current directory)

# Check if AWS_REGION and AWS_ACCOUNT_ID are set
if [ -z "$AWS_REGION" ] || [ -z "$AWS_ACCOUNT_ID" ]; then
  echo "Error: AWS_REGION or AWS_ACCOUNT_ID is not set or cannot be determined."
  exit 1
fi

# Authenticate Docker to your ECR registry
echo "Authenticating Docker to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build the Docker image
echo "Building Docker image..."
docker build -t $ECR_REPOSITORY_NAME:$IMAGE_TAG -f $DOCKERFILE .

# Tag the Docker image for ECR
echo "Tagging Docker image..."
docker tag $ECR_REPOSITORY_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_NAME:$IMAGE_TAG

# Push the Docker image to ECR
echo "Pushing Docker image to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_NAME:$IMAGE_TAG

echo "Docker image has been pushed to ECR: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_NAME:$IMAGE_TAG"

# Optional: Clean up local Docker images
# docker rmi $ECR_REPOSITORY_NAME:$IMAGE_TAG
# docker rmi $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_NAME:$IMAGE_TAG
